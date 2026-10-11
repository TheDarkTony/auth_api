from pydantic import BaseModel, field_validator
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

    @field_validator('allow_enumerate', mode='before')
    @classmethod
    def validate_allow_enumerate(cls, value):
        if value is None:
            raise ValueError('allow_enumerate is required')
        return value

    @field_validator('allow_read', mode='before')
    @classmethod
    def validate_allow_read(cls, value):
        if value is None:
            raise ValueError('allow_read is required')
        return value

    @field_validator('allow_create', mode='before')
    @classmethod
    def validate_allow_create(cls, value):
        if value is None:
            raise ValueError('allow_create is required')
        return value

    @field_validator('allow_edit', mode='before')
    @classmethod
    def validate_allow_edit(cls, value):
        if value is None:
            raise ValueError('allow_edit is required')
        return value

    @field_validator('allow_delete', mode='before')
    @classmethod
    def validate_allow_delete(cls, value):
        if value is None:
            raise ValueError('allow_delete is required')
        return value


class NewPermissionDemand(PermissionDemand):
    role_id: int|None
    resource_id: int|None
