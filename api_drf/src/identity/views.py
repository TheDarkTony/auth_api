from typing import cast

from rest_framework.decorators import api_view
from rest_framework.views import APIView
from dependency_injector.wiring import Provide, Closing, inject

from core_contracts.handler import Response as AppResponse
from src.identity.wrappers import (ListIdentitiesWrapper
            , FetchIdentityWrapper
            , EditIdentityDemographicsWrapper
            , FetchProfileWrapper
            , ListUsersWrapper
            , FetchUserWrapper
            , DeleteUserWrapper
            , EditUserWrapper
            , ChangePwdWrapper
            )

from src.api_core.container import AppContainer
from src.api_core.response import Offer

from .serializers import (IdentityResultSerializer
            , IdentitiesResultSerializer
            , IdentityDemographicsSerializer
            , ProfileResultSerializer
            , UsersResultSerializer
            , UserResultSerializer
            , ResultSerializer
            , EditUserSerializer
            , ChangeUserPwdSerializer)


# Create your views here.
class ListIdentitiesView(APIView):

    @inject
    def get(self, request
        , offerer: ListIdentitiesWrapper = Closing[Provide[AppContainer.list_identities_wrappers]]
    ):
        query = request.query_params
        cursor = query.get('cursor')
        direction = query.get('direction')

        next_cursor = prev_cursor = None
        if cursor is not None:
            if direction == 'next':
                next_cursor = cursor
            elif direction == 'prev':
                prev_cursor = cursor

        result = offerer.list_identities(
            request.demand_context
            , next_cursor=next_cursor
            , prev_cursor=prev_cursor
        )
        serializer = IdentitiesResultSerializer(result, context={'request': request, 'viewname': 'identity-details', 'list_viewname': 'identity-list'})
        return Offer(serializer, result).offer


class DetailIdentityView(APIView):

    @inject
    def get(self, request
        , id
        , offerer: FetchIdentityWrapper = Closing[Provide[AppContainer.fetch_identity_wrappers]]
    ):
        result = offerer.fetch_identity(request.demand_context, id)
        return Offer(IdentityResultSerializer(result, context={'request': request, 'viewname':'identity-details'}), result).offer

    @inject
    def put(self, request
        , id
        , offerer: EditIdentityDemographicsWrapper = Closing[Provide[AppContainer.edit_demographics_wrapper]]
    ):
        s = cast(IdentityDemographicsSerializer, IdentityDemographicsSerializer(data=request.data))
        result = offerer.edit_demographics(request.demand_context, id, demand=s.demand)
        return Offer(IdentityResultSerializer(result, context={'request': request, 'viewname':'identity-details'}), result).offer

    def get_serializer(self, *args, **kwargs):
        if self.request.method == 'PUT':
            inst:AppResponse|None = kwargs.get('instance')
            if inst is None:
                return IdentityDemographicsSerializer()
            
            return IdentityDemographicsSerializer(inst.data)


class DetailProfileView(APIView):

    @inject
    def get(self, request
        , offerer: FetchProfileWrapper = Closing[Provide[AppContainer.fetch_profile_wrapper]]
    ):
        result = offerer.fetch_profile(request.demand_context)
        return Offer(ProfileResultSerializer(result,  context={
            'request': request, 
            'identity_vn': 'identity-details',
            'user_vn': 'user-details'
        }), result).offer

    @inject
    def put(self, request, offerer: ChangePwdWrapper = Closing[Provide[AppContainer.change_user_pwd]]):
        demand = cast(ChangeUserPwdSerializer, ChangeUserPwdSerializer(data=request.data)).demand
        id = request.claims.user_id
        result = offerer.change_pwd(request.demand_context, id, demand)
        return Offer(ResultSerializer(result, context={'request': request, 'viewname': None}), result).offer

    def get_serializer(self, *args, **kwargs):
        if self.request.method == 'PUT':
            return ChangeUserPwdSerializer()


class ListUsersView(APIView):

    @inject
    def get(self, request
        , offerer: ListUsersWrapper = Closing[Provide[AppContainer.list_users_wrapper]]
    ):
        query = request.query_params
        cursor = query.get('cursor')
        direction = query.get('direction')

        next_cursor = prev_cursor = None
        if cursor is not None:
            if direction == 'next':
                next_cursor = cursor
            elif direction == 'prev':
                prev_cursor = cursor
        
        result = offerer.list_users(request.demand_context, next_cursor=next_cursor, prev_cursor=prev_cursor)

        return Offer(UsersResultSerializer(result, context={'request': request, 'viewname': 'user-details', 'list_viewname': 'user-list'}), result).offer


class DetailUserView(APIView):

    @inject
    def get(self, request
        , id
        , offerer: FetchUserWrapper = Closing[Provide[AppContainer.fetch_user_wrapper]]
    ):
        result = offerer.fetch_user(request.demand_context, id)
        return Offer(UserResultSerializer(result, context={
            'request': request,
            'viewname': 'user-details'
        }), result).offer

    @inject
    def put(self, request
        , id
        , offerer: EditUserWrapper = Closing[Provide[AppContainer.edit_user_wrapper]]
    ):
        demand = cast(EditUserSerializer, EditUserSerializer(data=request.data)).demand
        result = offerer.edit_user(request.demand_context, id, demand)
        return Offer(UserResultSerializer(result, context={
            'request': request, 
            'viewname': 'user-details'
        }), result).offer
    
    @inject
    def delete(self, request
        , id
        , offerer: DeleteUserWrapper = Closing[Provide[AppContainer.delete_user_wrapper]]
    ):
        result = offerer.delete_user(request.demand_context, id)
        return Offer(ResultSerializer(result, context={'request': request, 'viewname': 'user-details'}), result).offer


    def get_serializer(self, *args, **kwargs):
        if self.request.method == 'PUT':
            inst:AppResponse|None = kwargs.get('instance')
            if inst is None:
                return EditUserSerializer()
            
            return EditUserSerializer(inst.data)


@api_view(['PUT'])
@inject
def change_user_pwd(request, id, offerer: ChangePwdWrapper = Closing[Provide[AppContainer.change_user_pwd]]):
    demand = cast(ChangeUserPwdSerializer, ChangeUserPwdSerializer(data=request.data)).demand
    result = offerer.change_pwd(request.demand_context, id, demand)
    return Offer(ResultSerializer(result, context={'request': request, 'viewname': None}), result).offer
