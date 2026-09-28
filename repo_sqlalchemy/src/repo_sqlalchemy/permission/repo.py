from typing import Sequence

from sqlalchemy import select, or_, and_, func, Integer

from core_contracts.permission.repositories import IRoleRepository, IApplicationResourceRepository, IRolePermissionRepository
from core_contracts.base import AccessMode
from core_contracts.permission import models

from repo_sqlalchemy.schema import BaseRepo, SeanceManager
from repo_sqlalchemy.permission import entities


class ApplicationResourceRepository(BaseRepo[entities.ApplicationResource, models.ApplicationResource], IApplicationResourceRepository):

    def __init__(self, seance_manager: SeanceManager) -> None:
        super().__init__(entities.ApplicationResource, models.ApplicationResource, seance_manager)

    def list(self) -> Sequence[models.ApplicationResource]:

        stmt = select(entities.ApplicationResource).order_by(entities.ApplicationResource.id)
        entries: Sequence[entities.ApplicationResource]
        seance = self._seance()
        with seance.begin():
            entries = seance.scalars(stmt).all()

        return [self._to_model_obj(entry, models.ApplicationResource) for entry in entries]


class RoleRepository(BaseRepo[entities.Role, models.Role], IRoleRepository):

    def __init__(self,seance_manager: SeanceManager) -> None:
        super().__init__(entities.Role, models.Role, seance_manager)

    def list(self) -> Sequence[models.Role]:

        stmt = select(entities.Role).order_by(entities.Role.id)
        entries: Sequence[entities.Role]
        seance = self._seance()
        with seance.begin():
            entries = seance.scalars(stmt).all()

        return [self._to_model_obj(entry, models.Role) for entry in entries]


class RolePermissionRepository(BaseRepo[entities.RolesPermissions, models.RolePermission], IRolePermissionRepository):

    def __init__(self, seance_manager: SeanceManager) -> None:
        super().__init__(entities.RolesPermissions, models.RolePermission, seance_manager)


    def list_by_id(self, role_id: int, resource_id: int) -> Sequence[models.Permission]:

        permissions: list[models.Permission] = []
        
        specific_perms = and_(entities.RolesPermissions.role_id == role_id, entities.RolesPermissions.resource_id == resource_id)
        default_role_perms = and_(entities.RolesPermissions.role_id == role_id, entities.RolesPermissions.resource_id == None)
        default_resource_perms = and_(entities.RolesPermissions.role_id == None, entities.RolesPermissions.resource_id == resource_id)

        weight_clmn = (func
            .weigh_role_permission(entities.RolesPermissions.role_id, entities.RolesPermissions.resource_id, entities.RolesPermissions.mode, type_=Integer)                       
            .label('weight')
        )

        stmt = (select(entities.RolesPermissions, weight_clmn)
            .order_by(weight_clmn)
            .where(or_(specific_perms, default_role_perms, default_resource_perms))
        )

        seance = self._seance()
        with seance.begin():
            for row in seance.execute(stmt):
                perm, weight = row._t
                permission = self._to_model_obj(perm, models.Permission)
                permission.weight = weight
                permissions.append(permission)
        
        return permissions


    def list_by_resource_name(self, role_id: int, resource_name: str) -> Sequence[tuple[models.RolePermission, int]]:

        entries = self._list_permissions_core(role_id, resource_name)

        if len(entries) == 0:
            return []

        items = sorted(entries, key = lambda e: e[1])
        return [(self._to_model_obj(p, models.RolePermission), w) for p, w in items]


    def fetch_lightest_by_name(self, role_id: int, resource_name: str, mode: AccessMode) -> models.RolePermission:

        entries = self._list_permissions_core(role_id, resource_name)
        if len(entries) == 0:
            return models.RolePermission(None, None, None, False, False, False, False, False)

        entry: entities.RolesPermissions | None = None
        for item, w in entries:
            if item.mode is None:
                entry = item
                break

            if item.mode == mode.value:
                entry = item
                break;

        if entry is None:
            return models.RolePermission(None, None, None, False, False, False, False, False)
        
        return self._to_model_obj(entry, self._data_cls)


    def _list_permissions_core(self, role_id: int, resource_name: str, /) -> Sequence[tuple[entities.RolesPermissions, int]]:
        
        entries: list[tuple[entities.RolesPermissions, int]] = []

        specific_perms = and_(entities.RolesPermissions.role_id == role_id, entities.ApplicationResource.name == resource_name)
        default_role_perms = and_(entities.RolesPermissions.role_id == role_id, entities.ApplicationResource.name == None)
        default_resource_perms = and_(entities.RolesPermissions.role_id == None, entities.ApplicationResource.name == resource_name)

        weight_clmn = (func
            .weigh_role_permission(entities.RolesPermissions.role_id, entities.RolesPermissions.resource_id, entities.RolesPermissions.mode, type_=Integer)
            .label('weight')
        )

        stmt = (select(entities.RolesPermissions, weight_clmn)
            .order_by(weight_clmn)
            .outerjoin(entities.ApplicationResource, entities.RolesPermissions.resource_id == entities.ApplicationResource.id)
            .where(or_(specific_perms, default_role_perms, default_resource_perms))
        )

        seance = self._seance()
        min_weight = 9999
        with seance.begin():
            for row in seance.execute(stmt):
                perm, weight = row._t
                if weight < min_weight:
                    min_weight = weight

                entries.append((perm, weight))

        return entries
