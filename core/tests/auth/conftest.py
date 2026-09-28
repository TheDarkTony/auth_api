import pytest

from core.handler import Pipeline
from core.auth.signup import Settings
from core.auth.utils import AuthTokenUtil

from tests.conftest import BabRequestCase as BaseBabRequestCase
from tests.conftest import FakeIdentityRepo, FakeTempTokenRepo, FakeUserRepo


@pytest.fixture(scope='class')
def settings() -> Settings:
    return Settings(4, True, 300, '[^@]+@[^@]+')

@pytest.fixture(scope='class')
def auth_token_util() -> AuthTokenUtil:
    return AuthTokenUtil('AWDJy-DOlkeVBZ80P-1vD6oY9QSpiJv3XOkRwSiqSA8','HS256', 300, 500)

@pytest.fixture(scope='class')
def response(rqst_ctx, pipeline: Pipeline, handler):
    return pipeline.execute(rqst_ctx, handler)


class BabRequestCase(BaseBabRequestCase):

    @pytest.fixture(scope='class')
    @classmethod
    def token_repo(cls):
        return FakeTempTokenRepo()

    @pytest.fixture(scope='class')
    @classmethod
    def identity_repo(cls):
        return FakeIdentityRepo()

    @pytest.fixture(scope='class')
    @classmethod
    def user_repo(cls):
        return FakeUserRepo()
