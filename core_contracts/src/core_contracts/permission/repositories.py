from abc import abstractmethod
from typing import Sequence

from core_contracts.permission.models import Role, RolePermission, ApplicationResource, Permission
from core_contracts.base import IRepository, AccessMode


class IRoleRepository(IRepository[Role]):

    @abstractmethod
    def list(self) -> Sequence[Role]:
        raise NotImplementedError


class IApplicationResourceRepository(IRepository[ApplicationResource]):

    @abstractmethod
    def list(self) -> Sequence[ApplicationResource]:
        raise NotImplementedError


class IRolePermissionRepository(IRepository[RolePermission]):

    @abstractmethod
    def fetch_lightest_by_name(self, role_id: int, resource_name: str, mode: AccessMode) -> RolePermission:
        raise NotImplementedError

    @abstractmethod
    def list_by_id(self, role_id: int, resource_id: int, /) -> Sequence[Permission]:
        raise NotImplementedError

    @abstractmethod
    def list_by_resource_name(self, role_id: int, resource_name: str) -> Sequence[tuple[RolePermission, int]]:
        raise NotImplementedError
