from rest_framework import serializers
from rest_framework.reverse import reverse
from src.api_core.serializers import ResultSerializer, append_query

from core.permission.demands import NewPermissionDemand, PermissionDemand



class AppResourceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()


class RoleSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()


class PermissionSubjectSerializer(serializers.Serializer):
    mode = serializers.CharField(allow_null=True)
    allow_enumerate = serializers.BooleanField()
    allow_read = serializers.BooleanField()
    allow_create = serializers.BooleanField()
    allow_edit = serializers.BooleanField()
    allow_delete = serializers.BooleanField()

    def create(self, validated_data):
            return PermissionDemand(**validated_data)
    
    @property
    def demand(self) -> PermissionDemand:
        self.is_valid()
        return self.create(self.validated_data)


class NewPermissionSerializer(PermissionSubjectSerializer):
    role_id = serializers.IntegerField(allow_null=True)
    resource_id = serializers.IntegerField(allow_null=True)

    def create(self, validated_data):
        return NewPermissionDemand(**validated_data)

    @property
    def demand(self) -> NewPermissionDemand:
        self.is_valid()
        return self.create(self.validated_data)


class PermissionSerializer(PermissionSubjectSerializer):
    id = serializers.BigIntegerField()
    url = serializers.CharField(allow_null=True)

    role_id = serializers.IntegerField(allow_null=True)
    resource_id = serializers.IntegerField(allow_null=True)

    weight = serializers.IntegerField()
    name = serializers.CharField(allow_null=True)

    def to_representation(self, instance):
        repr = super().to_representation(instance)

        rqst = self.context.get('request')
        viewname = self.context.get('viewname')
        if rqst is not None and viewname is not None:
            url = reverse(viewname, request=rqst, kwargs={'id':instance.id})

            role_id = rqst.query_params.get('role_id')
            resource_id = rqst.query_params.get('resource_id')
            query = {}
            if role_id is not None:
                query['role_id'] = role_id
            if resource_id is not None:
                query['resource_id'] = resource_id

            repr['url'] = append_query(url, query)

        return repr


class RolesResultSerializer(ResultSerializer):
    body = RoleSerializer(source='data', many=True)

class AppResourcesResultSerializer(ResultSerializer):
    body = AppResourceSerializer(source='data', many=True)

class PermissionsResultSerializer(ResultSerializer):
    body = PermissionSerializer(source='data', many=True)

class PermissionResultSerializer(ResultSerializer):
    body = PermissionSerializer(source='data')