import jwt
import logging
import uuid

from django.http import JsonResponse
from django.urls import resolve
from rest_framework.settings import settings
from rest_framework.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_405_METHOD_NOT_ALLOWED, HTTP_500_INTERNAL_SERVER_ERROR

from dependency_injector.wiring import Provide, inject

from core.auth.utils import AuthTokenUtil
from core_contracts.handler import MessageType, DemandContext, TRACE_ID

from src.api_core.utils import AccessTokenBlackListValkey, UserTempBlackListValkey, get_auth_token
from src.api_core.container import AppContainer


security = settings.SECURITY_AUTH

LOGGER = logging.getLogger(__name__)


AUTH_TOKEN_UTIL = AuthTokenUtil(
        secret_jwt_key=security.get('SECRET_JWT_KEY'),
        jwt_algorithm=security.get('JWT_ALGORITHM'),
        access_token_seconds_ttl=security.get('ACCESS_TOKEN_SECONDS_TTL'),
        refresh_token_seconds_ttl=security.get('REFRESH_TOKEN_SECONDS_TTL')
    )

def _json_response(msg:str, status:int):
    return JsonResponse({
        'state_code':None, 
        'messages': [
            {
                'text':msg,
                'type': MessageType.error.value
            }
        ]
    }, status=status)


class AuthorizationMiddleware:

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    @inject
    def __call__(self, request
        , token_blk_list: AccessTokenBlackListValkey = Provide[AppContainer.access_token_black_list_repo]
        , usr_temp_blk_list: UserTempBlackListValkey = Provide[AppContainer.user_temp_black_list_repo]
    ):

        allow_anonymous = False
        view = None
        try:
            path: str = request.path_info
            view = resolve(path).func
        except Exception as ex:
            TRACE_ID.set(uuid.uuid4().hex)
            LOGGER.warning('Path info is not resolved. Skiped handling, 405 status returned.', exc_info=True, extra={'application':'pizza_app'})
            return _json_response('There are no requested resource', HTTP_405_METHOD_NOT_ALLOWED)

        try:
            allow_anonymous = getattr(view, 'allow_anonymous', False)
            if allow_anonymous:
                claims = None
            else:
                token = get_auth_token(request)
                if token is None:
                    return _json_response('Please sign in to get access to resource', HTTP_401_UNAUTHORIZED)

                try:
                    claims = AUTH_TOKEN_UTIL.verify_jwt_token(token)
                    if claims.type != 'access':
                        return _json_response('Please sign in to get access to resource', HTTP_401_UNAUTHORIZED)
                except jwt.ExpiredSignatureError as e:
                    return _json_response('Your session is expired. Please sign in to get access to resource', HTTP_401_UNAUTHORIZED)
                except jwt.InvalidTokenError as e:
                    return _json_response('Please sign in to get access to resource', HTTP_401_UNAUTHORIZED)

                if token_blk_list.is_blacklisted(token):
                    return _json_response('Please sign in before', HTTP_401_UNAUTHORIZED)

                if usr_temp_blk_list.is_blacklisted(claims.user_id):
                    return _json_response('Your user is removed. Access is forbidden.', HTTP_403_FORBIDDEN)

            setattr(request, 'claims', claims)
            setattr(request, 'demand_context', DemandContext(claims=claims, arguments={}))
        except Exception:
            LOGGER.error('Failed on handling Authorization middleware. 500 code is returned', exc_info=True, extra={'application':'pizza_app'})
            return _json_response('Sorry for inconviewnce. We are working on the problem.', HTTP_500_INTERNAL_SERVER_ERROR)

        return self.get_response(request)
