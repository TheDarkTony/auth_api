import valkey

from core_contracts.identity.repositories import IUserTempBlackListRepository


class AccessTokenBlackListRepo:

    def __init__(self, valkey_instance: valkey.Valkey) -> None:
        self._valkey: valkey.Valkey = valkey_instance

    def push_to_black_list(self, value: str, ttl:int):
        self._valkey.setex(f'blacklist:access_token:{value}', ttl, 1)

    def is_blacklisted(self, value: str) -> bool:
        exists = self._valkey.exists(f'blacklist:access_token:{value}')
        num = int(exists) # type: ignore
        return num > 0


class UserTempBlackListRepo(IUserTempBlackListRepository):

    def __init__(self, valkey_instance: valkey.Valkey) -> None:
        self._valkey: valkey.Valkey = valkey_instance

    def push_to_black_list(self, user_id: int, ttl: int):
        self._valkey.setex(f'blacklist:user:{user_id}', ttl, 1)

    def is_blacklisted(self, user_id: int) -> bool:
        exists = self._valkey.exists(f'blacklist:user:{user_id}')
        num = int(exists) # type: ignore
        return num > 0


class MockAccessTokenBlackListRepo:

    def push_to_black_list(self, value: str, ttl:int):
        print(f'bl_mock:value:{value}')

    def is_blacklisted(self, value: str) -> bool:
        return False


class MockUserTempBlackListRepo(IUserTempBlackListRepository):
    
    def push_to_black_list(self, user_id: int, ttl: int):
        print(f'bl_mock:user_id:{user_id}')

    def is_blacklisted(self, user_id: int) -> bool:
        return False
