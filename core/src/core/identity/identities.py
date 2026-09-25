from typing import Callable

from core.handler import Handler, DemandContext, Response, Pipeline, get_default_pipeline, ListAuthorizationFilter, MessageType

from core_contracts.base import AccessMode, Resources, IdentityArguments, PagginationArguments, BatchResponse
from core_contracts.metainfo import FieldMetaData, metainfo_int
from core_contracts.issues import ValidationIssue, NotFoundEntryIssue, ForbiddenIssue
from core_contracts.identity.repositories import IIdentityRepository
from core_contracts.permission.repositories import IRolePermissionRepository
from core_contracts.identity.models import Identity, IdentityFields

from core.utils import most_left_right_cursors
from core.identity.demands import EditDemographicsDemand


def verify_identity_argument_filter(ctx: DemandContext, next: Callable[[], Response]) -> Response:

    identity_id = ctx.arguments.get(IdentityArguments.IDENTITY_ID)
    if identity_id is None or not isinstance(identity_id, int):
        raise ValidationIssue('Identity id is required.')

    if identity_id <= 0:
        raise ValidationIssue('Identity id should be greater than 0.')

    return next()


def verify_edit_demographics_demand_filter(ctx: DemandContext, next: Callable[[], Response]) -> Response:
    
    demand = ctx.get_demand(EditDemographicsDemand)
    max_fname_length = metainfo_int(Identity, IdentityFields.FNAME, FieldMetaData.max_length)
    if len(demand.fname) > max_fname_length:
        raise ValidationIssue(f'Length of email is greater than {max_fname_length}')

    max_lname_length = metainfo_int(Identity, IdentityFields.LNAME, FieldMetaData.max_length)
    if len(demand.lname) > max_lname_length:
        raise ValidationIssue(f'Length of email is greater than {max_lname_length}')

    return next()


class EditDemographicsAuthorizationFilter:

    def __init__(self, perm_repo: IRolePermissionRepository) -> None:
        self._perm_repo: IRolePermissionRepository = perm_repo

    def authorize_operation(self, ctx: DemandContext, next: Callable[[], Response]) -> Response:

        usr_claims = ctx.current_usr_claims
        if usr_claims is None:
            raise ForbiddenIssue('Please authorize.')

        identity_id = ctx.arguments.get(IdentityArguments.IDENTITY_ID, 0)

        mode = AccessMode.own if identity_id == usr_claims.identity_id else AccessMode.nonown
        perm = self._perm_repo.fetch_lightest_by_name(usr_claims.role_id, Resources.IDENTITIES, mode)

        if not perm.allow_edit:
            raise ForbiddenIssue('You do not have access to edit identity')

        return next()


def pipeline_edit_demographics(perm_repo: IRolePermissionRepository) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(verify_identity_argument_filter)
    pipeline.use(verify_edit_demographics_demand_filter)
    pipeline.use(EditDemographicsAuthorizationFilter(perm_repo).authorize_operation)
    return pipeline


class EditDemographicsHandler(Handler):

    def __init__(self, identity_repo: IIdentityRepository) -> None:
        self._identity_repo: IIdentityRepository = identity_repo

    def execute(self, ctx: DemandContext) -> Response:

        identity_id: int = ctx.arguments.get(IdentityArguments.IDENTITY_ID, 0)
        identity = self._identity_repo.fetch_by_id(identity_id)
        if identity is None:
            raise NotFoundEntryIssue('Identity is not located.')

        demand = ctx.get_demand(EditDemographicsDemand)

        identity.fname = demand.fname
        identity.lname = demand.lname

        identity = self._identity_repo.save(identity)

        return Response(200, data=identity)


def verify_identity_lookup_args_filter(ctx: DemandContext, next: Callable[[], Response]) -> Response:
    
    fname = ctx.arguments.get(IdentityFields.FNAME)
    if fname is not None:
        max_length = metainfo_int(Identity, IdentityFields.FNAME, FieldMetaData.max_length)
        if len(fname) > max_length:
            raise ValidationIssue('Length of first name is greater than allowed')

    lname = ctx.arguments.get(IdentityFields.LNAME)
    if lname is not None:
        max_length = metainfo_int(Identity, IdentityFields.LNAME, FieldMetaData.max_length)
        if len(lname) > max_length:
            raise ValidationIssue('Length of last name is greater than allowed')

    email = ctx.arguments.get(IdentityFields.EMAIL)
    if email is not None:
        max_length = metainfo_int(Identity, IdentityFields.EMAIL, FieldMetaData.max_length)
        if len(email) > max_length:
            raise ValidationIssue('Length of last name is greater than allowed')

    return next()


class ListIdentitiesAuthorizationFilter(ListAuthorizationFilter):

    @property
    def resource(self) -> str:
        return Resources.IDENTITIES


def pipeline_list_identities(perm_repo: IRolePermissionRepository) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(verify_identity_lookup_args_filter)
    pipeline.use(ListIdentitiesAuthorizationFilter(perm_repo).authorize_operation)
    return pipeline


class ListIdentitiesHandler(Handler):

    def __init__(self, identity_repo: IIdentityRepository) -> None:
        self._identity_repo: IIdentityRepository = identity_repo

    def execute(self, ctx: DemandContext) -> Response:

        predicate = ctx.arguments
        identities = self._identity_repo.list(predicate)
        next_cursor, prev_cursor = most_left_right_cursors(identities)

        cursor = predicate.get(PagginationArguments.NEXT_CURSOR)
        if cursor is None:
            cursor = predicate.get(PagginationArguments.PREV_CURSOR)
        
        if next_cursor is not None:
            next_cursor = str(next_cursor)

        if prev_cursor is not None:
            prev_cursor = str(prev_cursor) if cursor is not None else None

        return Response(200, data=BatchResponse(next_cursor, prev_cursor, identities))


class FetchIdentityAuthorizationFilter:

    def __init__(self, perm_repo: IRolePermissionRepository) -> None:
        self._perm_repo: IRolePermissionRepository = perm_repo


    def authorize_operation(self, ctx: DemandContext, next: Callable[[], Response]) -> Response:

        usr_claims = ctx.current_usr_claims
        if usr_claims is None:
            raise ForbiddenIssue('Please authorize.')

        identity_id = ctx.arguments.get(IdentityArguments.IDENTITY_ID, 0)
        mode = AccessMode.own if identity_id == usr_claims.identity_id else AccessMode.nonown
        permission = self._perm_repo.fetch_lightest_by_name(usr_claims.role_id, Resources.IDENTITIES, mode)

        if not permission.allow_read:
            raise ForbiddenIssue('You do not have access to read identities')

        return next()


class FetchIdentityHandler(Handler):

    def __init__(self, identity_repo: IIdentityRepository) -> None:
        self._identity_repo: IIdentityRepository = identity_repo

    def execute(self, ctx: DemandContext) -> Response:

        identity_id = ctx.arguments.get(IdentityArguments.IDENTITY_ID, 0)
        identity = self._identity_repo.fetch_by_id(identity_id)
        if identity is None:
            resp = Response(404, data=identity)
            resp.add_message('Identity is not located', MessageType.error)
            return resp

        return Response(200, data=identity)


def pipeline_fetch_identity(perm_repo: IRolePermissionRepository) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(verify_identity_argument_filter)
    pipeline.use(FetchIdentityAuthorizationFilter(perm_repo).authorize_operation)
    return pipeline
