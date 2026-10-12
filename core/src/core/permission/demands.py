from pydantic import BaseModel, field_validator, ValidationInfo
from core_contracts.base import AccessMode


class PermissionDemand(BaseModel):
    mode: str | None
    allow_enumerate: bool
    allow_read: bool
    allow_create: bool
    allow_edit: bool
    allow_delete: bool

    @field_validator('mode', mode='before')
    @classmethod
    def validate_mode(cls, value):

        if value is not None and not (value == AccessMode.own or value == AccessMode.nonown):
            raise ValueError('mode value is invalid')
        return value

    @field_validator('allow_enumerate', 'allow_read', 'allow_create', 'allow_edit', 'allow_delete',  mode='before')
    @classmethod
    def validate_allow_enumerate(cls, value, info: ValidationInfo):
        if value is None:
            raise ValueError(f'{info.field_name} is required')
        return value


class NewPermissionDemand(PermissionDemand):
    role_id: int|None
    resource_id: int|None
