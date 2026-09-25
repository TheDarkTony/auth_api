from typing import cast

from rest_framework.views import APIView
from dependency_injector.wiring import Provide, Closing, inject

from src.api_core.container import AppContainer
from src.api_core.response import Offer

from core_contracts.handler import Response as AppResponse
from src.permission.wrappers import (
    ListRolesWrapper,
    ListAppResourcesWrapper,
    ListPermissionsWrapper,
    CreatePermissionWrapper,
    EditPermissionWrapper,
    DeletePermissionWrapper,
    FetchPermissionWrapper)

from .serializers import (
    ResultSerializer,
    RolesResultSerializer,
    AppResourcesResultSerializer,
    PermissionsResultSerializer,
    NewPermissionSerializer,
    PermissionResultSerializer,
    PermissionSubjectSerializer)


class ListRolesView(APIView):

    @inject
    def get(self, request
        , offerrer: ListRolesWrapper = Closing[Provide[AppContainer.list_roles_wrapper]]
    ):
        result = offerrer.list_roles(request.demand_context)
        serializer = RolesResultSerializer(result, context={'request': request})
        return Offer(serializer, result).offer


class ListAppResourcesView(APIView):

    @inject
    def get(self, request
        , offerrer: ListAppResourcesWrapper = Closing[Provide[AppContainer.list_app_resources_wrapper]]
    ):
        result = offerrer.list_app_resource(request.demand_context)
        serializer = AppResourcesResultSerializer(result, context={'request': request})
        return Offer(serializer, result).offer


class ListPermissionsView(APIView):

    @inject
    def get(self, request
        , offerrer: ListPermissionsWrapper = Closing[Provide[AppContainer.list_permissions_wrapper]]
    ):

        query = request.query_params
        role_id = query.get('role_id')
        resource_id = query.get('resource_id')
        
        result = offerrer.list_permissions(request.demand_context, role_id, resource_id)
        serializer = PermissionsResultSerializer(result, context={'request': request, 'viewname': 'permission-detail'})
        return Offer(serializer, result).offer

    @inject
    def post(self, request
        , offerrer: CreatePermissionWrapper = Closing[Provide[AppContainer.create_permission_wrapper]]
    ):
        query = request.query_params
        role_id = query.get('role_id')
        resource_id = query.get('resource_id')

        demand = cast(NewPermissionSerializer, NewPermissionSerializer(data=request.data)).demand

        result = offerrer.create_permission(request.demand_context, role_id, resource_id, demand)
        serializer = PermissionResultSerializer(result,context={'request': request, 'viewname': 'permission-detail'})
        return Offer(serializer, result).offer

    def get_serializer(self, *args, **kwargs):
        if self.request.method == 'POST':
            return NewPermissionSerializer()


class DetailPermissionView(APIView):

    @inject
    def get(self, request
        , id
        , offerrer: FetchPermissionWrapper = Closing[Provide[AppContainer.fetch_permission_wrapper]]
    ):
        query = request.query_params
        role_id = query.get('role_id')
        resource_id = query.get('resource_id')

        result = offerrer.fetch_permission(request.demand_context, id)
        serializer = PermissionResultSerializer(result, context={'request': request, 'viewname': 'permission-detail'})
        return Offer(serializer, result).offer
        
    @inject
    def put(self, request
        , id
        , offerrer: EditPermissionWrapper = Closing[Provide[AppContainer.edit_permission_wrapper]]
    ):
        query = request.query_params
        role_id = query.get('role_id')
        resource_id = query.get('resource_id')

        demand = cast(PermissionSubjectSerializer, PermissionSubjectSerializer(data=request.data)).demand

        result = offerrer.edit_permission(request.demand_context, role_id, resource_id, id, demand)
        serializer = PermissionResultSerializer(result,context={'request': request, 'viewname': 'permission-detail'})
        return Offer(serializer, result).offer

    @inject
    def delete(self, request
        , id
        , offerrer: DeletePermissionWrapper = Closing[Provide[AppContainer.delete_permission_wrapper]]
    ):
        query = request.query_params
        role_id = query.get('role_id')
        resource_id = query.get('resource_id')

        result = offerrer.delete_permission(request.demand_context, id)
        serializer = ResultSerializer(result, context={'request': request})
        return Offer(serializer, result).offer

    def get_serializer(self, *args, **kwargs):
        if self.request.method == 'PUT':
            inst:AppResponse|None = kwargs.get('instance')
            if inst is None:
                return PermissionSubjectSerializer()
            
            return PermissionSubjectSerializer(inst.data)
