from typing import cast
from rest_framework.views import APIView

from dependency_injector.wiring import Provide, inject

from src.api_core.container import AppContainer
from src.api_core.response import Offer
from src.api_core.serializers import ResultSerializer

from core_contracts.handler import Response as AppResponse
from src.pizza.wrappers import CreateOrderWrapper, EditOrdersWrapper, ReadOrdersWrapper, DeleteOrdersWrapper, ListOrdersWrapper

from src.pizza.serializers import OrderSubjectSerializer, OrderResultSerializer, OrdersResultSerializer


class ListOrdersView(APIView):

    @inject
    def get(self, request, offerer: ListOrdersWrapper = Provide[AppContainer.list_orders_wrapper]):
        res = offerer.list(request.demand_context)
        ser = OrdersResultSerializer(res, context={'request': request, 'viewname': 'order-details'})
        return Offer(ser, res).offer

    @inject
    def post(self, request, offerer: CreateOrderWrapper = Provide[AppContainer.create_order_wrapper]):
        s = cast(OrderSubjectSerializer, OrderSubjectSerializer(data=request.data))
        d = s.demand
        res = offerer.create(request.demand_context, d)
        return Offer(ResultSerializer(res), res).offer

    def get_serializer(self, *args, **kwargs):
        if self.request.method == 'POST':
            return OrderSubjectSerializer()


class DetailOrderView(APIView):

    @inject
    def get(self, request, id, offerer: ReadOrdersWrapper = Provide[AppContainer.read_order_wrapper]):
        res = offerer.read(request.demand_context, id)
        ser = OrderResultSerializer(res, context={'request': request, 'viewname': 'order-details'})
        return Offer(ser, res).offer

    @inject
    def put(self, request, id, offerer: EditOrdersWrapper = Provide[AppContainer.edit_order_wrapper]):
        s = cast(OrderSubjectSerializer, OrderSubjectSerializer(data=request.data))
        res = offerer.edit(request.demand_context, id, s.demand)
        return Offer(ResultSerializer(res), res).offer

    @inject
    def delete(self, request, id, offerer: DeleteOrdersWrapper = Provide[AppContainer.delete_order_wrapper]):
        res = offerer.delete(request.demand_context, id)
        return Offer(ResultSerializer(res), res).offer

    def get_serializer(self, *args, **kwargs):
        if self.request.method == 'PUT':
            inst:AppResponse|None = kwargs.get('instance')
            if inst is None:
                return OrderSubjectSerializer()
            
            return OrderSubjectSerializer(inst.data)

