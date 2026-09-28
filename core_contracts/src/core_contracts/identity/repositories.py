from abc import abstractmethod, ABCMeta
from typing import Any, Sequence

from core_contracts.identity import models
from core_contracts.base import IRepository


class IIdentityRepository(IRepository[models.Identity]):

    @abstractmethod
    def list(self, predicate: dict[str, Any]) -> Sequence[models.IdentityItem]:
        raise NotImplementedError

    @abstractmethod
    def fetch_by_email(self, email: str) -> models.Identity|None:
        raise NotImplementedError
    
    @abstractmethod
    def update_and_attach_user(self,
        identity:models.Identity,
        user: models.UserSubject
    ) -> tuple[models.Identity, models.User]:
        raise NotImplementedError


class IUserRepository(IRepository[models.User]):

    @abstractmethod
    def list(self, predicate: dict[str, Any]) -> Sequence[models.User]:
        raise NotImplementedError

    @abstractmethod
    def fetch_active_by_usrname(self, usrname: str) -> models.User|None:
        raise NotImplementedError

    @abstractmethod
    def fetch_by_usrname(self, usrname: str) -> models.User|None:
        raise NotImplementedError


class IUserTempBlackListRepository(metaclass=ABCMeta):

    @abstractmethod
    def push_to_black_list(self, user_id: int, ttl:int):
        raise NotImplementedError

    @abstractmethod
    def is_blacklisted(self, user_id: int) -> bool:
        raise NotImplementedError

