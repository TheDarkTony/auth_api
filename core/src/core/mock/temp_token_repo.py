from core_contracts.temp_token.models import TempToken
from core_contracts.temp_token.repositories import ITempTokenRepository


_MOCK_TEMP_DATA: dict[str, TempToken] = {}


class MockTempTokenRepo(ITempTokenRepository):
    def fetch_by_token(self, token: str) -> TempToken | None:
        t = _MOCK_TEMP_DATA.get(token, None)
        return t

    def add(self, token: TempToken) -> TempToken:
        _MOCK_TEMP_DATA[token.token] = token
        return token

    def edit(self, token: TempToken) -> TempToken:
        raise NotImplementedError
