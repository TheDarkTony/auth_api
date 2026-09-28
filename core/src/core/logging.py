import logging
import json
from typing import Protocol
from types import TracebackType
import traceback

from core.utils import utcnow
from core_contracts.handler import TRACE_ID, DemandContext


class QueuePublisher(Protocol):

    def enqueue(self, json_message: str): ...


class LogViaQueueHandler(logging.Handler):

    def __init__(self, queue:QueuePublisher, level: int | str = 0) -> None:
        super().__init__(level)
        self.queue = queue

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if record.name.startswith('pika'):
                #Skip pika logs due to deadlock. Before to create esteblish connection pika logs INFO about the event.
                #For the log entry can be processed by different way ... file etc.
                return

            exc_traceback:TracebackType|None = None
            if record.exc_info is not None:
                exc_type, exc_value, exc_traceback = record.exc_info

            demand_ctx: DemandContext|None = getattr(record, 'demand_ctx', None)
            application: str|None = getattr(record, 'application', None)
            demand_args:str|None = None
            if demand_ctx is not None:

                claims = demand_ctx.current_usr_claims
                if claims is not None:
                    claims = claims.__dict__

                demand = demand_ctx.demand
                if demand is not None and not isinstance(demand, dict):
                    demand = demand.__dict__

                demand_args = json.dumps({
                    'arguments': demand_ctx.arguments,
                    'claims': claims,
                    'demand': demand
                }, default=str)

            msg = {
                'level': getattr(record, 'levelname', 'unknown'),
                'correlation_id': TRACE_ID.get(),
                'happened_at': str(utcnow()),
                'message': record.getMessage(),
                'traceback': "".join(traceback.format_tb(exc_traceback)) if exc_traceback is not None else None,
                'demand_args': demand_args,
                'application': application
            }

            json_msg = json.dumps(msg)
            self.queue.enqueue(json_msg)
        except Exception as ex:
            print('logger exception:')
            print(ex)
            self.handleError(record)
