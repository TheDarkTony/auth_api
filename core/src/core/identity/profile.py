from enum import StrEnum
from typing import Callable

from core_contracts.identity.repositories import IUserRepository, IIdentityRepository
from core_contracts.permission.repositories import IRolePermissionRepository
from core_contracts.issues import ForbiddenIssue, NotFoundEntryIssue
from core_contracts.base import AccessMode, Resources
from core_contracts.identity.models import ProfileResponse, Identity, User

from core.handler import Handler, Response, Pipeline, DemandContext, get_default_pipeline


class ProfileArguments(StrEnum):
    IDENTITY_ID = 'identity_id'
    USER_ID = 'usr_id'


class FetchProfileAuthorizationFilter:

    def __init__(self, perm_repo: IRolePermissionRepository) -> None:
        self._perm_repo: IRolePermissionRepository = perm_repo

    def authorize_operation(self, ctx: DemandContext, next: Callable[[], Response]) -> Response:

        usr_claims = ctx.current_usr_claims
        if usr_claims is None:
            raise ForbiddenIssue('Please authorize.')

        mode = AccessMode.own
        identity_perm = self._perm_repo.fetch_lightest_by_name(usr_claims.role_id, Resources.IDENTITIES, mode)
        user_perm = self._perm_repo.fetch_lightest_by_name(usr_claims.role_id, Resources.USERS, mode)

        if user_perm.allow_read:
            ctx.arguments[ProfileArguments.USER_ID] = usr_claims.user_id

        if user_perm.allow_read:
            ctx.arguments[ProfileArguments.IDENTITY_ID] = usr_claims.identity_id

        if not user_perm.allow_read and not identity_perm.allow_read:
            raise ForbiddenIssue('You do not have access to read profile information')

        return next()


class FetchProfileHandler(Handler):

    def __init__(self, usr_repo: IUserRepository, identity_repo: IIdentityRepository) -> None:
        self._usr_repo: IUserRepository = usr_repo
        self._identity_repo: IIdentityRepository = identity_repo

    def execute(self, ctx: DemandContext) -> Response:

        identity: Identity|None = None
        user: User | None = None
        identity_id = ctx.arguments.get(ProfileArguments.IDENTITY_ID, 0)
        if identity_id > 0:
            identity = self._identity_repo.fetch_by_id(identity_id)
            if identity is None:
                raise NotFoundEntryIssue('Identity is not located')

        user_id = ctx.arguments.get(ProfileArguments.USER_ID, 0)
        if user_id > 0:
            user = self._usr_repo.fetch_by_id(user_id)
            if user is None:
                raise NotFoundEntryIssue('User is not located')

        return Response(200, data=ProfileResponse(identity=identity, user=user))


def pipeline_fetch_profile(perm_repo: IRolePermissionRepository) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(FetchProfileAuthorizationFilter(perm_repo).authorize_operation)
    return pipeline
