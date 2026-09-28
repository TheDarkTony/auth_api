import logging
from typing import Callable

from rest_framework.views import exception_handler
from rest_framework.settings import settings

import valkey

from core_contracts.handler import MessageType, Response
from core_contracts.issues import ConfigurationIssue
from core_contracts.identity.repositories import IUserTempBlackListRepository
from queue_publishers import publisher

from src.api_core.response import Offer
from src.api_core.serializers import ResultSerializer


LOGGER = logging.getLogger(__name__)


def api_internal_exception_handler(exc, context):
    request = context.get('request')
    demand_ctx = getattr(request, 'demand_context', None) if request is not None else None
    LOGGER.error(str(exc), exc_info=True, extra={'application':'pizza_app', 'demand_ctx': demand_ctx})

    # #standard error response
    # if settings.DEBUG:
    #     response = exception_handler(exc, context)
    #     return response

    res = Response(500)
    res.add_message('Something goes wrong. We are working on it', MessageType.error)
    ser =  ResultSerializer(res)

    return Offer(ser, res).offer


class DjangoLogFilter(logging.Filter):

    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        return not record.name.startswith('django')


class QueueLogAdapter:

    def __init__(self, queue_manager_provired, exchange:str) -> None:
        self._manager_provider:Callable[[], publisher.QueueManager] = queue_manager_provired
        self._exchange: str = exchange
        self._queue_manager: publisher.QueueManager|None = None

    def enqueue(self, json_message: str):
        publisher = self._manager.get_publisher()
        
        (publisher
         .msg_props(content_type='application/json')
         .target(self._exchange, '')
         .publish(json_message))

    @property
    def _manager(self) -> publisher.QueueManager:
        if self._queue_manager is None:
            self._queue_manager = self._manager_provider()
        return self._queue_manager


class AccessTokenBlackListValkey:

    def __init__(self, valkey_instance: valkey.Valkey) -> None:
        self._valkey: valkey.Valkey = valkey_instance

    def push_to_black_list(self, value: str, ttl:int):
        self._valkey.setex(f'blacklist:access_token:{value}', ttl, 1)

    def is_blacklisted(self, value: str) -> bool:
        exists = self._valkey.exists(f'blacklist:access_token:{value}')
        num = int(exists) # type: ignore
        return num > 0


class UserTempBlackListValkey(IUserTempBlackListRepository):

    def __init__(self, valkey_instance: valkey.Valkey) -> None:
        self._valkey: valkey.Valkey = valkey_instance

    def push_to_black_list(self, user_id: int, ttl: int):
        self._valkey.setex(f'blacklist:user:{user_id}', ttl, 1)

    def is_blacklisted(self, user_id: int) -> bool:
        exists = self._valkey.exists(f'blacklist:user:{user_id}')
        num = int(exists) # type: ignore
        return num > 0


def get_auth_token(request) -> str|None:

    token:str|None = request.headers.get('Authorization')
    if token is None and settings.DEBUG:
        token = request.COOKIES.get('_access_token_')

    prefix = 'Bearer '
    if token is not None and token.startswith(prefix):
        token = token.replace(prefix, '').strip()

    return token