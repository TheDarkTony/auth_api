from typing import Annotated
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, StringConstraints, computed_field

from core_contracts.metainfo import FieldLength
from core_contracts.base import utcnow


class IdentitySubject(BaseModel):
    email: Annotated[str, StringConstraints(max_length=FieldLength.l_75.value)]
    email_verified: bool
    fname: Annotated[str | None, StringConstraints(max_length=FieldLength.l_50.value)]
    lname: Annotated[str | None, StringConstraints(max_length=FieldLength.l_50.value)]
    created_date: datetime = Field(default_factory=utcnow)
    is_activated: bool = Field(default=False)


class Identity(IdentitySubject):
    id: int = 0


class IdentityItem(BaseModel):
    id: int
    fname: str|None
    lname: str|None


class IdentityFields(StrEnum):
    EMAIL = 'email'
    EMAIL_VERIFIED = 'email_verified'
    FNAME = 'fname'
    LNAME = 'lname'
    CREATED_DATE = 'created_date'
    IS_ACTIVATED = 'is_activated'
    ID = 'id'


class UserSubject(BaseModel):
    identity_id: int
    role_id: int
    username: Annotated[str, StringConstraints(max_length=FieldLength.l_50.value)]
    pwd: Annotated[str, StringConstraints(max_length=FieldLength.l_75.value)]
    email_2fa_enabled: bool
    deleted_date: datetime | None = Field(default=None)

    @computed_field
    @property
    def archived(self) -> bool:
        return self.deleted_date is not None


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


class ProfileResponse(BaseModel):

    identity: Identity|None
    user: User|None
