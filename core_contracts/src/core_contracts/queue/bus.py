from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Message(object):
    body: str
    content_type: str
    correlation_id: str
    destination_point: str
    tag:str|None = field(default=None)


class IMessageOutBus(metaclass=ABCMeta):

    @abstractmethod
    def dequeue(self) -> Message|None:
        raise NotImplementedError


class IMessageInBus(metaclass=ABCMeta):

    @abstractmethod
    def enqueue(self, message: Message):
        raise NotImplementedError