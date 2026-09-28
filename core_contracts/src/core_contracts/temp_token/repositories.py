from abc import ABCMeta, abstractmethod

from core_contracts.temp_token.models import TempToken


class ITempTokenRepository(metaclass=ABCMeta):

    @abstractmethod
    def fetch_by_token(self, token: str) -> TempToken|None:
        raise NotImplementedError


    @abstractmethod
    def add(self, token: TempToken) -> TempToken:
        raise NotImplementedError


    @abstractmethod
    def edit(self, token: TempToken) -> TempToken:
        raise NotImplementedError
