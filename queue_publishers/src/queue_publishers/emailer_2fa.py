import json
from dataclasses import asdict

from core_contracts.queue.emailer_2fa import Email2FAVerificationMessage, Emailer2FAQueuePublisher
from core_contracts.issues import ConfigurationIssue

from queue_publishers.publisher import QueueManager



class Emailer2FAPublisher(Emailer2FAQueuePublisher):

    def __init__(self, publisher: QueueManager, exchange_name: str) -> None:
        self._publisher: QueueManager = publisher
        if exchange_name is None or len(exchange_name) == 0:
            raise ConfigurationIssue('Configuration missed: exchange_name is none for Emailer2FA')
        self._exchange_name = exchange_name


    def send_2fa_code_via_email(self, data: Email2FAVerificationMessage, correlation_id:str|None=None):
        
        exchange = self._exchange_name
        publisher = self._publisher.get_publisher()
        publisher.target(exchange, '')

        publisher.msg_props(content_type='application/json', correlation_id=correlation_id)
        msg = json.dumps(asdict(data))
        publisher.publish(msg)
