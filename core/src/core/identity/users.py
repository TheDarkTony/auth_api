from typing import Callable

from core.utils import verify_hash, hashpwd, most_left_right_cursors
from core.handler import (Handler, Pipeline, DemandContext, Response
                          , SingleItemAuthorizationFilter, ListAuthorizationFilter
                          , get_default_pipeline
                          , get_mode_by_user
                          , Claims)

from core_contracts.base import utcnow, Resources, AccessMode, BatchResponse, IdentityArguments, PagginationArguments
from core_contracts.handler import MessageType
from core_contracts.identity.repositories import IUserRepository, IUserTempBlackListRepository
from core_contracts.permission.models import RolePermission
from core_contracts.permission.repositories import IRolePermissionRepository
from core_contracts.issues import ValidationIssue, ForbiddenIssue, NotFoundEntryIssue

from core.identity.demands import ChangePwdDemand, EditUserDemand


class ListUsersAuthorizationFilter(ListAuthorizationFilter):
    @property
    def resource(self) -> str:
        return Resources.USERS


class ListUsersHandler:
    def __init__(self, usr_repo: IUserRepository) -> None:
        self._usr_repo: IUserRepository = usr_repo

    def execute(self, ctx: DemandContext) -> Response:

        predicate = ctx.arguments
        users = self._usr_repo.list(predicate)
        next_cursor, prev_cursor = most_left_right_cursors(users)

        cursor = predicate.get(PagginationArguments.NEXT_CURSOR)
        if cursor is None:
            cursor = predicate.get(PagginationArguments.PREV_CURSOR)
        
        if next_cursor is not None:
            next_cursor = str(next_cursor)

        if prev_cursor is not None:
            prev_cursor = str(prev_cursor) if cursor is not None else None

        return Response(200, data=BatchResponse(next_cursor, prev_cursor, users))


def pipeline_list_user(perm_repo: IRolePermissionRepository) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(ListUsersAuthorizationFilter(perm_repo).authorize_operation)
    return pipeline


class _UserAuthorizationFilter(SingleItemAuthorizationFilter):

    def __init__(self, perm_repo: IRolePermissionRepository) -> None:
        super().__init__(perm_repo)

    @property
    def resource(self) -> str:
        return Resources.USERS

    def _get_mode_core(self, claims: Claims, ctx: DemandContext) -> AccessMode:
        return get_mode_by_user(claims, ctx)


class ReadUserAuthorizationFilter(_UserAuthorizationFilter):

    def authorize_core(self, permission: RolePermission):
        if not permission.allow_read:
            raise ForbiddenIssue('You do not have access to read user')


class DeleteUserAuthorizationFilter(_UserAuthorizationFilter):

    def authorize_core(self, permission: RolePermission):
        if not permission.allow_delete:
            raise ForbiddenIssue('You do not have access to delete user')


class EditUserAuthorizationFilter(_UserAuthorizationFilter):

    def authorize_core(self, permission: RolePermission):
        if not permission.allow_edit:
            raise ForbiddenIssue('You do not have access to edit user')


def verify_user_argument_filter(ctx: DemandContext, next: Callable[[], Response]) -> Response:

    usr_id = ctx.arguments.get(IdentityArguments.USER_ID)
    if usr_id is None or not isinstance(usr_id, int):
        raise ValidationIssue('user id is required.')

    if usr_id <= 0:
        raise ValidationIssue('user id should be greater than 0.')

    return next()


class FetchUserHandler(Handler):

    def __init__(self, usr_repo: IUserRepository) -> None:
        self._usr_repo: IUserRepository = usr_repo

    def execute(self, ctx: DemandContext) -> Response:
        usr_id = ctx.arguments.get(IdentityArguments.USER_ID, 0)
        usr = self._usr_repo.fetch_by_id(usr_id)

        if usr is None:
            r = Response(404)
            r.add_message('User is not located', MessageType.info)
            return r

        if usr.archived:
            r = Response(410)
            r.add_message('User has been deleted', MessageType.info)
            return r

        return Response(200, data=usr)


def pipeline_fetch_user(perm_repo: IRolePermissionRepository) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(verify_user_argument_filter)
    pipeline.use(ReadUserAuthorizationFilter(perm_repo).authorize_operation)
    return pipeline


class DeleteUserHandler(Handler):

    def __init__(self, usr_repo: IUserRepository
        , user_temp_black_list_repo: IUserTempBlackListRepository
        , access_token_seconds_ttl: int
        ) -> None:
        self._usr_repo: IUserRepository = usr_repo
        self._user_temp_black_list_repo: IUserTempBlackListRepository = user_temp_black_list_repo
        self._access_token_seconds_ttl: int = access_token_seconds_ttl

    def execute(self, ctx: DemandContext) -> Response:

        usr_id = ctx.arguments.get(IdentityArguments.USER_ID, 0)
        usr = self._usr_repo.fetch_by_id(usr_id)
        if usr is None:
            raise NotFoundEntryIssue('User is not located')

        if usr.deleted_date is None:
            usr.deleted_date = utcnow()
            self._usr_repo.save(usr)

        self._user_temp_black_list_repo.push_to_black_list(usr.id, self._access_token_seconds_ttl)

        return Response(200)


def pipeline_delete_user(perm_repo: IRolePermissionRepository) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(verify_user_argument_filter)
    pipeline.use(DeleteUserAuthorizationFilter(perm_repo).authorize_operation)
    return pipeline


def validate_change_pwd_demand_filter(ctx: DemandContext, next: Callable[[], Response]) -> Response:

    demand = ctx.get_demand(ChangePwdDemand)

    if demand is None:
        raise ValidationIssue('Demand body is required')

    if demand.old_pwd is None:
        raise ValidationIssue('old password is required')

    if demand.new_pwd is None:
        raise ValidationIssue('new password is required')

    if demand.new_pwd_confirmed is None:
        raise ValidationIssue('password confirmation is required')

    if demand.new_pwd != demand.new_pwd_confirmed:
        raise ValidationIssue('new password and confirmation does not match')

    return next()


class ChangePwdHandler(Handler):

    def __init__(self, usr_repo: IUserRepository) -> None:
        self._usr_repo: IUserRepository = usr_repo

    def execute(self, ctx: DemandContext) -> Response:
    
        usr_id = ctx.arguments.get(IdentityArguments.USER_ID, 0)
        usr = self._usr_repo.fetch_by_id(usr_id)
        if usr is None:
            raise NotFoundEntryIssue('User is not located')

        demand = ctx.get_demand(ChangePwdDemand)

        if not verify_hash(demand.old_pwd or '', usr.pwd):
            raise ValidationIssue('Old password is incorrect')

        usr.pwd = hashpwd(demand.new_pwd or '')
        usr = self._usr_repo.save(usr)

        return Response(200)


def pipeline_change_pwd(perm_repo: IRolePermissionRepository) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(verify_user_argument_filter)
    pipeline.use(validate_change_pwd_demand_filter)
    pipeline.use(EditUserAuthorizationFilter(perm_repo).authorize_operation)
    return pipeline


def verify_edit_user_demand_filter(ctx: DemandContext, next: Callable[[], Response]) -> Response:

    demand = ctx.get_demand(EditUserDemand)
    if demand is None or demand.email_2fa_enabled is None:
        raise ValidationIssue('Demand data is required.')

    return next()


class EditUserHandler(Handler):

    def __init__(self, usr_repo: IUserRepository) -> None:
            self._usr_repo: IUserRepository = usr_repo
    
    def execute(self, ctx: DemandContext) -> Response:

        usr_id = ctx.arguments.get(IdentityArguments.USER_ID, 0)
        usr = self._usr_repo.fetch_by_id(usr_id)
        if usr is None:
            raise NotFoundEntryIssue('User is not located')

        demand = ctx.get_demand(EditUserDemand)

        if usr.email_2fa_enabled != demand.email_2fa_enabled:
            usr.email_2fa_enabled = demand.email_2fa_enabled
            usr = self._usr_repo.save(usr)

        return Response(200, data=usr)


def pipeline_edit_user(perm_repo: IRolePermissionRepository) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(verify_user_argument_filter)
    pipeline.use(verify_edit_user_demand_filter)
    pipeline.use(EditUserAuthorizationFilter(perm_repo).authorize_operation)
    return pipeline
