from abc import abstractmethod, ABCMeta
from typing import Callable, Any
import logging

from core_contracts.base import IdentityArguments, AccessMode, AccessArguments
from core_contracts.issues import ValidationIssue, ForbiddenIssue, ApplicationIssue, NotFoundEntryIssue
from core_contracts.handler import MessageType, Response, DemandContext, Claims, FilterCallable, Handler
from core_contracts.permission.repositories import IRolePermissionRepository, RolePermission


class Pipeline:
    def __init__(self) -> None:
        self._pipeline: list[FilterCallable] = []

    def use(self, handler: FilterCallable) -> None:
        """Adds a new middleware layer into the pipeline stack."""
        self._pipeline.append(handler)

    def execute(self, ctx: DemandContext, core_handler: Handler) -> Response:
        """Executes registered filters one by one before handler is triggered."""
        index = 0

        def dispatch_next() -> Any:
            nonlocal index
            if index < len(self._pipeline):
                current_handler = self._pipeline[index]
                index += 1
                return current_handler(ctx, dispatch_next)
            else:
                return core_handler.execute(ctx)

        return dispatch_next()

#common filters
LOGGER = logging.getLogger(__name__)

def error_logging_filter(ctx: DemandContext, next: Callable[[], Response]) -> Response:

    def _log_ctx():
        return {'demand_ctx': ctx, 'application':'pizza_app'}

    try:
        return next()
    except ValidationIssue as ex:
        LOGGER.warning(str(ex), exc_info=True, extra=_log_ctx()) #for testing
        res = Response(400)
        res.add_message(str(ex), MessageType.error)
        return res
    except NotFoundEntryIssue as ex:
        LOGGER.warning(str(ex), exc_info=True, extra=_log_ctx())
        res = Response(404)
        res.add_message(str(ex), MessageType.error)
        return res
    except ForbiddenIssue as ex:
        LOGGER.warning(str(ex), exc_info=True, extra=_log_ctx())
        res = Response(403)
        res.add_message(str(ex), MessageType.error)
        return res
    except (ApplicationIssue, Exception) as ex:
        LOGGER.error(str(ex), exc_info=True, extra=_log_ctx())
        res = Response(500)
        res.add_message('Something goes wrong. We are working on it', MessageType.error)
        return res


def get_default_pipeline() -> Pipeline:
    pipeline = Pipeline()
    pipeline.use(error_logging_filter)
    return pipeline


def get_mode_by_user(claims: Claims, ctx: DemandContext) -> AccessMode:
    usr_id = ctx.arguments.get(IdentityArguments.USER_ID, 0)
    return AccessMode.own if claims.user_id == usr_id else AccessMode.nonown


def get_mode_by_identity(claims: Claims, ctx: DemandContext) -> AccessMode:
    identity_id = ctx.arguments.get(IdentityArguments.IDENTITY_ID, 0)
    return AccessMode.own if claims.identity_id == identity_id else AccessMode.nonown


class SingleItemAuthorizationFilter(metaclass=ABCMeta):

    def __init__(self, perm_repo: IRolePermissionRepository) -> None:
        self._perm_repo: IRolePermissionRepository = perm_repo

    def authorize_operation(self, ctx: DemandContext, next: Callable[[], Response]) -> Response:

        usr_claims = ctx.current_usr_claims
        if usr_claims is None:
            raise ForbiddenIssue('Please authorize.')

        mode = self._get_mode_core(usr_claims, ctx)
        perm = self._perm_repo.fetch_lightest_by_name(usr_claims.role_id, self.resource, mode)

        self.authorize_core(perm)
        return next()

    @property
    @abstractmethod
    def resource(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def authorize_core(self, permission: RolePermission):
        raise NotImplementedError

    @abstractmethod
    def _get_mode_core(self, claims: Claims, ctx: DemandContext) -> AccessMode:
        raise NotImplementedError


class ListAuthorizationFilter(metaclass=ABCMeta):

    def __init__(self, perm_repo: IRolePermissionRepository) -> None:
        self._perm_repo: IRolePermissionRepository = perm_repo

    def authorize_operation(self, ctx: DemandContext, next: Callable[[], Response]) -> Response:
    
        claims = ctx.current_usr_claims
        if claims is None:
            raise ForbiddenIssue('Please authorize.')

        predicate = ctx.arguments
        predicate[AccessArguments.CURRENT_IDENTITY] = claims.identity_id
        predicate[AccessArguments.CURRENT_USR] = claims.user_id

        permissions = self._perm_repo.list_by_resource_name(claims.role_id, self.resource)

        allow_own: bool|None = None
        allow_nonown: bool|None = None
        for p, w in permissions:
            if p.mode is None:
                if allow_own is None:
                    allow_own = p.allow_enumerate
                if allow_nonown is None:
                    allow_nonown = p.allow_enumerate
            elif p.mode == AccessMode.own.value and allow_own is None:
                allow_own = p.allow_enumerate
            elif p.mode == AccessMode.nonown.value and allow_nonown is None:
                allow_nonown = p.allow_enumerate

            if allow_own is not None and allow_nonown is not None:
                break;

        if allow_own is None and allow_nonown is None:
            raise ForbiddenIssue(f'You do not have access to list {self.resource}')

        if allow_own and allow_nonown:
            predicate[AccessArguments.MODE] = None
        elif allow_own and not allow_nonown:
            predicate[AccessArguments.MODE] = AccessMode.own.value
        elif not allow_own and allow_nonown:
            predicate[AccessArguments.MODE] = AccessMode.nonown.value
        else:
            raise ForbiddenIssue(f'You do not have access to list {self.resource}')

        return next()

    @property
    @abstractmethod
    def resource(self) -> str:
        raise NotImplementedError
