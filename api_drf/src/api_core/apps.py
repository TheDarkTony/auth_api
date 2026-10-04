import atexit
import os
import signal
import sys
import logging

from django.apps import AppConfig
from rest_framework.settings import settings

from core.logging import LogViaQueueHandler

from src.api_core.container import AppContainer
from src.api_core.utils import DjangoLogFilter, BusQueueLogAdapter

from queue_publishers.message_bus import MemoryMessageBus
from queue_publishers.queue_manager import get_queue_manager_bg_task, ThreadStopper


MESSAGE_BUS: MemoryMessageBus = MemoryMessageBus()

def setup_bg_publisher(amqp_url):
    stopper = ThreadStopper()
    thread = get_queue_manager_bg_task(amqp_url, MESSAGE_BUS, stopper)
    return thread, stopper


class ApiCoreConfig(AppConfig):
    name = 'src.api_core'
    label = 'api_core'
    verbose_name = 'Api Core'
    default = True

    def ready(self) -> None:

        container = AppContainer()
        container.wire([
            'src.api_core.middleware',
            'src.identity.views',
            'src.auth.views',
            'src.permission.views',
            'src.pizza.views',
        ])

        security = settings.SECURITY_AUTH
        secret_jwt_key = security.get('SECRET_JWT_KEY')
        jwt_algorithm = security.get('JWT_ALGORITHM')
        access_token_seconds_ttl = security.get('ACCESS_TOKEN_SECONDS_TTL', -1)
        refresh_token_seconds_ttl = security.get('REFRESH_TOKEN_SECONDS_TTL', -1)

        security_2fa = settings.SECURITY_AUTH_2FA
        default_email_2fa_enabled = security_2fa.get('DEFAULT_EMAIL_2FA_ENABLED')
        email_code_seconds_ttl = security_2fa.get('EMAIL_CODE_SECONDS_TTL', -1)
        email_regex_template = security_2fa.get('EMAIL_REGEX_TEMPLATE')

        signup_default_role_id = settings.SIGNUP_DEFAULT_ROLE_ID

        pizza_app = settings.DATABASES.get('PIZZA_APP')
        db_env1_conn = None
        
        if pizza_app is not None:
            db_env1_conn = pizza_app.get('ENV1')

        if db_env1_conn is None:
            raise Exception('Missed configuration: DATABASES.PIZZA_APP.ENV1')

        valkey_url = settings.VALKEY_URL
        if valkey_url is None:
            raise Exception('Missed configuration: VALKEY_URL')

        queue = settings.RABBITMQ
        queue_url = queue.get('URL')
        queue_host = queue.get('HOST')
        queue_username = queue.get('USERNAME')
        queue_password = queue.get('PASSWORD')
        queue_exchanges = queue.get('EXCHANGES')
        auth_2fa_emailer_exchange = None
        pizza_db_logging_exchange = None
        if queue_exchanges is not None:
            auth_2fa_emailer_exchange = queue_exchanges.get('AUTH_2FA_EMAILER')
            pizza_db_logging_exchange = queue_exchanges.get('LOGGING')

        if auth_2fa_emailer_exchange is None:
            raise Exception('Missed configuration: RABBITMQ.EXCHANGES.AUTH_2FA_EMAILER ')
        if pizza_db_logging_exchange is None:
            raise Exception('Missed configuration: RABBITMQ.EXCHANGES.LOGGING ')

        container.config.from_dict({
            'db': {
                'connection': db_env1_conn
            },
            'valkey': {
                'url': valkey_url
            },
            'rabbitmq': {
                'url': queue_url,
                'host': queue_host,
                'username': queue_username,
                'password': queue_password,
                'exchanges': {
                    'auth_2fa_emailer': auth_2fa_emailer_exchange,
                    'logging': pizza_db_logging_exchange
                }
            },
            'auth': {
                'default_role_id': signup_default_role_id,
                'default_email_2fa_enabled': default_email_2fa_enabled,
                'email_code_seconds_ttl': email_code_seconds_ttl,
                'email_regex_template': email_regex_template,
                
                'secret_jwt_key': secret_jwt_key,
                'jwt_algorithm': jwt_algorithm,
                'access_token_seconds_ttl': access_token_seconds_ttl,
                'refresh_token_seconds_ttl': refresh_token_seconds_ttl,
            }
        })

        container.override_providers(message_bus=MESSAGE_BUS)
        thread, stopper = setup_bg_publisher(queue_url)
        thread.start()

        log_emitter = BusQueueLogAdapter(MESSAGE_BUS)
        log_emitter.setup_exchange(pizza_db_logging_exchange)
        
        queue_log_handler = LogViaQueueHandler(queue=log_emitter)
        queue_log_handler.addFilter(DjangoLogFilter(name='filter_django_logs_out'))
        logging.basicConfig(format='%(message)s', handlers=[queue_log_handler], level=logging.INFO)

        disposed = False
        def clean_up():
            nonlocal disposed
            if disposed:
                return

            try:
                print('Disposing: db engine')
                db_conn = container.db_engine()
                db_conn.dispose()
            except Exception as ex:
                print(ex)

            try:
                stopper.stop()
                thread.join()
                print('QM stopped')
            except Exception as ex:
                print(ex)

            try:
                print('Disposing: valkey server')
                valkey = container.valkey_client()
                valkey.close()
            except Exception as ex:
                print(ex)

            container.unwire()
            disposed = True
            print('Disposed')


        def graceful_shutdown(signum, frame):
            print("\n[Shutdown] Control-C detected. Cleaning up resources...")
            clean_up()
            sys.exit(0) # Terminate the process cleanly so Django can release the port

        if os.environ.get('RUN_MAIN') == 'true':
            signal.signal(signal.SIGINT, graceful_shutdown)

        atexit.register(clean_up)
