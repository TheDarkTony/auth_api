import jwt

from typing import Callable, Any
from dataclasses import asdict

from core_contracts.handler import Claims
from core_contracts.metainfo import get_metainfo
from core_contracts.issues import ValidationIssue, ConfigurationIssue

from core.utils import utc_plus_delta
from core.handler import DemandContext, Response
from core.identity.demands import SignInData, Sign2FAFeedbackDemand


class AuthTokenUtil:
    _REFRESH_JWT_TYPE = 'refresh'
    _ACCESS_JWT_TYPE = 'access'

    def __init__(self,
        secret_jwt_key: str,
        jwt_algorithm: str,
        access_token_seconds_ttl: int,
        refresh_token_seconds_ttl: int
    ) -> None:

        if secret_jwt_key is None or len(secret_jwt_key) == 0:
            raise ConfigurationIssue('Missed configuration: secret_jwt_key')

        if jwt_algorithm is None or len(jwt_algorithm) == 0:
            raise ConfigurationIssue('Missed configuration: jwt_algorithm')

        if access_token_seconds_ttl is None or access_token_seconds_ttl <= 0:
            raise ConfigurationIssue('Missed configuration: access_token_seconds_ttl')

        if refresh_token_seconds_ttl is None or refresh_token_seconds_ttl <= 0:
            raise ConfigurationIssue('Missed configuration: refresh_token_seconds_ttl')

        self.access_token_seconds_ttl: int = access_token_seconds_ttl
        self.refresh_token_seconds_ttl: int = refresh_token_seconds_ttl
        self.secret_jwt_key: str = secret_jwt_key
        self.jwt_algorithm: str = jwt_algorithm


    def generate_jwt_token(self, claims: Claims) -> str:
        return jwt.encode(asdict(claims), self.secret_jwt_key, algorithm=self.jwt_algorithm)

    def verify_jwt_token(self, token) -> Claims:
        payload: dict[str, Any] = jwt.decode(token, self.secret_jwt_key, [self.jwt_algorithm])
        return Claims(**payload)

    def generate_access_data(
        self,
        identity_id: int,
        role_id: int,
        usr_id: int
    ):
        access_token = self.generate_jwt_token(Claims(
                identity_id,
                role_id,
                usr_id,
                self._ACCESS_JWT_TYPE,
                exp=utc_plus_delta(self.access_token_seconds_ttl)
            )
        )

        refresh_token = self.generate_jwt_token(Claims(
                identity_id,
                role_id,
                usr_id,
                self._REFRESH_JWT_TYPE,
                exp=utc_plus_delta(self.refresh_token_seconds_ttl)
            )
        )

        return SignInData(access_token, refresh_token)


def verify_2fa_feedback_demand_filter(ctx: DemandContext, next: Callable[[], Response]) -> Response:
    
    demand = ctx.get_demand(Sign2FAFeedbackDemand)
    
    if demand.process_token is None or len(demand.process_token) == 0:
        raise ValidationIssue('Email is required.')
    
    if demand.code is None or len(demand.code) == 0:
        raise ValidationIssue('Code is required.')

    token_max_length = get_metainfo(Sign2FAFeedbackDemand, 'process_token').max_length
    if token_max_length is not None and len(demand.process_token) > token_max_length:
        raise ValidationIssue(f'Wrong token value.')
    
    code_max_length = get_metainfo(Sign2FAFeedbackDemand, 'code').max_length
    if code_max_length is not None and len(demand.code) > code_max_length:
        raise ValidationIssue(f'Value of code is invalid.')

    return next()
