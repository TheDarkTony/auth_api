from abc import ABCMeta, abstractmethod
from typing import Sequence
from dataclasses import dataclass
from enum import StrEnum, IntEnum
from datetime import datetime, timezone


class IRepository[TMobel](metaclass=ABCMeta):

    @abstractmethod
    def fetch_by_id(self, id: int,/) -> TMobel | None:
        raise NotImplementedError


    @abstractmethod
    def save(self, model: TMobel,/) -> TMobel:
        raise NotImplementedError


    @abstractmethod
    def delete(self, id: int,/) -> None:
        raise NotImplementedError


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class BatchResponse:
    next_cursor: str | None
    prev_cursor: str | None
    items: Sequence[object]


class PagginationArguments(StrEnum):
    NEXT_CURSOR = 'next_cursor'
    PREV_CURSOR = 'prev_cursor'
    BATCH_SIZE = 'batch_size'


class AccessArguments(StrEnum):
    MODE = 'mode'
    CURRENT_IDENTITY = 'current_identity_id'
    CURRENT_USR = 'current_usr_id'
    CURRENT_ROLE = 'current_role_id'


class IdentityArguments(StrEnum):
    USER_ID = 'usr_id'
    IDENTITY_ID = 'identity_id'


class AccessMode(StrEnum):
    own = 'own'
    nonown = 'nonown'


class Roles(IntEnum):
    admin = 1
    cook = 2
    waiter = 3
    customer = 4


class Resources(StrEnum):
    IDENTITIES = 'identities'
    USERS = 'users'
    ROLE_PERMISSIONS = 'roles_permissions'
    ROLES = 'roles'
    APPLICATION_RESOURCES = 'application_resources'
    MENU = 'menu'
    ORDERS = 'orders'
