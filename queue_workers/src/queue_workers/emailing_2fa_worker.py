import json
import random
import logging
import traceback
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from smtplib import SMTP

from pika import BasicProperties
from repo_sqlalchemy.temp_token.repo import TempToken
from sqlalchemy.orm import Session

from queue_workers._worker import utcnow, config, ConfigIssue, Worker


APPLICATION_NAME = 'queue_worker:emailing_2fa'
CONTENT_TYPE = 'application/json'

PREFETCH_COUNT = 1

LOGGING_EXCHANGE_NAME = config['exchanges']['logging_db']

SMTP_SERVER = config['mail']['smtp_server']
SMTP_PORT = config.getint('mail', 'smtp_port')

SENDER_USER = config['mail']['sender_user']
SENDER_PASSWORD = config['mail']['sender_password']
SENDER_MAIL =  config['mail']['sender_mail']

DEFAULT_CODE_TTL = config.getint('verification_2fa', 'default_temp_code_ttl')
CODE_LENGTH = config.getint('verification_2fa', 'temp_code_length')


def generate_code(length: int) -> str:
    code = str.join('', [str(random.randint(0, 9)) for _ in range(length)])
    return code


def content_maker(code: str, code_ttl:int, event:str|None) -> str:
    if event == 'signin':
        msg = f'We detected attempt for login. Please enter the {code} to confirm your identity. Code is active during {code_ttl /60} minutes.'
    elif event == 'signup':
        msg = f'Please enter {code} code to verify your email and activate account. Code is valid during {code_ttl /60} minutes.'
    else:
        msg = f'Please enter {code} code during {code_ttl /60} minutes.'

    return msg


def subject_maker() -> str:
    return 'Identity Verification'


def log_error(ch, body, correlation_id):
    ch.basic_publish(
        exchange=LOGGING_EXCHANGE_NAME,
        routing_key='',
        body=body,
        properties=BasicProperties(content_type=CONTENT_TYPE, correlation_id=correlation_id)
    )

def json_error_message(message, correlation_id, e, **kwargs):
    tb = None
    if e is not None:
        tb = ''.join(traceback.format_tb(e.__traceback__))

    args = json.dumps(kwargs) if len(kwargs) > 0 else None

    msg = json.dumps({
        'level': logging.getLevelName(logging.ERROR),
        'correlation_id': correlation_id,
        'message': message,
        'happend_at': str(utcnow()),
        'traceback': tb,
        'demand_args': args,
        'application': APPLICATION_NAME
    })
    return msg


_event_to_token: dict[str, int] = {
    'signup':1,
    'signin':2
}


class Emailing2FAWorker(Worker):

    def handle(self, channel, queue_name, db_engine):
        channel.basic_qos(prefetch_count=PREFETCH_COUNT)
        channel.basic_consume(queue_name, on_message_callback=self.get_callback())
        print('START CONSUMING EMAILING')
        channel.start_consuming()
        return super().handle(channel, queue_name, db_engine)

    def get_callback(self):
        
        def on_message(ch, method, properties, body):
            
            correlation_id = properties.correlation_id
            if properties.content_type != CONTENT_TYPE:
                error = json_error_message(f'{properties.content_type} is not supported', correlation_id, None)
                log_error(ch, error, correlation_id)
                ch.basic_reject(method.delivery_tag)
                return

            data: dict = json.loads(body)
            event: str = data.get('event', 'unknown')
            email: str|None = data.get('email')
            pwd: str|None = data.get('pwd')
            token: str|None = data.get('token')
            code_seconds_ttl: float|None = data.get('code_seconds_ttl')
            if code_seconds_ttl is None:
                code_seconds_ttl = DEFAULT_CODE_TTL

            code = generate_code(CODE_LENGTH)

            token_expired_at = datetime.now(timezone.utc) + timedelta(seconds=code_seconds_ttl)
            token_json_data = json.dumps({'code': code, 'email': email, 'pwd': pwd })
            token_type:int = _event_to_token.get(event, 0)
            
            try:
                temp_token = TempToken(token=token, type=token_type, expired_at=token_expired_at, json_data=token_json_data)
                with Session(self._db_engine) as session:
                    session.add(temp_token)
                    session.commit()
            except Exception as ex:
                body = json_error_message(
                    message='worker failed on saving temp token',
                    correlation_id=correlation_id,
                    e=ex
                )
                log_error(ch, body, correlation_id)

            #sending mail
            try:
                mail = EmailMessage()
                mail['Subject'] = subject_maker()
                mail['From'] = SENDER_MAIL
                mail['To'] = email
                mail.set_content(content_maker(code, code_seconds_ttl, event))
                with SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.starttls()
                    server.login(SENDER_USER, SENDER_PASSWORD)            
                    server.send_message(mail)
            except Exception as ex:
                body = json_error_message(
                    message='worker failed on sending mail',
                    correlation_id=correlation_id,
                    e=ex
                )
                log_error(ch, body, correlation_id)

            ch.basic_ack(delivery_tag=method.delivery_tag)
            print(f" [email_2fa] done")

        return on_message


if __name__ == '__main__':
    try:
        if SMTP_SERVER is None:
            raise ConfigIssue('Missed [mail].[smtp_server] setting')

        if SMTP_PORT is None:
            raise ConfigIssue('Missed [mail].[smtp_port] setting')

        if SENDER_USER is None:
            raise ConfigIssue('Missed [mail].[sender_user] setting')

        if SENDER_PASSWORD is None:
            raise ConfigIssue('Missed [mail].[sender_password] setting')

        if SENDER_MAIL is None:
            raise ConfigIssue('Missed [mail].[sender_mail] setting')

        if DEFAULT_CODE_TTL is None:
            raise ConfigIssue('Missed [verification_2fa].[default_temp_code_ttl] setting')

        if CODE_LENGTH is None:
            raise ConfigIssue('Missed [verification_2fa].[temp_code_length] setting')

        worker = Emailing2FAWorker('emailer_2fa')
        worker.start()
    except ConfigIssue as ex:
        print('Failed on starting app: ', str(ex))
