from dataclasses import dataclass
from abc import ABCMeta, abstractmethod
from enum import Enum


class VerificationEvents(Enum):
    SIGNUP = 'signup'
    SIGNIN = 'signin'


@dataclass
class Email2FAVerificationMessage:
    event: str
    token: str
    email: str
    code_seconds_ttl: int
    pwd: str|None = None


class Emailer2FAQueuePublisher(metaclass=ABCMeta):

    @abstractmethod
    def send_2fa_code_via_email(self, data: Email2FAVerificationMessage,  correlation_id:str):
        raise NotImplementedError

