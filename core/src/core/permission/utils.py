from typing import Sequence
from core_contracts.permission import models
from core_contracts.base import AccessMode


def _default_deny_permission() -> models.RolePermission:
    return models.RolePermission(
        role_id=None,
        resource_id=None,
        mode=None,
        allow_enumerate=False,
        allow_read=False,
        allow_create=False,
        allow_edit=False,
        allow_delete=False)


def fetch_lightest_permission(entries:Sequence[models.Permission], mode: AccessMode) -> models.RolePermission:
    entry: models.RolePermission | None = None
    for item in entries:
        if item.mode is None:
            entry = item
            break

        if item.mode == mode.value:
            entry = item
            break;

    if entry is None:
        entry = _default_deny_permission()

    return entry
