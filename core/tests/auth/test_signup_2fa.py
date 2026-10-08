import json
import bcrypt
from datetime import timedelta
from secrets import token_hex

import pytest

from core.handler import Pipeline, Response, DemandContext
from core.auth.signup import pipeline_signup_2fa, SignUp2FAVerificationHandler, Sign2FAFeedbackDemand
from core_contracts.identity.models import Identity, UserSubject, User
from core_contracts.temp_token.models import TempToken
from core_contracts.base import utcnow

from tests.conftest import FakeIdentityRepo, FakeTempTokenRepo, FakeUserRepo
from tests.auth.conftest import BabRequestCase


@pytest.fixture(scope='class')
def pipeline() -> Pipeline:
    return pipeline_signup_2fa()

@pytest.fixture(scope='class')
def handler(identity_repo, user_repo, token_repo, settings, auth_token_util):
    return SignUp2FAVerificationHandler(token_repo, identity_repo, user_repo, settings, auth_token_util)


class TestSignUpEmailVerified:

    @pytest.fixture(scope='class')
    @classmethod
    def code(cls):
        return '12345'

    @pytest.fixture(scope='class')
    @classmethod
    def rqst_ctx(cls, code) -> DemandContext:
        demand = Sign2FAFeedbackDemand(process_token=token_hex(16), code=code)
        return DemandContext(demand, None)

    @pytest.fixture(scope='class')
    @classmethod
    def identity_repo(cls, monkey):
        def fetch_identity_by_email(r, email) -> Identity|None:
            assert email is not None
            return Identity(email=email, email_verified=False, fname=None, lname=None, is_activated=False, id=99)

        def update_and_attach_user(r, identity: Identity, usr: UserSubject):
            assert identity.email_verified == True
            assert identity.is_activated == True
            assert usr.role_id > 0
            return identity, User(identity_id=identity.id, role_id=usr.role_id, username=usr.username, pwd=usr.pwd, email_2fa_enabled=usr.email_2fa_enabled, id=99)
        
        monkey.setattr(FakeIdentityRepo, FakeIdentityRepo.fetch_by_email.__name__, fetch_identity_by_email)
        monkey.setattr(FakeIdentityRepo, FakeIdentityRepo.update_and_attach_user.__name__, update_and_attach_user)
        return FakeIdentityRepo()

    @pytest.fixture(scope='class')
    @classmethod
    def user_repo(cls, monkey):
        def fetch_by_usrname(repo, usrname):
            assert usrname is not None
            return None
        
        monkey.setattr(FakeUserRepo, FakeUserRepo.fetch_by_usrname.__name__, fetch_by_usrname)
        return FakeUserRepo()

    @pytest.fixture(scope='class')
    @classmethod
    def token_repo(cls, monkey, code):
        def fetch_by_token(token):
            assert token is not None

            expired_at = utcnow() + timedelta(minutes=1)
            pwd = bcrypt.hashpw('Test@123'.encode('utf-8'), bcrypt.gensalt())
            data = json.dumps({'code':code, 'email': 'ivanov@bk.ru', 'pwd': pwd.decode('utf-8')})
            return TempToken(token=token, type=1, expired_at=expired_at, json_data=data)

        monkey.setattr(FakeTempTokenRepo, 'fetch_by_token', fetch_by_token)
        return FakeTempTokenRepo


    def test_response_status(self, response: Response):
        assert response.status == 201

    def test_response_auth_token(self, response: Response):
        assert response.data is not None

        access_token = None
        if isinstance(response.data, dict):
            access_token = response.data.get('access_token')
        else:
            access_token = getattr(response.data, 'access_token')

        assert access_token is not None and len(access_token) > 0


class TestSignUp2FABadRequest(BabRequestCase):

    @pytest.fixture(scope='class', params=[
        {'process_token':'', 'code':''},
        {'process_token':'qwerty1234', 'code':''},
        {'process_token':'', 'code':'12345'},
        {'process_token':'qwerty1234', 'code':'123456'},
    ],
    ids=[
        'process token and code are required',
        'code is required',
        'process token is reqired',
        'code length is greater max length'
    ])
    @classmethod
    def rqst_ctx(cls, request):
        demand = request.param
        return DemandContext(demand, None)
