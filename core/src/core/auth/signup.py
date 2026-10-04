import secrets
import re
import json

from typing import Callable
from dataclasses import dataclass, field

from core_contracts.identity.repositories import IIdentityRepository, IUserRepository
from core_contracts.identity.models import Identity, UserSubject
from core_contracts.issues import ValidationIssue, ApplicationIssue, ConfigurationIssue
from core_contracts.metainfo import FieldMetaData, metainfo_int
from core_contracts.temp_token.repositories import ITempTokenRepository

from core_contracts.queue.emailer_2fa import Email2FAVerificationMessage, Emailer2FAQueuePublisher, VerificationEvents

from core import utils
from core.auth.utils import verify_2fa_feedback_demand_filter, AuthTokenUtil
from core.identity.demands import SignUpDemand, Sign2FAFeedbackDemand, DemandAccepted
from core.handler import Handler, Response, MessageType
from core.handler import DemandContext, Pipeline, get_default_pipeline


@dataclass
class Settings:
    default_role_id: int
    default_email_2fa_enabled: bool
    email_code_seconds_ttl: int
    email_regex_template: str
    email_regex: re.Pattern = field(init=False)

    def __post_init__(self):
        if self.email_regex_template is not None:
            self.email_regex = re.compile(rf'{self.email_regex_template}')


class VerifySignUpDemandFilter:

    def __init__(self, settings: Settings) -> None:
        if settings.email_regex_template is None or len(settings.email_regex_template) <=0:
            raise ConfigurationIssue('Missed configuration: email_regex_template')

        self.settings: Settings = settings

    def verify(self, ctx: DemandContext, next: Callable[[], Response]) -> Response:
        
        demand = ctx.get_demand(SignUpDemand)
        
        if demand.email is None or len(demand.email) == 0:
            raise ValidationIssue('Email is required')
        
        if demand.pwd is None or len(demand.pwd) == 0:
            raise ValidationIssue('Password is required')

        max_email_length = metainfo_int(Identity, 'email', FieldMetaData.max_length.name)
        if len(demand.email) > max_email_length:
            raise ValidationIssue(f'Length of email is greater than {max_email_length}')

        if not self.settings.email_regex.match(demand.email):
            raise ValidationIssue('Value of email is invalid. It should contain at least @ and dot')

        return next()


def pipeline_signup(settings: Settings) -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(VerifySignUpDemandFilter(settings).verify)
    return pipeline


class SignUpHandler(Handler):

    def __init__(self, identity_repo: IIdentityRepository
        , user_repo: IUserRepository
        , emailer_queue: Emailer2FAQueuePublisher
        , settings: Settings
    ) -> None:
        if settings.email_code_seconds_ttl is None or settings.email_code_seconds_ttl <= 0:
            raise ConfigurationIssue('Missed configuration: email_code_seconds_ttl')

        self._identity_repo: IIdentityRepository = identity_repo
        self._user_repo: IUserRepository = user_repo
        self._emailer_queue: Emailer2FAQueuePublisher = emailer_queue
        self.settings: Settings = settings

    def execute(self, ctx: DemandContext) -> Response:

        demand = ctx.get_demand(SignUpDemand)
        identity = self._identity_repo.fetch_by_email(demand.email)

        if identity is None:
            identity = Identity(demand.email, False)
            identity = self._identity_repo.save(identity)

        if identity.is_activated:
            usr = self._user_repo.fetch_by_usrname(demand.email)
            if usr is not None and usr.deleted_date is None:
                raise ValidationIssue("User with email is already registered")

        token = secrets.token_hex(16)
        pwd = utils.hashpwd(demand.pwd)
        msg = Email2FAVerificationMessage(
            VerificationEvents.SIGNUP.value,
            token, demand.email,
            self.settings.email_code_seconds_ttl,
            pwd
        )

        self._emailer_queue.send_2fa_code_via_email(msg, correlation_id=ctx.request_trace_id)

        data = DemandAccepted(token)
        response = Response(202, data=data, state_code=utils.AcceptedStateEnum.Verification2FA.value)
        msg = 'We have sent email with code to verify email. Please enter code to form'
        response.add_message(msg, MessageType.info)

        return response


def pipeline_signup_2fa() -> Pipeline:
    pipeline = get_default_pipeline()
    pipeline.use(verify_2fa_feedback_demand_filter)
    return pipeline


class SignUp2FAVerificationHandler(Handler):

    def __init__(self, token_repo: ITempTokenRepository
        , identity_repo: IIdentityRepository
        , user_repo: IUserRepository
        , settings: Settings
        , auth_util: AuthTokenUtil
    ) -> None:
        if settings.default_role_id is None or settings.default_role_id <= 0:
            raise ConfigurationIssue('Missed configuration: default_role_id')
        
        self._temp_token_repo: ITempTokenRepository = token_repo
        self._identity_repo: IIdentityRepository = identity_repo
        self._user_repo: IUserRepository = user_repo
        self.settings: Settings = settings
        self.auth_util: AuthTokenUtil = auth_util


    def execute(self, ctx: DemandContext) -> Response:
        
        demand = ctx.get_demand(Sign2FAFeedbackDemand)
        token = self._temp_token_repo.fetch_by_token(demand.process_token)
        if token is None:
            raise ValidationIssue('Your code is expered or missed. Please try to get new code.')

        if token.expired_at.timestamp() < utils.utcnow().timestamp():
            raise ValidationIssue('Your code is expered. Please try to get new code.')

        data: dict = json.loads(token.json_data)

        code: str|None = data.get('code')
        email: str|None = data.get('email')
        pwd: str|None = data.get('pwd')

        if code is None or email is None or pwd is None:
            raise ApplicationIssue(f'Code, email or pwd is empty for token {token.token}')

        if code != demand.code:
            raise ValidationIssue('Provided code is invalid.')

        identity = self._identity_repo.fetch_by_email(email)

        if identity is None:
            raise ApplicationIssue(f'Identity is not located for email={email}')

        if identity.is_activated:
            usr = self._user_repo.fetch_by_usrname(email)
            if usr is not None:
                if usr.deleted_date is None:
                    raise ValidationIssue('User with email is already registered.')
                else:
                    usr.deleted_date = None
                    user = self._user_repo.save(usr)
                    
                    signin_data = self.auth_util.generate_access_data(
                        identity.id,
                        user.role_id,
                        user.id
                    )
                    return Response(201, data=signin_data)

        identity.is_activated = True
        identity.email_verified = True

        usr = UserSubject(
            identity.id,
            self.settings.default_role_id,
            identity.email,
            pwd,
            self.settings.default_email_2fa_enabled
        )

        identity, user = self._identity_repo.update_and_attach_user(identity, usr)

        signin_data = self.auth_util.generate_access_data(
            identity.id,
            user.role_id,
            user.id
        )
        return Response(201, data=signin_data)
