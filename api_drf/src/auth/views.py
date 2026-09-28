from typing import cast
from datetime import datetime, timezone

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.settings import settings
from rest_framework import status

from dependency_injector.wiring import Provide, Closing, inject

from core_contracts.base import utcnow
from core_contracts.handler import MessageType, Claims, Response as AppResponse
from src.auth.wrappers import SignUpWrapper, SignUp2FAWrapper, SignInWrapper, SignIn2FAWrapper

from src.api_core.response import Offer
from src.api_core.decorators import attach_serializer, allow_anonymous
from src.api_core.utils import get_auth_token, AccessTokenBlackListValkey
from src.api_core.container import AppContainer

from .serializers import (
    SignUpSerializer,
    SingUpResultSerializer,
    Sign2FAFeedbackSerializer,
    SingUp2FAFeedbackResultSerializer,
    SignIn200ResultSerializer,
    SignIn202ResultSerializer,
    SignInSerializer,
    ResultSerializer)


def _dummy_browsable_api(msg):
    if settings.DEBUG:
        return Response(msg)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST', 'GET'])
@inject
def signout(request, token_blk_list: AccessTokenBlackListValkey = Provide[AppContainer.access_token_black_list_repo]):
    if request.method == 'GET':
        return _dummy_browsable_api('Dummy brawsable page')

    token = get_auth_token(request)
    serializer = ResultSerializer(context={'request': request, 'viewname': None})

    if token is None:
        r = AppResponse(401)
        r.add_message('Please authorized', MessageType.error)
        return Offer(serializer, r).offer

    claims: Claims = getattr(request, 'claims')

    now = utcnow()
    expired_at = datetime.fromtimestamp(claims.exp, tz=timezone.utc) #type: ignore
    if expired_at > now:
        ttl = expired_at - now
        token_blk_list.push_to_black_list(token, ttl.seconds)

    return Offer(serializer, AppResponse(202)).offer


@attach_serializer(SignUpSerializer)
@allow_anonymous()
@api_view(['POST', 'GET'])
@inject
def signup(request
    , offerer: SignUpWrapper = Closing[Provide[AppContainer.sign_up_wrapper]]
):
    if request.method == 'GET':
        return _dummy_browsable_api('Please enter your credentials')
    
    demand = cast(SignUpSerializer, SignUpSerializer(data=request.data)).demand
    result = offerer.sign_up(request.demand_context, demand)
    serializer = SingUpResultSerializer(result, context={'request': request, 'viewname': None})
    return Offer(serializer, result).offer


@attach_serializer(Sign2FAFeedbackSerializer)
@allow_anonymous()
@api_view(['POST', 'GET'])
@inject
def signup_2fa(request
    , offerer: SignUp2FAWrapper = Closing[Provide[AppContainer.signup_2fa_wrapper]]
):
    if request.method == 'GET':
        return _dummy_browsable_api('Please enter 2FA data')
    
    demand = cast(Sign2FAFeedbackSerializer, Sign2FAFeedbackSerializer(data=request.data)).demand
    result = offerer.verify_2fa_signup(request.demand_context, demand)
    serializer = SingUp2FAFeedbackResultSerializer(result, context={'request': request, 'viewname': None})
    return Offer(serializer, result).offer


@attach_serializer(SignInSerializer)
@allow_anonymous()
@api_view(['POST', 'GET'])
@inject
def signin(request
    , offerer: SignInWrapper = Closing[Provide[AppContainer.sign_in_wrapper]]
):
    if request.method == 'GET':
        return _dummy_browsable_api('Please enter your credentials')
    
    demand = cast(SignInSerializer, SignInSerializer(data=request.data)).demand
    result = offerer.sign_in(request.demand_context, demand)

    if result.status == 200:
        serializer = SignIn200ResultSerializer(result, context={'request': request, 'viewname': None})
    elif result.status == 202:
        serializer = SignIn202ResultSerializer(result, context={'request': request, 'viewname': None})
    else:
        serializer = ResultSerializer(result, context={'request': request, 'viewname': None})

    return Offer(serializer, result).offer

@attach_serializer(Sign2FAFeedbackSerializer)
@allow_anonymous()
@api_view(['POST', 'GET'])
@inject
def signin_2fa(request
    , offerer: SignIn2FAWrapper = Closing[Provide[AppContainer.signin_2fa_wrapper]]
):
    if request.method == 'GET':
        return _dummy_browsable_api('Please enter 2FA data')
    
    demand = cast(Sign2FAFeedbackSerializer, Sign2FAFeedbackSerializer(data=request.data)).demand
    result = offerer.verify_2fa_signin(request.demand_context, demand)
    serializer = SignIn200ResultSerializer(result, context={'request': request, 'viewname': None})
    return Offer(serializer, result).offer
