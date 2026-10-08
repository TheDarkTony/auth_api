from typing import Callable, Any, Protocol
from enum import IntEnum
from dataclasses import dataclass, field, fields
from datetime import datetime
import uuid, contextvars

from pydantic import BaseModel, ValidationError

from core_contracts.metainfo import DataclassModel
from core_contracts.issues import ValidationIssue


TRACE_ID = contextvars.ContextVar("trace_id", default='')


class MessageType(IntEnum):
    info = 0
    instraction = 1
    warning = 2
    error = 3


@dataclass
class ResponseMessage:
    text: str
    type: MessageType


@dataclass
class Response:
    status: int
    state_code: int|None = field(default=None)
    data: object|None = field(default=None)
    messages: list[ResponseMessage] = field(default_factory=list)

    def add_message(self, text: str, type: MessageType, /) -> None:
        self.messages.append(ResponseMessage(text, type))


@dataclass
class Claims:
    identity_id: int
    role_id: int
    user_id: int
    type:str
    exp: datetime|int


class DemandContext:

    def __init__(self, demand = None, claims: Claims|None = None, arguments:dict[str,Any]|None = None) -> None:
        self.demand:object = demand
        self.current_usr_claims: Claims|None = claims
        if arguments is None:
            self.arguments: dict[str, Any] = {}
        else:
            self.arguments: dict[str, Any] = arguments
        TRACE_ID.set(uuid.uuid4().hex)

    @property
    def request_trace_id(self) -> str:
        return TRACE_ID.get()


    def get_demand[TDemand:DataclassModel](self, demand_type: type[TDemand]) -> TDemand:

        if self.demand is None:
            raise Exception('Invalid behavior. Demand is None.')
        
        demand = self.demand
        if isinstance(self.demand, demand_type):
            return self.demand

        if issubclass(demand_type, BaseModel):
            try:
                from_obj_attr = not isinstance(self.demand, dict)
                self.demand = demand_type.model_validate(self.demand, from_attributes=from_obj_attr)
                return self.demand
            except ValidationError as ex:
                raise ValidationIssue(str(ex))


        demand_fields = fields(demand_type)
        args: dict
        if isinstance(demand, dict):
            args = { field.name: demand.get(field.name, field.default) for field in demand_fields }
        else:
            args = { field.name: getattr(demand, field.name, field.default) for field in demand_fields }

        self.demand = demand_type(**args)
        return self.demand


FilterCallable = Callable[[DemandContext, Callable[[], Response]], Response]


class Handler:

    def execute(self, ctx: DemandContext) -> Response:
        raise NotImplementedError


class PipelineProtocol(Protocol):

    def execute(self, ctx: DemandContext, core_handler: Handler) -> Response: ...