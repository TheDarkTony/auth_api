from dataclasses import dataclass
from typing import Annotated
import re

from pydantic import BaseModel, StringConstraints, field_validator, ValidationInfo

from core_contracts.metainfo import FieldLength


class EditDemographicsDemand(BaseModel):
    fname: Annotated[str, StringConstraints(max_length=FieldLength.l_50)]
    lname: Annotated[str, StringConstraints(max_length=FieldLength.l_50)]


class ChangePwdDemand(BaseModel):
    old_pwd: str|None
    new_pwd: str|None
    new_pwd_confirmed: str|None


    @field_validator('new_pwd_confirmed', mode='after')
    @classmethod
    def validate_confirmation(cls, value: str, info: ValidationInfo) -> str:

        pwd = info.data.get('new_pwd')
        if pwd != value:
            raise ValueError('new password and confirmation does not match')

        return value


class EditUserDemand(BaseModel):
    email_2fa_enabled: bool


class SignInDemand(BaseModel):
    email: Annotated[str, StringConstraints(max_length=FieldLength.l_75)]
    pwd: str

    @field_validator('email', mode='before')
    @classmethod
    def validate_email(cls, value: str, info: ValidationInfo) -> str:
        if not isinstance(value, str):
            raise ValueError('Wrong email type is provided')

        if value is None or len(value) == 0:
            raise ValueError('Email is required')

        if isinstance(info.context, dict):
            email_regex = info.context.get('email_regex')
            if email_regex is not None and isinstance(email_regex, re.Pattern):
                if not email_regex.match(value):
                    raise ValueError('Value of email is invalid')

        return value


    @field_validator('pwd', mode='before')
    @classmethod
    def validate_pwd(cls, value: str, info: ValidationInfo) -> str:
        if not isinstance(value, str):
            raise ValueError('Wrong email type is provided')

        if value is None or len(value) == 0:
            raise ValueError('Email is required')
        return value


class SignUpDemand(SignInDemand):
    ...


class Sign2FAFeedbackDemand(BaseModel):
    process_token: Annotated[str, StringConstraints(max_length=FieldLength.l_75.value)] = ''
    code: Annotated[str, StringConstraints(max_length=FieldLength.l_5.value)] = ''


@dataclass
class SignInData:
    access_token: str
    refresh_token: str


@dataclass
class DemandAccepted:
    process_token: str
