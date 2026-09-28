from enum import IntEnum, StrEnum
from typing import Protocol, ClassVar, Dict, Any, Type


class FieldMetaData(StrEnum):
    max_length = 'max_length'


class FieldLength(IntEnum):
    l_5 = 5
    l_25 = 25
    l_50 = 50
    l_75 = 75
    l_100 = 100


class DataclassModel(Protocol):
    __dataclass_fields__: ClassVar[Dict[str, Any]]


def metainfo_int(model: Type[DataclassModel], field: str, metakey: str) -> int:
    return model.__dataclass_fields__[field].metadata.get(metakey)