import json
from dataclasses import asdict

from core_contracts.queue.emailer_2fa import Email2FAVerificationMessage, Emailer2FAQueuePublisher
from core_contracts.issues import ConfigurationIssue

from queue_publishers.publisher import QueueManager
from queue_publishers.message_bus import Message, MemoryMessageBus


#DEPRICATED
class Emailer2FAPublisher(Emailer2FAQueuePublisher):

    def __init__(self, manager: QueueManager, exchange_name: str) -> None:
        self._manager: QueueManager = manager
        if exchange_name is None or len(exchange_name) == 0:
            raise ConfigurationIssue('Configuration missed: exchange_name is none for Emailer2FA')
        self._exchange_name = exchange_name


    def send_2fa_code_via_email(self, data: Email2FAVerificationMessage, correlation_id:str):
        
        exchange = self._exchange_name
        publisher = self._manager.get_publisher()
        publisher.target(exchange, '')

        publisher.msg_props(content_type='application/json', correlation_id=correlation_id)
        msg = json.dumps(asdict(data))
        publisher.publish(msg)


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
