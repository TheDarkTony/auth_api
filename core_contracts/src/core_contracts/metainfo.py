from enum import IntEnum
from typing import Protocol, ClassVar, Dict, Any, Type
from pydantic import BaseModel, StringConstraints


class FieldLength(IntEnum):
    l_5 = 5
    l_25 = 25
    l_50 = 50
    l_75 = 75
    l_100 = 100


class DataclassModel(Protocol):
    __dataclass_fields__: ClassVar[Dict[str, Any]]


def get_metainfo(model: Type[BaseModel], field_name: str) -> StringConstraints:
    field = model.model_fields.get(field_name, None)
    if field is None or field.annotation is None:
        raise Exception(f'meta info is missed for {field_name} of {model}')

    for arg in field.metadata:
        if isinstance(arg, StringConstraints):
            return arg

    raise Exception(f'meta info is missed for {field_name} of {model}')
