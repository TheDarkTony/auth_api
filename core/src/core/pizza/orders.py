import threading
from typing import Callable
from enum import Enum
from dataclasses import dataclass
from core_contracts.permission.repositories import IRolePermissionRepository, RolePermission
from core_contracts.handler import Response, DemandContext
from core_contracts.issues import ValidationIssue, ForbiddenIssue, NotFoundEntryIssue
from core_contracts.base import AccessMode, AccessArguments
from core.handler import Handler, Pipeline, get_default_pipeline, MessageType


class Arguments(Enum):
    ORDER_ID = 'order_id'


@dataclass
class OrderSubject:
    subject:str
    cost:float
    customer_user_id: int|None
    cook_user_id: int|None
    waiter_user_id: int|None
    status: str|None


@dataclass
class Order(OrderSubject):
    id:int


_ORDERS_LOCK = threading.Lock()

ORDERS: dict[int, Order] = {}

def _get_order(id:int) -> Order|None:
    with _ORDERS_LOCK:
        return ORDERS.get(id)

def _delete_order(id:int):
    with _ORDERS_LOCK:
        ORDERS.__delitem__(id)

def _add_order(o: OrderSubject):
    with _ORDERS_LOCK:
        size = len(ORDERS)
        ORDERS[size+1] = Order(
            o.subject,
            o.cost,
            o.customer_user_id,
            o.cook_user_id,
            o.waiter_user_id,
            status='created',
            id=size+1
        )

def _edit_order(id: int, o: OrderSubject):
    with _ORDERS_LOCK:
        order = ORDERS[id]
        order.cost = o.cost
        order.subject = o.subject
        order.cook_user_id = o.cook_user_id
        order.waiter_user_id = o.waiter_user_id


def validate_order_demand_filter(ctx: DemandContext, next: Callable[[], Response]) -> Response:

    demand = ctx.get_demand(OrderSubject)
    if demand is None:
        raise ValidationIssue('Order is required')

    if demand.subject is None or len(demand.subject) == 0:
        raise ValidationIssue('Subject of order is required')

    if demand.customer_user_id is None or demand.customer_user_id <= 0:
        raise ValidationIssue('Customer is required')

    return next()


def validate_arguments_filter(ctx: DemandContext, next: Callable[[], Response]) -> Response:

    order_id = ctx.arguments.get(Arguments.ORDER_ID.value, 0)
    if order_id <= 0:
        raise ValidationIssue('id of order is required')

    return next()


class CreateOrderAuthorizationFilter:

    def __init__(self, perm_repo: IRolePermissionRepository) -> None:
        self._perm_repo: IRolePermissionRepository = perm_repo

    def authorize_operation(self, ctx: DemandContext, next: Callable[[], Response]) -> Response:

        claims = ctx.current_usr_claims
        if claims is None:
            raise ForbiddenIssue('Please authorize.')

        demand = ctx.get_demand(OrderSubject)

        mode = AccessMode.nonown
        if claims.user_id == demand.cook_user_id:
            mode = AccessMode.own
        elif claims.user_id == demand.waiter_user_id:
            mode = AccessMode.own
        elif claims.user_id == demand.customer_user_id:
            mode = AccessMode.own

        perms = self._perm_repo.list_by_resource_name(claims.role_id, 'orders')

        for perm, w in perms:
            if perm.mode is None or perm.mode == mode:
                self.allow_action(perm)
                break

        return next()

    def allow_action(self, perm: RolePermission):
        if not perm.allow_create:
            raise ForbiddenIssue('You do not have access to create order')


class _OrderAuthorizationFilter:

    def __init__(self, perm_repo: IRolePermissionRepository) -> None:
        self._perm_repo: IRolePermissionRepository = perm_repo

    def authorize_operation(self, ctx: DemandContext, next: Callable[[], Response]) -> Response:

        claims = ctx.current_usr_claims
        if claims is None:
            raise ForbiddenIssue('Please authorize.')

        order_id = ctx.arguments.get(Arguments.ORDER_ID.value, 0)
        order = _get_order(order_id)
        if order is None:
            raise NotFoundEntryIssue('Order is not located')

        mode = AccessMode.nonown
        if claims.user_id == order.cook_user_id:
            mode = AccessMode.own
        elif claims.user_id == order.waiter_user_id:
            mode = AccessMode.own
        elif claims.user_id == order.customer_user_id:
            mode = AccessMode.own

        perms = self._perm_repo.list_by_resource_name(claims.role_id, 'orders')

        for perm, w in perms:
            if perm.mode is None or perm.mode == mode:
                self.allow_action(perm)
                break

        return next()

    def allow_action(self, perm: RolePermission):
        raise NotImplementedError

        

class EditOrderAuthorizationFilter(_OrderAuthorizationFilter):

    def allow_action(self, perm: RolePermission):
        if not perm.allow_edit:
            raise ForbiddenIssue('You do not have access to edit order')

class DeleteOrderAuthorizationFilter(_OrderAuthorizationFilter):

    def allow_action(self, perm: RolePermission):
        if not perm.allow_delete:
            raise ForbiddenIssue('You do not have access to delete order')

class ReadOrderAuthorizationFilter(_OrderAuthorizationFilter):

    def allow_action(self, perm: RolePermission):
        if not perm.allow_read:
            raise ForbiddenIssue('You do not have access to read order')


class ListOrderAutorizationFilter:

    def __init__(self, perm_repo: IRolePermissionRepository) -> None:
        self._perm_repo: IRolePermissionRepository = perm_repo
    
    def authorize_operation(self, ctx: DemandContext, next: Callable[[], Response]) -> Response:

        claims = ctx.current_usr_claims
        if claims is None:
            raise ForbiddenIssue('Please authorize.')

        permissions = self._perm_repo.list_by_resource_name(claims.role_id, 'orders')
        
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
            raise ForbiddenIssue(f'You do not have access to list orders')

        if allow_own and allow_nonown:
            ctx.arguments[AccessArguments.MODE] = None
        elif allow_own and not allow_nonown:
            ctx.arguments[AccessArguments.MODE] = AccessMode.own
        elif not allow_own and allow_nonown:
            ctx.arguments[AccessArguments.MODE] = AccessMode.nonown
        else:
            raise ForbiddenIssue(f'You do not have access to list orders')

        return next()


class CreateOrderHandler(Handler):

    def execute(self, ctx: DemandContext) -> Response:
        demand = ctx.get_demand(OrderSubject)
        _add_order(demand)
        return Response(200)


class ReadOrderHandler(Handler):

    def execute(self, ctx: DemandContext) -> Response:

        order_id = ctx.arguments.get(Arguments.ORDER_ID.value, 0)
        order = _get_order(order_id)
        if order is None:
            r = Response(404)
            r.add_message('Order is not located', MessageType.error)
            return r

        return Response(200, data=order)

class EditOrderHandler(Handler):

    def execute(self, ctx: DemandContext) -> Response:

        order_id = ctx.arguments.get(Arguments.ORDER_ID.value, 0)
        demand = ctx.get_demand(OrderSubject)
        order = _get_order(order_id)
        if order is None:
            r = Response(404)
            r.add_message('Order is not located', MessageType.error)
            return r

        _edit_order(order_id, demand)
        return Response(200)


class DeleteOrderHandler(Handler):

    def execute(self, ctx: DemandContext) -> Response:

        order_id = ctx.arguments.get(Arguments.ORDER_ID.value, 0)
        order = _get_order(order_id)
        if order is None:
            r = Response(404)
            r.add_message('Order is not located', MessageType.error)
            return r

        _delete_order(order_id)
        return Response(200)


class ListOrdersHandler(Handler):

    def execute(self, ctx: DemandContext) -> Response:

        mode: AccessMode|None = ctx.arguments.get(AccessArguments.MODE)
        claims = ctx.current_usr_claims
        if claims is None:
            raise ForbiddenIssue('Please authorize')

        def include(o: Order) -> bool:
            if mode is None:
                return True

            if mode == AccessMode.own:
                return (claims.user_id == o.customer_user_id 
                        or claims.user_id == o.waiter_user_id
                        or claims.user_id == o.cook_user_id)
            elif mode == AccessMode.nonown:
                return not (claims.user_id == o.customer_user_id 
                        or claims.user_id == o.waiter_user_id
                        or claims.user_id == o.cook_user_id)

            return False

        orders = [item for id, item in ORDERS.items() if include(item)]

        return Response(200, data=orders)


def create_order_pipeline(perm_repo: IRolePermissionRepository) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(validate_order_demand_filter)
    pipeline.use(CreateOrderAuthorizationFilter(perm_repo).authorize_operation)
    return pipeline

def edit_order_pipeline(perm_repo: IRolePermissionRepository) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(validate_arguments_filter)
    pipeline.use(validate_order_demand_filter)
    pipeline.use(EditOrderAuthorizationFilter(perm_repo).authorize_operation)
    return pipeline

def delete_order_pipeline(perm_repo: IRolePermissionRepository) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(validate_arguments_filter)
    pipeline.use(DeleteOrderAuthorizationFilter(perm_repo).authorize_operation)
    return pipeline

def read_order_pipeline(perm_repo: IRolePermissionRepository) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(validate_arguments_filter)
    pipeline.use(ReadOrderAuthorizationFilter(perm_repo).authorize_operation)
    return pipeline

def list_order_pipeline(perm_repo: IRolePermissionRepository) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(ListOrderAutorizationFilter(perm_repo).authorize_operation)
    return pipeline
    