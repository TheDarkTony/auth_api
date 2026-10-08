from typing import Any, Sequence

import pytest
from _pytest.monkeypatch import MonkeyPatch

from core_contracts.temp_token.models import TempToken
from core_contracts.identity.repositories import IIdentityRepository, IUserRepository
from core_contracts.identity.models import Identity, IdentityItem, IdentitySubject, User, UserSubject
from core_contracts.temp_token.repositories import ITempTokenRepository
from core_contracts.queue.emailer_2fa import Emailer2FAQueuePublisher, Email2FAVerificationMessage
from core.handler import MessageType, Response


@pytest.fixture(scope='class')
def monkey():
    m = MonkeyPatch()
    yield m
    m.undo()


class BabRequestCase:
    def test_response_status(self, response: Response):
        assert response.status == 400
    
    def test_response_error_message(self, response: Response):
        assert len(response.messages) == 1 and response.messages[0].type == MessageType.error

    def test_response_empty_data(self, response: Response):
        assert response.data is None


class FakeTempTokenRepo(ITempTokenRepository):
    def fetch_by_token(self, token: str) -> TempToken | None:
        raise NotImplementedError()

    def add(self, token: TempToken) -> TempToken:
        raise NotImplementedError()

    def edit(self, token: TempToken) -> TempToken:
        raise NotImplementedError()


class FakeIdentityRepo(IIdentityRepository):
    def fetch_by_id(self, id: int) -> Identity:
        raise NotImplementedError()

    def save(self, model: Identity) -> Identity:
        raise NotImplementedError()

    def delete(self, id: int) -> None:
        raise NotImplementedError()

    def register(self, identity: IdentitySubject, user: UserSubject) -> tuple[Identity, User]:
        raise NotImplementedError()

    def fetch_by_email(self, email: str) -> Identity | None:
        raise NotImplementedError()

    def update_and_attach_user(self, identity: Identity, user: UserSubject) -> tuple[Identity, User]:
        raise NotImplementedError()

    def list(self, predicate: dict[str, Any]) -> Sequence[IdentityItem]:
        raise NotImplementedError


class FakeUserRepo(IUserRepository):
    def fetch_by_id(self, id: int) -> User:
        raise NotImplementedError

    def save(self, model: User) -> User:
        raise NotImplementedError

    def delete(self, id: int) -> None:
        raise NotImplementedError

    def fetch_active_by_usrname(self, usrname: str) -> User | None:
        raise NotImplementedError

    def fetch_by_usrname(self, usrname: str) -> User | None:
        raise NotImplementedError

    def list(self, predicate: dict[str, Any]) -> Sequence[User]:
        raise NotImplementedError


class MockEmail2FaVerificationQueue(Emailer2FAQueuePublisher):

    def send_2fa_code_via_email(self, data: Email2FAVerificationMessage, correlation_id: str | None):
        raise NotImplementedError
