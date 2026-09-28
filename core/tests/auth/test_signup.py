import pytest

from core_contracts.identity.repositories import IIdentityRepository
from core_contracts.identity.models import Identity, User
from core_contracts.queue.emailer_2fa import Email2FAVerificationMessage, Emailer2FAQueuePublisher
from core.auth.signup import SignUpHandler, pipeline_signup, Settings
from core.handler import Pipeline, DemandContext, MessageType, Response

from tests.conftest import FakeIdentityRepo, MockEmail2FaVerificationQueue, FakeUserRepo
from tests.auth.conftest import BabRequestCase


@pytest.fixture(scope='class')
def emailer_queue(monkey) -> Emailer2FAQueuePublisher:
    def send_2fa_code_via_email(q, message: Email2FAVerificationMessage):
        assert message.email is not None
        assert message.pwd is not None
        assert message.code_seconds_ttl > 0
        assert message.token is not None

    monkey.setattr(MockEmail2FaVerificationQueue, MockEmail2FaVerificationQueue.send_2fa_code_via_email.__name__, send_2fa_code_via_email)
    return MockEmail2FaVerificationQueue()

@pytest.fixture(scope='class')
def pipeline(settings) -> Pipeline:
    return pipeline_signup(settings)

@pytest.fixture(scope='class')
def handler(identity_repo, user_repo, emailer_queue, settings):
    return SignUpHandler(identity_repo, user_repo, emailer_queue, settings)


class TestSignUpAccepted:

    @pytest.fixture(scope='class', params=[
        DemandContext({'email':'ivanov@bk.ru', 'pwd': 'Test@1234'}, None),
        DemandContext({'email':'abc_12345678901234567890123456789012345678901234567890123456789012345@bk.ru', 'pwd': 'Test@123'}, None),
    ],
    ids=[
        'ordinar_request_data',
        'edge_email_75_length_data'
    ])
    @classmethod
    def rqst_ctx(cls, request):
        return request.param

    @pytest.fixture(scope='class')
    @classmethod
    def identity_repo(cls, monkey):
        def get_by_email(repo, email)->Identity|None:
            assert email is not None
            return None
        
        def save_identity(repo, identity: Identity) -> Identity:
            assert identity.id == 0
            identity.id = 1
            return identity

        monkey.setattr(FakeIdentityRepo, FakeIdentityRepo.fetch_by_email.__name__, get_by_email)
        monkey.setattr(FakeIdentityRepo, FakeIdentityRepo.save.__name__, save_identity)
        return FakeIdentityRepo()

    @pytest.fixture(scope='class')
    @classmethod
    def user_repo(cls, monkey):
        def fetch_by_usrname(repo, usrname):
            assert usrname is not None
            return None
        
        monkey.setattr(FakeUserRepo, FakeUserRepo.fetch_by_usrname.__name__, fetch_by_usrname)
        return FakeUserRepo()

    def test_response_status(self, response: Response):
        assert response.status == 202

    def test_response_info_message(self, response: Response):
        assert len(response.messages) == 1 and response.messages[0].type == MessageType.info

    def test_response_data_with_token(self, response: Response):
        assert response.data is not None
        token = None
        if isinstance(response.data, dict):
            token = response.data.get('process_token')
        else:
            token = getattr(response.data, 'process_token', None)

        assert token is not None


class TestSignUpWithEmailCollision(BabRequestCase):

    @pytest.fixture(scope='class')
    @classmethod
    def rqst_ctx(cls):
        return DemandContext({'email':'popov@bk.ru', 'pwd': 'Test@1234'}, None)

    @pytest.fixture(scope='class')
    @classmethod
    def identity_repo(cls, monkey) -> IIdentityRepository:
        def get_identity(repo, email) -> Identity|None:
            assert email is not None
            return Identity(email, True, id=99, is_activated=True)

        monkey.setattr(FakeIdentityRepo, FakeIdentityRepo.fetch_by_email.__name__, get_identity)
        return FakeIdentityRepo()

    @pytest.fixture(scope='class')
    @classmethod
    def user_repo(cls, monkey):
        def fetch_by_usrname(repo, usrname):
            assert usrname is not None
            return User(99, 4, usrname, 'test@123', True, None, 100)
        
        monkey.setattr(FakeUserRepo, FakeUserRepo.fetch_by_usrname.__name__, fetch_by_usrname)
        return FakeUserRepo()


class TestSignUpBadRequest(BabRequestCase):

    @pytest.fixture(scope='class', params=[
        DemandContext({'email':None, 'pwd': 'Test@123'}, None),
        DemandContext({'email':'ivanov', 'pwd': 'Test@123'}, None),
        DemandContext({'email':'ivanov@bk.ru', 'pwd': ''}, None),
        DemandContext({'email':'abc_123456789012345678901234567890123456789012345678901234567890123456@bk.ru', 'pwd': 'Test@123'}, None),
    ], ids=[
        'email is required',
        'wrong email value. missed @',
        'pwd is required',
        'email is longer 75 symbols'
    ])
    @classmethod
    def rqst_ctx(cls, request):
        return request.param
