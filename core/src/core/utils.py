from enum import IntEnum
from datetime import datetime, timezone, timedelta
from typing import Protocol, Sequence

import bcrypt


def hashpwd(pwd:str, salt: str|bytes|None = None) -> str:

    if salt is None:
        salt = bcrypt.gensalt()

    encoding = 'utf-8'
    hash_pwd = bcrypt.hashpw(pwd.encode(encoding), bcrypt.gensalt(10))
    return hash_pwd.decode(encoding)


def verify_hash(value: str, hash: str) -> bool:
    val = value.encode('utf-8')
    return bcrypt.checkpw(val, hash.encode('utf-8')) 


def utc_plus_delta(seconds:int)->datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=seconds)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IdentifiableModel(Protocol):
    id:int


def most_left_right_cursors(items: Sequence[IdentifiableModel]) -> tuple[int|None, int|None]:
    next_cursor = None
    prev_cursor = None
    if len(items) > 0:
        next_cursor = prev_cursor = items[0].id
        for item in items:
            if item.id > next_cursor:
                next_cursor = item.id
            if item.id < prev_cursor:
                prev_cursor = item.id

    return next_cursor, prev_cursor


class AcceptedStateEnum(IntEnum):
    Verification2FA = 1
