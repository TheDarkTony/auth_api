from dataclasses import dataclass, field

from core_contracts.metainfo import FieldLength, FieldMetaData

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


@dataclass
class Sign2FAFeedbackDemand:
    process_token: str = field(default='', metadata={FieldMetaData.max_length.value: FieldLength.l_75.value})
    code: str = field(default='', metadata={FieldMetaData.max_length.value: FieldLength.l_5.value})