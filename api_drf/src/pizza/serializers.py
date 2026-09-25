from rest_framework import serializers
from rest_framework.reverse import reverse

from src.api_core.serializers import ResultSerializer
from core.pizza.orders import OrderSubject


class OrderSubjectSerializer(serializers.Serializer):

    subject = serializers.CharField(allow_null=True)
    cost = serializers.DecimalField(max_digits=5, decimal_places=2)
    customer_user_id = serializers.IntegerField(required=False, default=0)
    cook_user_id = serializers.IntegerField(required=False, default=0)
    waiter_user_id = serializers.IntegerField(required=False, default=0)
    status = serializers.CharField(allow_null=True)

    def create(self, validated_data) -> OrderSubject:
        return OrderSubject(**validated_data)

    @property
    def demand(self) -> OrderSubject:
        self.is_valid()
        return self.create(self.validated_data)


class OrderSerializer(OrderSubjectSerializer):
    id = serializers.IntegerField()

    def to_representation(self, instance):
        repr = super().to_representation(instance)

        order_vn = self.context.get('viewname')
        rqst = self.context.get('request')

        if order_vn is not None and rqst is not None:
            repr['url'] = reverse(order_vn, kwargs={'id':instance.id}, request=rqst)

        return repr


class OrderResultSerializer(ResultSerializer):
    body = OrderSerializer(source='data')


class OrdersResultSerializer(ResultSerializer):
    items = OrderSerializer(source='data',many=True)