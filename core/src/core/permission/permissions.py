from enum import StrEnum
from typing import Callable

from core_contracts.handler import Claims, MessageType
from core_contracts.issues import ValidationIssue, NotFoundEntryIssue, ForbiddenIssue
from core_contracts.base import AccessMode, Resources
from core_contracts.permission.repositories import (IRolePermissionRepository
                                              , IApplicationResourceRepository
                                              , IRoleRepository
                                              , RolePermission
                                              , Permission)
from core.permission.demands import PermissionDemand, NewPermissionDemand
from core.handler import (Handler
                          , DemandContext
                          , Response
                          , ListAuthorizationFilter
                          , SingleItemAuthorizationFilter
                          , get_default_pipeline
                          , Pipeline)


class Arguments(StrEnum):
    ROLE_ID = 'role_id'
    RESOURCE_ID = 'resource_id'
    PERMISSION_ID = 'permission_id'


class ListApplicationResourcesAuthorizationFilter(ListAuthorizationFilter):
    @property
    def resource(self) -> str:
        return Resources.APPLICATION_RESOURCES


class ListAppResourcesHandler:

    def __init__(self, resources_repo: IApplicationResourceRepository) -> None:
        self._resources_repo: IApplicationResourceRepository = resources_repo

    def execute(self, ctx: DemandContext) -> Response:
        resources = self._resources_repo.list()
        return Response(200, data=resources)


def list_app_resources_pipeline(perm_repo: IRolePermissionRepository) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(ListApplicationResourcesAuthorizationFilter(perm_repo).authorize_operation)
    return pipeline


class ListRolesAuthorizationHandler(ListAuthorizationFilter):
    @property
    def resource(self) -> str:
        return Resources.ROLES


class ListRolesHandler(Handler):

    def __init__(self, roles_repo: IRoleRepository) -> None:
        self._roles_repo: IRoleRepository = roles_repo

    def execute(self, ctx: DemandContext) -> Response:
        roles = self._roles_repo.list()
        return Response(200, data=roles)


def list_roles_pipeline(perm_repo: IRolePermissionRepository) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(ListRolesAuthorizationHandler(perm_repo).authorize_operation)
    return pipeline


def validate_list_arguments_filter(ctx: DemandContext, next: Callable[[], Response]) -> Response:

    role_id = ctx.arguments.get(Arguments.ROLE_ID)
    resource_id = ctx.arguments.get(Arguments.RESOURCE_ID)

    if role_id is None or role_id <=0:
        raise ValidationIssue('role id is required')

    if resource_id is None or resource_id <= 0:
        raise ValidationIssue('resource id is required')

    return next()


class ListPermissionsAuthorizationFilter(ListAuthorizationFilter):

    @property
    def resource(self) -> str:
        return Resources.ROLE_PERMISSIONS


class ListPermissionsHandler(Handler):

    def __init__(self, perm_repo: IRolePermissionRepository) -> None:
        self._perm_repo:IRolePermissionRepository = perm_repo

    def execute(self, ctx: DemandContext) -> Response:

        role_id = ctx.arguments.get(Arguments.ROLE_ID, 0)
        resource_id = ctx.arguments.get(Arguments.RESOURCE_ID, 0)
        permissions = self._perm_repo.list_by_id(role_id, resource_id)

        return Response(200, data=permissions)


def list_permissions_pipeline(perm_repo: IRolePermissionRepository) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(validate_list_arguments_filter)
    pipeline.use(ListPermissionsAuthorizationFilter(perm_repo).authorize_operation)
    return pipeline


def validate_perm_id_arg_filter(ctx: DemandContext, next: Callable[[], Response]) -> Response:

    perm_id = ctx.arguments.get(Arguments.PERMISSION_ID)
    if perm_id is None or perm_id <= 0:
        raise ValidationIssue('permission id is required')

    return next()


def validate_perm_demand_filter(ctx: DemandContext, next: Callable[[], Response]) -> Response:

    demand = ctx.get_demand(PermissionDemand)

    mode = demand.mode
    if mode is not None and not (mode == AccessMode.own or mode == AccessMode.nonown):
        raise ValidationIssue('invalid value of mode')

    if demand.allow_enumerate is None:
        raise ValidationIssue('allow_enumerate is required')

    if demand.allow_read is None:
        raise ValidationIssue('allow_read is required')

    if demand.allow_create is None:
        raise ValidationIssue('allow_create is required')

    if demand.allow_edit is None:
        raise ValidationIssue('allow_edit is required')

    if demand.allow_delete is None:
        raise ValidationIssue('allow_delete is required')
    
    return next()


class _PermissionAuthorizationFilter:
    def __init__(self, perm_repo: IRolePermissionRepository) -> None:
        self._perm_repo: IRolePermissionRepository = perm_repo

    @property
    def resource(self) -> str:
        return Resources.ROLE_PERMISSIONS

    def authorize_operation(self, ctx: DemandContext, next: Callable[[], Response]) -> Response:

        usr_claims = ctx.current_usr_claims
        if usr_claims is None:
            raise ForbiddenIssue('Please authorize.')

        perms = self._perm_repo.list_by_resource_name(usr_claims.role_id, self.resource)
        if len(perms) == 0:
            raise ForbiddenIssue('Please authorize.')

        perm, w = perms[0]
        if perm.mode is not None:
            raise ForbiddenIssue(f'You do not have access to {self.resource}')

        self.allow_operation(perm)
        return next()

    def allow_operation(self, perm: RolePermission):
        raise NotImplementedError


class EditPermissionAuthorizationFilter(_PermissionAuthorizationFilter):

    def allow_operation(self, perm: RolePermission):
        if not perm.allow_edit:
            raise ForbiddenIssue(f'You do not have access to {self.resource}')


class EditPermissionHandler(Handler):

    def __init__(self, perm_repo: IRolePermissionRepository) -> None:
        self._perm_repo:IRolePermissionRepository = perm_repo

    def execute(self, ctx: DemandContext) -> Response:

        perm_id = ctx.arguments.get(Arguments.PERMISSION_ID, 0)
        role_id = ctx.arguments.get(Arguments.ROLE_ID, 0)
        resource_id = ctx.arguments.get(Arguments.RESOURCE_ID, 0)
        demand = ctx.get_demand(PermissionDemand)

        perms = self._perm_repo.list_by_id(role_id, resource_id)
        permission = next((p for p in perms if p.id == perm_id), None)
        if permission is None:
            raise NotFoundEntryIssue('Permission is not located')

        mismatch = False
        
        # None       => own-nonown
        if permission.mode is None and demand.mode is not None:
            collision = next((p for p in perms if p.weight == permission.weight-1 and p.mode == demand.mode), None)
            mismatch = collision is not None

        # own-nonown => None
        elif permission.mode is not None and demand.mode is None:
            collision = next((p for p in perms if p.weight == permission.weight+1 and p.mode is None), None)
            mismatch = collision is not None

        # own-nonown => (nonown-own)
        else:    
            collision = next((p for p in perms if p.weight == permission.weight and p.mode == demand.mode), None)
            mismatch = collision is not None and collision.id != permission.id

        if mismatch:
            raise ValidationIssue('Permission can not be edited. It conflicts with anouther one.')

        permission.mode = demand.mode
        permission.allow_enumerate = demand.allow_enumerate
        permission.allow_read = demand.allow_read
        permission.allow_create = demand.allow_create
        permission.allow_edit = demand.allow_edit
        permission.allow_delete = demand.allow_delete

        self._perm_repo.save(permission)

        return Response(200, data=permission)


def edit_permission_pipeline(perm_repo: IRolePermissionRepository) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(validate_list_arguments_filter)
    pipeline.use(validate_perm_id_arg_filter)
    pipeline.use(validate_perm_demand_filter)
    pipeline.use(EditPermissionAuthorizationFilter(perm_repo).authorize_operation)
    return pipeline


class CreatePermissionAuthorizationFilter(_PermissionAuthorizationFilter):

    def allow_operation(self, perm: RolePermission):
        if not perm.allow_create:
            raise ForbiddenIssue(f'You do not have access to {self.resource}')


def create_permission_pipeline(perm_repo: IRolePermissionRepository) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(validate_list_arguments_filter)
    pipeline.use(validate_perm_demand_filter)
    pipeline.use(CreatePermissionAuthorizationFilter(perm_repo).authorize_operation)
    return pipeline


class CreatePermissionHandler(Handler):

    def __init__(self, perm_repo: IRolePermissionRepository) -> None:
        self._perm_repo:IRolePermissionRepository = perm_repo

    def execute(self, ctx: DemandContext) -> Response:

        role_id = ctx.arguments.get(Arguments.ROLE_ID, 0)
        resource_id = ctx.arguments.get(Arguments.RESOURCE_ID, 0)
        demand = ctx.get_demand(NewPermissionDemand)

        if demand.role_id is not None and demand.role_id != role_id:
            raise ValidationIssue('Unallowed role id is specified')

        if demand.resource_id is not None and demand.resource_id != resource_id:
            raise ValidationIssue('Unallowed resource id is specified')

        perms = self._perm_repo.list_by_id(role_id, resource_id)

        mismatch = next((p 
            for p in perms 
            if p.role_id == demand.role_id and p.resource_id == demand.resource_id and p.mode == demand.mode)
            , None
        )

        if mismatch is not None:
            raise ValidationIssue('State mismatch is detected. Please correct your request')

        perm = RolePermission(
            demand.role_id,
            demand.resource_id,
            demand.mode,
            demand.allow_enumerate,
            demand.allow_read,
            demand.allow_create,
            demand.allow_edit,
            demand.allow_delete
        )

        perm = self._perm_repo.save(perm)

        return Response(200, data=Permission(
                perm.role_id,
                perm.resource_id,
                perm.mode,
                perm.allow_enumerate,
                perm.allow_read,
                perm.allow_create,
                perm.allow_edit,
                perm.allow_delete,
                id=perm.id
            )
        )


class DeletePermissionAuthorizationFilter(_PermissionAuthorizationFilter):

    def allow_operation(self, perm: RolePermission):
        if not perm.allow_delete:
            raise ForbiddenIssue(f'You do not have access to {self.resource}')


def delete_permission_pipeline(perm_repo: IRolePermissionRepository) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(validate_perm_id_arg_filter)
    pipeline.use(DeletePermissionAuthorizationFilter(perm_repo).authorize_operation)
    return pipeline


class DeletePermissionHandler(Handler):

    def __init__(self, perm_repo: IRolePermissionRepository) -> None:
        self._perm_repo:IRolePermissionRepository = perm_repo

    def execute(self, ctx: DemandContext) -> Response:

        perm_id = ctx.arguments.get(Arguments.PERMISSION_ID, 0)
        perm = self._perm_repo.fetch_by_id(perm_id)
        if perm is None:
            return Response(200)

        self._perm_repo.delete(perm_id)

        return Response(200)


class FetchPermissionAuthorizationFilter(_PermissionAuthorizationFilter):

    def allow_operation(self, perm: RolePermission):
        if not perm.allow_read:
            raise ForbiddenIssue(f'You do not have access to {self.resource}')


def fetch_permission_pipeline(perm_repo: IRolePermissionRepository) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(validate_perm_id_arg_filter)
    pipeline.use(FetchPermissionAuthorizationFilter(perm_repo).authorize_operation)
    return pipeline


class FetchPermissionHandler(Handler):

    def __init__(self, perm_repo: IRolePermissionRepository) -> None:
        self._perm_repo:IRolePermissionRepository = perm_repo

    def execute(self, ctx: DemandContext) -> Response:

        perm_id = ctx.arguments.get(Arguments.PERMISSION_ID, 0)
        perm = self._perm_repo.fetch_by_id(perm_id)
        if perm is None:
            resp = Response(404)
            resp.add_message('Permission is not located', MessageType.info)
            return resp

        return Response(200, data=Permission(
                perm.role_id,
                perm.resource_id,
                perm.mode,
                perm.allow_enumerate,
                perm.allow_read,
                perm.allow_create,
                perm.allow_edit,
                perm.allow_delete,
                id=perm.id
            )
        )
