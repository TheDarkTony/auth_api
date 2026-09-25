import threading
from datetime import datetime
from typing_extensions import Self

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika import exceptions

from core_contracts.issues import ConfigurationIssue, ResourceDisposedIssue
from core.utils import utcnow


_connections_lock = threading.Lock()
_connections: dict[int, tuple[pika.BlockingConnection, datetime]] = {}

_disposed: bool = False

def dispose():
    global _disposed

    if _disposed:
        return

    with _connections_lock:
        for thread, conn_data in _connections.items():
            conn, time = conn_data
            if conn.is_open:
                try:
                    # Wait until all the data events have been processed
                    conn.process_data_events(time_limit=1)
                    conn.close()
                except Exception:
                    print('Failed on cloasing connection rabbitmq')
        _connections.clear()

    _disposed = True


class QueueManager:

    class Publisher:

        def __init__(self, queue: 'QueueManager') -> None:
            self._queue: 'QueueManager' = queue
            self._ex_name: str|None = None
            self._routing_name: str|None = None
            self._msg_props = {}

        def target(self, ex_name: str, routing_key: str) -> Self:
            self._ex_name = ex_name
            self._routing_name = routing_key
            return self

        def msg_props(self,  **kwargs) -> Self:
            self._msg_props = kwargs
            return self

        def publish(self, message):
            if self._routing_name is None or self._ex_name is None:
                raise Exception('Publisher routing arguments is none')

            self._queue._enqueue_message(self._ex_name, self._routing_name, message, **self._msg_props)


    def __init__(self, host, username, password, max_retry_attempts=2) -> None:
        if host is None:
            raise ConfigurationIssue('Missed configuration: queue host is none')

        if username is None:
            raise ConfigurationIssue('Missed configuration: queue username is none')

        if password is None:
            raise ConfigurationIssue('Missed configuration: queue password is none')

        if max_retry_attempts is None or max_retry_attempts < 1:
            raise ConfigurationIssue('Missed configuration: max_retry_attempts')

        self._host = host
        self._username = username
        self._password = password
        self._max_retry_attempts = max_retry_attempts


    def get_publisher(self, name: str|None=None) -> Publisher:
        if _disposed:
            raise ResourceDisposedIssue('Queue publisher is disposed')

        return self.Publisher(self)


    def _enqueue_message(self, exchange:str, routing:str, message:str|bytes, **kwargs):
        if _disposed:
            raise ResourceDisposedIssue('Queue publisher is disposed')

        def _publish():
            ch = self._get_channel()
            ch.basic_publish(
                exchange=exchange,
                routing_key=routing,
                body=message,
                properties=pika.BasicProperties(**kwargs)
            )
            ch.close()

        self._with_connection_retry(_publish)


    def _setup_threaded_connection(self):
        thread = threading.get_ident()
        connection, _ = _connections.get(thread, (None, None))

        if connection is None or connection.is_closed:
            with _connections_lock:
                connection, _ = _connections.get(thread, (None, None))
                if connection is None or connection.is_closed:
                    creds = pika.PlainCredentials(self._username, self._password)
                    params = pika.ConnectionParameters(self._host, credentials=creds, heartbeat=0)
                    connection = pika.BlockingConnection(params)
                    _connections[thread] = (connection, utcnow())

        return connection


    def _get_channel(self) -> BlockingChannel:
        if _disposed:
            raise ResourceDisposedIssue('Queue publisher is disposed')

        connection = self._setup_threaded_connection()
        ch = connection.channel()
        return ch

    def _with_connection_retry(self, callback):
        
        attempts = 0
        while attempts < self._max_retry_attempts:
            try:
                callback()
                break
            except ResourceDisposedIssue:
                raise
            except exceptions.ConnectionClosedByBroker:
                # Don't recover if connection was closed by broker
                raise
            except exceptions.AMQPChannelError:
                # Don't recover on channel errors
                raise
            except exceptions.AMQPConnectionError:
                #Recover on all other connection errors
                self._setup_threaded_connection()
                if attempts < self._max_retry_attempts:
                    attempts += 1
                    continue
                raise
