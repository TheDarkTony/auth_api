from core_contracts.base import IdentityArguments, PagginationArguments
from core_contracts.handler import DemandContext, Response, PipelineProtocol, Handler
from core_contracts.identity.models import IdentityFields, UserFields

from core.identity.demands import EditDemographicsDemand, EditUserDemand, ChangePwdDemand


class DemandHandlerWrapper:
    def __init__(self, pipeline: PipelineProtocol, handler: Handler) -> None:
            self._pipeline = pipeline
            self._handler = handler


class ListIdentitiesWrapper(DemandHandlerWrapper):

    def list_identities(self
        , ctx: DemandContext
        , next_cursor: str|None=None
        , prev_cursor: str|None=None
        , batch_size: int|None=None
        , fname:str|None = None
        , lname: str|None = None
        , email: str|None = None) -> Response:
        
        if next_cursor is not None:
            ctx.arguments[PagginationArguments.NEXT_CURSOR] = int(next_cursor)

        if prev_cursor is not None:
            ctx.arguments[PagginationArguments.PREV_CURSOR] = int(prev_cursor)

        if batch_size is not None:
            ctx.arguments[PagginationArguments.BATCH_SIZE] = batch_size

        if fname is not None:
            ctx.arguments[IdentityFields.FNAME] = fname

        if lname is not None:
            ctx.arguments[IdentityFields.LNAME] = lname

        if email is not None:
            ctx.arguments[IdentityFields.EMAIL] = email

        return self._pipeline.execute(ctx, self._handler)


class FetchIdentityWrapper(DemandHandlerWrapper):

    def fetch_identity(self, ctx: DemandContext,  identity_id: int) -> Response:

        ctx.arguments[IdentityArguments.IDENTITY_ID] = identity_id
        return self._pipeline.execute(ctx, self._handler)


class EditIdentityDemographicsWrapper(DemandHandlerWrapper):

    def edit_demographics(self, ctx: DemandContext,  identity_id:int, demand: EditDemographicsDemand) -> Response: 

        ctx.arguments[IdentityArguments.IDENTITY_ID] = identity_id
        ctx.demand = demand

        return self._pipeline.execute(ctx, self._handler)


class FetchProfileWrapper(DemandHandlerWrapper):

    def fetch_profile(self, ctx: DemandContext ) -> Response:
        return self._pipeline.execute(ctx, self._handler)


class ListUsersWrapper(DemandHandlerWrapper):

    def list_users(self, ctx: DemandContext
        , next_cursor: str|None=None
        , prev_cursor: str|None=None
        , batch_size: int|None=None
        , username:str|None=None
    ) -> Response:

        if next_cursor is not None:
            ctx.arguments[PagginationArguments.NEXT_CURSOR] = int(next_cursor)

        if prev_cursor is not None:
            ctx.arguments[PagginationArguments.PREV_CURSOR] = int(prev_cursor)

        if batch_size is not None:
            ctx.arguments[PagginationArguments.BATCH_SIZE] = batch_size

        if username is not None:
            ctx.arguments[UserFields.USERNAME] = username

        return self._pipeline.execute(ctx, self._handler)


class FetchUserWrapper(DemandHandlerWrapper):

    def fetch_user(self, ctx:DemandContext, usr_id: int) -> Response:
        ctx.arguments[IdentityArguments.USER_ID] = usr_id
        return self._pipeline.execute(ctx, self._handler)

class DeleteUserWrapper(DemandHandlerWrapper):

    def delete_user(self, ctx:DemandContext, usr_id: int) -> Response:
        ctx.arguments[IdentityArguments.USER_ID] = usr_id
        return self._pipeline.execute(ctx, self._handler)


class EditUserWrapper(DemandHandlerWrapper):

    def edit_user(self, ctx: DemandContext, usr_id:int, demand: EditUserDemand) -> Response:
        ctx.arguments[IdentityArguments.USER_ID] = usr_id
        ctx.demand = demand
        return self._pipeline.execute(ctx, self._handler)


class ChangePwdWrapper(DemandHandlerWrapper):

    def change_pwd(self, ctx: DemandContext, usr_id: int, demand: ChangePwdDemand) -> Response:
        ctx.arguments[IdentityArguments.USER_ID] = usr_id
        ctx.demand = demand
        return self._pipeline.execute(ctx, self._handler)
