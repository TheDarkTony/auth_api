import threading

import pika
import pika.channel

from core_contracts.issues import ConfigurationIssue
from core_contracts.queue.bus import IMessageOutBus


class QueueManager(object):

    PUBLISH_INTERVAL = 1 #seconds

    lock = threading.Lock()

    def __init__(self, amqp_url, message_bus: IMessageOutBus) -> None:

        if amqp_url is None:
            raise ConfigurationIssue('Missed option: amqp_url is required.')

        if message_bus is None:
            raise ConfigurationIssue('Missed dependency: message_bus is required.')

        self._amqp_url = amqp_url
        self._message_bus: IMessageOutBus = message_bus

        self._connection: pika.SelectConnection|None = None
        self._channel: pika.channel.Channel|None = None
        self._stopping = False

        self._acked: int = 0
        self._nacked: int = 0
        self._deliveries: dict = {}
        self._message_number: int = 0


    def connect(self) -> pika.SelectConnection:
        connection = pika.SelectConnection(
            parameters=pika.URLParameters(self._amqp_url),
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_open_error,
            on_close_callback=self.on_connection_closed
        )

        return connection


    def on_connection_open(self, _unused_connection):
        """
        This method is called by pika once the connection to RabbitMQ has been established.

        It passes the handle to the connection object in case we need it, but in this case, we'll
        just mark it unused.

        :param pika.SelectConnection _unused_connection: The connection
        """
        self.open_channel()


    def on_connection_open_error(self, _unused_connection, err):
        """
        This method is called by pika if the connection to RabbitMQ can't be established.

        :param pika.SelectConnection _unused_connection: The connection
        :param Exception err: The error
        """
        if self._connection is None:
            return
        self._connection.ioloop.call_later(5, self._connection.ioloop.stop)


    def on_connection_closed(self, _connection, reason):
        """
        This method is invoked by pika when the connection to RabbitMQ is closed unexpectedly.

        Since it is unexpected, we will reconnect to RabbitMQ if it disconnects.

        :param pika.connection.Connection _connection: The closed connection obj
        :param Exception reason: exception representing reason for loss of connection.
        """
        if self._connection is None:
            return
        
        self._channel = None
        if self._stopping:
            self._connection.ioloop.stop()
        else:
            self._connection.ioloop.call_later(5, self._connection.ioloop.stop)


    def open_channel(self):
        if self._connection is None:
            return
        self._connection.channel(on_open_callback=self.on_channel_open)


    def on_channel_open(self, channel):
        """
        This method is invoked by pika when the channel has been opened.
        The channel object is passed in so we can make use of it.
        Since the channel is now open, we'll declare the exchange to use.

        :param pika.channel.Channel channel: The channel object
        """
        self._channel = channel
        #self.add_on_channel_close_callback()

        self.start_publishing()


    # def add_on_channel_close_callback(self):
    #     """
    #     This method tells pika to call the on_channel_closed method if RabbitMQ unexpectedly
    #     closes the channel.
    #     """
    #     self._channel.add_on_close_callback(self.on_channel_closed)


    # def on_channel_closed(self, channel, reason):
    #     """
    #     Invoked by pika when RabbitMQ unexpectedly closes the channel.

    #     Channels are usually closed if you attempt to do something that violates the protocol, such
    #     as re-declare an exchange or queue with different parameters. In this case, we'll close the
    #     connection to shutdown the object.

    #     :param pika.channel.Channel channel: The closed channel
    #     :param Exception reason: why the channel was closed
    #     """
    #     self._channel = None
    #     if not self._stopping:
    #         self._connection.close()


    def start_publishing(self):
        """This method will enable delivery confirmations and schedule the first message to be sent to RabbitMQ."""
        self.enable_delivery_confirmations()
        self.schedule_next_message(self.PUBLISH_INTERVAL)


    def enable_delivery_confirmations(self):
        """
        Send the Confirm.Select RPC method to RabbitMQ to enable delivery confirmations on the
        channel. The only way to turn this off is to close the channel and create a new one.

        When the message is confirmed from RabbitMQ, the on_delivery_confirmation method will be
        invoked passing in a Basic.Ack or Basic.Nack method from RabbitMQ that will indicate which
        messages it is confirming or rejecting.
        """
        if self._channel is None:
            return
        self._channel.confirm_delivery(self.on_delivery_confirmation)


    def on_delivery_confirmation(self, method_frame):
        """
        Invoked by pika when RabbitMQ responds to a Basic.Publish RPC command, passing in either a
        Basic.Ack or Basic.Nack frame with the delivery tag of the message that was published. The
        delivery tag is an integer counter indicating the message number that was sent on the
        channel via Basic.Publish. Here we're just doing house keeping to keep track of stats and
        remove message numbers that we expect a delivery confirmation of from the list used to keep
        track of messages that are pending confirmation.

        :param pika.frame.Method method_frame: Basic.Ack or Basic.Nack frame
        """
        confirmation_type = method_frame.method.NAME.split('.')[1].lower()
        ack_multiple = method_frame.method.multiple
        delivery_tag = method_frame.method.delivery_tag

        if confirmation_type == 'ack':
            self._acked += 1
        elif confirmation_type == 'nack':
            self._nacked += 1

        del self._deliveries[delivery_tag]

        if ack_multiple:
            for tmp_tag in list(self._deliveries.keys()):
                if tmp_tag <= delivery_tag:
                    self._acked += 1
                    del self._deliveries[tmp_tag]

        """NOTE: at some point you would check self._deliveries for stale entries and decide to attempt re-delivery."""


    def schedule_next_message(self, seconds_interval):
        """If we are not closing our connection to RabbitMQ, schedule another message to be delivered in PUBLISH_INTERVAL seconds."""
        if self._connection is None:
            return
        self._connection.ioloop.call_later(seconds_interval, self.publish_message)


    def publish_message(self):
        """
        If the class is not stopping, publish a message to RabbitMQ, appending a list of deliveries
        with the message number that was sent. This list will be used to check for delivery
        confirmations in the on_delivery_confirmations method.

        Once the message has been sent, schedule another message to be sent. The main reason I put
        scheduling in was just so you can get a good idea of how the process is flowing by slowing
        down and speeding up the delivery intervals by changing the PUBLISH_INTERVAL constant in the
        class.
        """
        if self._channel is None or not self._channel.is_open:
            return

        msg = self._message_bus.dequeue()
        if msg is None:
            self.schedule_next_message(self.PUBLISH_INTERVAL)
            return

        hdrs = {}
        properties = pika.BasicProperties(
            app_id='api-publisher',
            content_type=msg.content_type,
            headers=hdrs,
            correlation_id=msg.correlation_id
        )

        self._channel.basic_publish(msg.destination_point, '', msg.body, properties)

        self._message_number += 1
        self._deliveries[self._message_number] = True

        self.schedule_next_message(self.PUBLISH_INTERVAL)


    def run(self):
        """Run the example code by connecting and then starting the IOLoop."""
        while not self._stopping:
            self._connection = None
            self._deliveries = {}
            self._acked = 0
            self._nacked = 0
            self._message_number = 0

            try:
                self._connection = self.connect()
                self._connection.ioloop.start()
            except KeyboardInterrupt:
                self.stop()
                """
                Stop the example by closing the channel and connection.
        
                We set a flag here so that we stop scheduling new messages to be published. The IOLoop is
                started because this method is invoked by the Try/Catch below when KeyboardInterrupt is
                caught. Starting the IOLoop again will allow the publisher to cleanly disconnect from
                RabbitMQ.
                """
                if self._connection is not None and not self._connection.is_closed:
                    self._connection.ioloop.start()


    def stop(self):
        with self.lock:
            if not self._stopping:        
                self._stopping = True
                self.close_channel()
                self.close_connection()


    def close_channel(self):
        """Invoke this command to close the channel with RabbitMQ by sending the Channel.Close RPC command."""
        if self._channel is not None:
            self._channel.close()


    def close_connection(self):
        """This method closes the connection to RabbitMQ."""
        if self._connection is not None:
            self._connection.close()


class ThreadStopper(object):
    def __init__(self) -> None:
        self._manager:QueueManager|None = None

    def _pin(self, manager: QueueManager):
        self._manager = manager

    def stop(self):
        if self._manager is None:
            return
        self._manager.stop()


def _run_queue_manager(amqp_url, message_bus, thread_stopper: ThreadStopper):
    try:
        m = QueueManager(amqp_url, message_bus)
        thread_stopper._pin(m)
        m.run()
    except (Exception, KeyboardInterrupt) as ex:
        print('Error on ThreadedQueueManager')
        print(ex)


def get_queue_manager_bg_task(amqp_url, message_bus, stopper: ThreadStopper) -> threading.Thread:
    return threading.Thread(target=_run_queue_manager, args=(amqp_url, message_bus, stopper))
