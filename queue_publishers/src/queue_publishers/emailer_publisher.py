import json
from dataclasses import asdict

from core_contracts.queue.emailer_2fa import Email2FAVerificationMessage, Emailer2FAQueuePublisher
from core_contracts.issues import ConfigurationIssue

from queue_publishers.message_bus import Message, MemoryMessageBus


class BusedEmail2FAPublisher(Emailer2FAQueuePublisher):

    def __init__(self, bus: MemoryMessageBus, exchange_name: str):
        self._bus: MemoryMessageBus = bus
        if exchange_name is None or len(exchange_name) == 0:
            raise ConfigurationIssue('Configuration missed: exchange_name is none for Emailer2FA')
        self._exchange_name = exchange_name


    def send_2fa_code_via_email(self, data: Email2FAVerificationMessage, correlation_id: str):

        body = json.dumps(asdict(data))
        msg = Message(
            body=body,
            content_type='application/json',
            correlation_id=correlation_id,
            destination_point=self._exchange_name
        )
        self._bus.enqueue(msg)


from core_contracts.temp_token.repositories import ITempTokenRepository, TempToken
from core_contracts.base import utcnow, generate_code
from datetime import timedelta
import json

_event_to_token: dict[str, int] = {
    'signup':1,
    'signin':2
}

class MockEmail2FAPublisher(Emailer2FAQueuePublisher):
    CODE_LENGTH = 5

    def __init__(self, temp_token_repo: ITempTokenRepository) -> None:
        self._repo: ITempTokenRepository = temp_token_repo


    def send_2fa_code_via_email(self, data: Email2FAVerificationMessage, correlation_id: str):
        
        _expired_at = utcnow() + timedelta(seconds=data.code_seconds_ttl)
        _type =  _event_to_token.get(data.event, -1)
        _code = generate_code(self.CODE_LENGTH)
        _pwd = data.pwd
        _jd = json.dumps({'code': _code, 'email': data.email, 'pwd': _pwd })

        print(f'mock: token: {data.token} : data : {_jd}')

        t = TempToken(token=data.token, type=_type, expired_at=_expired_at, json_data=_jd)
        self._repo.add(t)
