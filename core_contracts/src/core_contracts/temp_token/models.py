from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum, StrEnum

from core_contracts.metainfo import FieldMetaData, FieldLength


@dataclass
class TempToken:
    token: str = field(metadata={FieldMetaData.max_length.value:FieldLength.l_100.value})
    type: int|None
    expired_at: datetime
    json_data: str


class TempTokenFields(StrEnum):
    TOKEN = 'token'
    TYPE = 'type'
    EXPIRED_AT = 'expired_at'
    JSON_DATA = 'json_data'


class TokenType(IntEnum):
    SIGNUP_2FA = 1
    SIGNIN_2FA = 2
