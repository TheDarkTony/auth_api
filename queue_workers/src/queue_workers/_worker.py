from datetime import datetime, timezone
from configparser import ConfigParser

from pika.exchange_type import ExchangeType
from pika import ConnectionParameters, BlockingConnection, PlainCredentials, exceptions, BasicProperties

from sqlalchemy import Engine, create_engine


class ConfigIssue(Exception): ...

config = ConfigParser()
config.read('config.ini')

MAX_RETRY_ATTEMPTS = 2


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Worker:

    def __init__(self, exchange_cfg_key:str) -> None:
        self.max_retry_attempts: int = MAX_RETRY_ATTEMPTS
        self._retry_attempted: int = 0

        qhost = config['rabbitmq']['host']
        qusername = config['rabbitmq']['username']
        qpwd = config['rabbitmq']['password']
        qheartbeat = config['rabbitmq']['heartbeat']
        exchange_name = config['exchanges'][exchange_cfg_key]
        db_connection_url = config['database']['url']

        if qhost is None:
            raise ConfigIssue('Missed [rabbitmq].[host] setting')

        if qusername is None:
            raise ConfigIssue('Missed [rabbitmq].[username] setting')

        if qpwd is None:
            raise ConfigIssue('Missed [rabbitmq].[password] setting')

        if exchange_name is None:
            raise ConfigIssue(f'Missed [exchanges].[{exchange_cfg_key}] setting')

        if db_connection_url is None:
            raise ConfigIssue('Missed [database].[url] setting')


        self.q_username:str = qusername
        self.q_password:str = qpwd
        self.q_host:str = qhost
        self.q_exchange_name:str = exchange_name
        self.db_connection_url: str = db_connection_url
        self._db_engine: Engine

    def handle(self, channel, queue_name, db_engine):
        self._retry_attempted = 0

    def setup_connection(self):
        creds = PlainCredentials(self.q_username, self.q_password)
        params = ConnectionParameters(self.q_host, credentials=creds)
        connection = BlockingConnection(params)
        
        channel = connection.channel()
        channel.exchange_declare(self.q_exchange_name, ExchangeType.direct)

        result = channel.queue_declare('', exclusive=True)
        queue_name = result.method.queue
        channel.queue_bind(queue=queue_name, exchange=self.q_exchange_name, routing_key='')
        return connection, channel, queue_name


    def start(self):
        try:
            connection, channel, queue_name = self.setup_connection()
            db_engine: Engine = create_engine(self.db_connection_url)
            self._db_engine = db_engine

            try:
                while self._retry_attempted <= self.max_retry_attempts:
                    try:
                        self.handle(channel, queue_name, db_engine)
                    except exceptions.ConnectionClosedByBroker as ex:
                        # Don't recover if connection was closed by broker
                        break
                    except exceptions.AMQPChannelError as ex:
                        # Don't recover on channel errors
                        break
                    except exceptions.AMQPConnectionError as ex:
                        #Recover on all other connection errors
                        if self._retry_attempted < self.max_retry_attempts:
                            connection, channel, queue_name = self.setup_connection()

                        self._retry_attempted +=1
                        continue
                    except KeyboardInterrupt:
                        print("\nBye Bye...")
                        break

                    break
            finally:
                db_engine.dispose()

                print('Disposing RabbitMQ connections...')
                if channel.is_open:
                    channel.close()

                connection.process_data_events(time_limit=1)
                if connection.is_open:
                    connection.close()

        except Exception as ex:
           print('Connection to queue is failed at start')
        finally:
            print('Bye bye... see you later')
