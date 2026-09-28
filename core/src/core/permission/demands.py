from dataclasses import dataclass

@dataclass
class PermissionDemand:
    mode: str | None
    allow_enumerate: bool
    allow_read: bool
    allow_create: bool
    allow_edit: bool
    allow_delete: bool


@dataclass
class NewPermissionDemand(PermissionDemand):
    role_id: int|None
    resource_id: int|None