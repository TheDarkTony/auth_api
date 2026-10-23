from typing import Annotated, Any
from enum import StrEnum

from pydantic import BaseModel, StringConstraints, model_serializer

from core_contracts.metainfo import FieldLength


class RoleSubject(BaseModel):
    name: Annotated[str, StringConstraints(max_length=FieldLength.l_25.value)]
    description: Annotated[str, StringConstraints(max_length=FieldLength.l_100.value)]


class Role(RoleSubject):
    id: int = 0


class RoleFields(StrEnum):
    NAME = 'name'
    DESCRIPTION = 'description'
    ID = 'id'


class ApplicationResourceSubject(BaseModel):
    name: Annotated[str, StringConstraints(max_length=FieldLength.l_25.value)]
    description: Annotated[str, StringConstraints(max_length=FieldLength.l_100.value)]


class ApplicationResource(ApplicationResourceSubject):
    id: int = 0


class ApplicationResourceFields(StrEnum):
    NAME = 'name'
    DESCRIPTION = 'description'
    ID = 'id'


class PermissionSubject(BaseModel):
    role_id: int | None = None
    resource_id: int | None = None

    mode: str | None = None
    allow_enumerate: bool
    allow_read: bool
    allow_create: bool
    allow_edit: bool
    allow_delete: bool


    @model_serializer(mode='wrap')
    def serialize_bool_to_int(self, handler) -> dict[str, Any]:
        result: dict[str, Any] = handler(self)
        for k, v in result.items():
            if isinstance(v, bool):
                result[k] = 1 if v else 0
        return result


class RolePermission(PermissionSubject):
    id: int = 0


class RolePermissionFields(StrEnum):
    ROLE_ID = 'role_id'
    RESOURCE_ID = 'resource_id'
    MODE = 'mode'
    ALLOW_ENUMERATE = 'allow_enumerate'
    ALLOW_READ = 'allow_read'
    ALLOW_CREATE = 'allow_create'
    ALLOW_EDIT = 'allow_edit'
    ALLOW_DELETE = 'allow_delete'
    ID = 'id'


class Permission(RolePermission):
    weight: int = 9999
    name: str | None = None

    def model_post_init(self, context: Any) -> None:
        if self.resource_id is not None and self.role_id is not None:
            self.name = 'role permission'
            self.weight = 2 if self.mode is None else 1

        elif self.resource_id is None and self.role_id is None:
            self.name = 'default role'
            self.weight = 4 if self.mode is None else 3

        elif self.resource_id is None and self.role_id is not None:
            self.name = 'default resource permission'
            self.weight = 6 if self.mode is None else 5
            
        elif self.resource_id is not None and self.role_id is None:
            self.name = 'default role permission'
            self.weight = 7
