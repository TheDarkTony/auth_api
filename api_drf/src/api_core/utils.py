import logging

from rest_framework.views import exception_handler
from rest_framework.settings import settings

from core_contracts.handler import MessageType, Response, TRACE_ID
from core_contracts.queue.bus import IMessageInBus, Message

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


class BusQueueLogAdapter(object):

    def __init__(self, bus:IMessageInBus):
        self._bus: IMessageInBus = bus
        self._exchange: str = ''

    def setup_exchange(self, exchange: str):
        self._exchange = exchange

    def enqueue(self, json_message: str):
        self._bus.enqueue(Message(
            body=json_message,
            content_type='application/json',
            correlation_id=TRACE_ID.get(),
            destination_point=self._exchange
        ))


def get_auth_token(request) -> str|None:

    token:str|None = request.headers.get('Authorization')
    if token is None and settings.DEBUG:
        token = request.COOKIES.get('_access_token_')

    prefix = 'Bearer '
    if token is not None and token.startswith(prefix):
        token = token.replace(prefix, '').strip()

    return token
