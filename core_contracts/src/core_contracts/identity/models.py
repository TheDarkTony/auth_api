from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from core_contracts.metainfo import FieldMetaData, FieldLength
from core_contracts.base import utcnow


@dataclass
class IdentitySubject:
    email: str = field(metadata={FieldMetaData.max_length.value: FieldLength.l_75.value})
    email_verified: bool
    fname: str | None = field(default=None, metadata={FieldMetaData.max_length.value: FieldLength.l_50.value})
    lname: str | None = field(default=None, metadata={FieldMetaData.max_length.value: FieldLength.l_50.value})
    created_date: datetime = field(default_factory=utcnow)
    is_activated: bool = field(default=False)


@dataclass
class Identity(IdentitySubject):
    id: int = 0


@dataclass
class IdentityItem:
    id: int
    fname: str
    lname: str


class IdentityFields(StrEnum):
    EMAIL = 'email'
    EMAIL_VERIFIED = 'email_verified'
    FNAME = 'fname'
    LNAME = 'lname'
    CREATED_DATE = 'created_date'
    IS_ACTIVATED = 'is_activated'
    ID = 'id'


@dataclass
class UserSubject:
    identity_id: int
    role_id: int
    username: str = field(metadata={FieldMetaData.max_length.value: FieldLength.l_50.value})
    pwd: str = field(metadata={FieldMetaData.max_length.value: FieldLength.l_75.value})
    email_2fa_enabled: bool
    deleted_date: datetime | None = field(default=None)

    @property
    def archived(self) -> bool:
        return self.deleted_date is not None



@dataclass
class User(UserSubject):
    id: int = 0


class UserFields(StrEnum):
    IDENTITY_ID = 'identity_id'
    ROLE_ID = 'role_id'
    USERNAME = 'username'
    PWD = 'pwd'
    EMAIL_2FA_ENABLED = 'email_2fa_enabled'
    DELETED_DATE = 'deleted_date'
    ID = 'id'


@dataclass
class ProfileResponse:

    identity: Identity|None
    user: User|None
