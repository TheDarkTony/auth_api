import json
import secrets
from typing import Callable

from core_contracts.identity.repositories import IUserRepository
from core_contracts.temp_token.repositories import ITempTokenRepository
from core_contracts.temp_token.models import TokenType
from core_contracts.metainfo import FieldMetaData, metainfo_int
from core_contracts.issues import ValidationIssue, ForbiddenIssue, ApplicationIssue
from core_contracts.queue.emailer_2fa import Emailer2FAQueuePublisher, Email2FAVerificationMessage, VerificationEvents
from core_contracts.identity import models as iden_model

from core import utils
from core.auth.utils import Sign2FAFeedbackDemand, verify_2fa_feedback_demand_filter, AuthTokenUtil
from core.auth.signup import Settings
from core.identity.demands import SignInDemand
from core.identity.demands import DemandAccepted
from core.handler import Handler, DemandContext, Response, Pipeline, MessageType, get_default_pipeline


class SignInDemandValidationFilter:

    def __init__(self, settings: Settings) -> None:
        self.settings: Settings = settings

    def verify(self, ctx: DemandContext, next: Callable[[], Response]) -> Response:
        
        demand = ctx.get_demand(SignInDemand)

        if demand.email is None or len(demand.email) == 0:
            raise ValidationIssue('Email is required')
        
        if demand.pwd is None or len(demand.pwd) == 0:
            raise ValidationIssue('Password is required')

        max_email_length = metainfo_int(iden_model.Identity, 'email', FieldMetaData.max_length.name)
        if len(demand.email) > max_email_length:
            raise ValidationIssue(f'Length of email is greater than {max_email_length}')

        if not self.settings.email_regex.match(demand.email):
            raise ValidationIssue('Value of email is invalid. It should contain at least @ and dot')

        return next()


def pipeline_sign_in(settings: Settings) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(SignInDemandValidationFilter(settings).verify)
    return pipeline


class SingInHandler(Handler):

    def __init__(self,
        user_repo: IUserRepository,
        emailer_queue: Emailer2FAQueuePublisher,
        settings: Settings,
        auth_util: AuthTokenUtil
    ) -> None:
        self._user_repo: IUserRepository = user_repo
        self.__emailer_queue: Emailer2FAQueuePublisher = emailer_queue
        self.settings: Settings = settings
        self.auth_util: AuthTokenUtil = auth_util

    def execute(self, ctx: DemandContext) -> Response:

        demand = ctx.get_demand(SignInDemand)
        usr = self._user_repo.fetch_active_by_usrname(demand.email)

        if usr is None:
            raise ValidationIssue('Active user is not located with specified email')

        if usr.deleted_date is not None:
            raise ForbiddenIssue('The user has been deleted.')

        if not utils.verify_hash(demand.pwd, usr.pwd):
            raise ValidationIssue('Provided password is incorrect')

        if usr.email_2fa_enabled:
            temp_token = secrets.token_hex(16)
            msg = Email2FAVerificationMessage(
                VerificationEvents.SIGNIN.value,
                temp_token,
                demand.email,
                self.settings.email_code_seconds_ttl
            )
            self.__emailer_queue.send_2fa_code_via_email(msg, correlation_id=ctx.request_trace_id)

            data = DemandAccepted(temp_token)
            resp = Response(202, data=data, state_code=utils.AcceptedStateEnum.Verification2FA.value)
            resp.add_message('Please enter code we have sent to your email', MessageType.info)
            return resp

        signin_data = self.auth_util.generate_access_data(
            usr.identity_id,
            usr.role_id,
            usr.id
        )
        return Response(200, data=signin_data)


def pipeline_sign_in_2fa_feedback() -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(verify_2fa_feedback_demand_filter)
    return pipeline


class SignIn2FAHandler(Handler):

    def __init__(self, user_repo: IUserRepository
        , token_repo: ITempTokenRepository
        , auth_util: AuthTokenUtil
    ) -> None:
        self._user_repo: IUserRepository = user_repo
        self._temp_token_repo: ITempTokenRepository = token_repo
        self.auth_util: AuthTokenUtil = auth_util

    def execute(self, ctx: DemandContext) -> Response:

        demand = ctx.get_demand(Sign2FAFeedbackDemand)
        token = self._temp_token_repo.fetch_by_token(demand.process_token)
        if token is None:
            raise ValidationIssue('Your code is expered or missed. Please try to get new code.')

        if token.expired_at.timestamp() < utils.utcnow().timestamp():
            raise ValidationIssue('Your code is expered. Please try to get new code.')

        if token.type != TokenType.SIGNIN_2FA.value:
            raise ValidationIssue('Provided token is invalid')

        data: dict = json.loads(token.json_data)

        code: str|None = data.get('code')
        email: str|None = data.get('email')

        if code is None or email is None:
            raise ApplicationIssue(f'Code or email is empty for token {token.token}')

        if code != demand.code:
            raise ValidationIssue('Provided code is invalid.')

        usr = self._user_repo.fetch_active_by_usrname(email)
        if usr is None:
            raise ApplicationIssue(f'User with name = {email} is not located')

        if usr.deleted_date is not None:
            raise ForbiddenIssue('The user has been deleted.')

        signin_data = self.auth_util.generate_access_data(
            usr.identity_id,
            usr.role_id,
            usr.id
        )
        return Response(200, data=signin_data)
