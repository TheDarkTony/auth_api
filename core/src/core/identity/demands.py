from dataclasses import dataclass, field
from typing import Annotated

from pydantic import BaseModel, StringConstraints

from core_contracts.metainfo import FieldLength

@dataclass
class EditDemographicsDemand:
    fname: str
    lname: str


@dataclass
class ChangePwdDemand:
    old_pwd: str|None
    new_pwd: str|None
    new_pwd_confirmed: str|None


@dataclass
class EditUserDemand:
    email_2fa_enabled: bool


@dataclass
class SignUpDemand:
    email: str = field(default='')
    pwd: str = field(default='')


@dataclass
class SignInData:
    access_token: str
    refresh_token: str


@dataclass
class SignInDemand:
    email: str
    pwd: str


@dataclass
class DemandAccepted:
    process_token: str


class Sign2FAFeedbackDemand(BaseModel):
    process_token: Annotated[str, StringConstraints(max_length=FieldLength.l_75.value)] = ''
    code: Annotated[str, StringConstraints(max_length=FieldLength.l_5.value)] = ''
