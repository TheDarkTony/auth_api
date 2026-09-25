from core_contracts.handler import DemandContext, Response, PipelineProtocol, Handler
from core.pizza.orders import OrderSubject, Arguments


class DemandHandlerWrapper:
    def __init__(self, pipeline: PipelineProtocol, handler: Handler) -> None:
        self._pipeline = pipeline
        self._handler = handler


class CreateOrderWrapper(DemandHandlerWrapper):

    def create(self, ctx: DemandContext, demand: OrderSubject) -> Response:
        ctx.demand = demand
        return self._pipeline.execute(ctx, self._handler)


class ListOrdersWrapper(DemandHandlerWrapper):

    def list(self, ctx: DemandContext) -> Response:
        return self._pipeline.execute(ctx, self._handler)


class DeleteOrdersWrapper(DemandHandlerWrapper):

    def delete(self, ctx: DemandContext, id:int) -> Response:
        ctx.arguments[Arguments.ORDER_ID.value] = id
        return self._pipeline.execute(ctx, self._handler)


class ReadOrdersWrapper(DemandHandlerWrapper):

    def read(self, ctx: DemandContext, id:int) -> Response:
        ctx.arguments[Arguments.ORDER_ID.value] = id
        return self._pipeline.execute(ctx, self._handler)


class EditOrdersWrapper(DemandHandlerWrapper):

    def edit(self, ctx: DemandContext, id:int, demand: OrderSubject) -> Response:
        ctx.demand = demand
        ctx.arguments[Arguments.ORDER_ID.value] = id
        return self._pipeline.execute(ctx, self._handler)
