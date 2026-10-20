from typing import Sequence, cast, Any

import valkey

from core_contracts.permission.models import Permission, RolePermission
from core_contracts.permission.repositories import IRolePermissionRepository


class RolePermissionCacheRepository(IRolePermissionRepository):
    TTL = 300 #seconds

    def __init__(self, repo: IRolePermissionRepository, valkey_client: valkey.Valkey) -> None:
        self._repo: IRolePermissionRepository = repo
        self._valkey: valkey.Valkey = valkey_client

    #can be removed from interface
    def list_by_resource_name(self, role_id: int, resource_name: str) -> Sequence[tuple[RolePermission, int]]:
        return self._repo.list_by_resource_name(role_id, resource_name)

    def fetch_by_id(self, id: int) -> RolePermission | None:
        cached_entry = cast(dict, self._valkey.hgetall(self._CACHE_ENTRY_KEY_(id)))
        if len(cached_entry) > 0:
            return self._entry(cached_entry)
        perm = self._repo.fetch_by_id(id)
        if perm is None:
            return None
        self._cache_item(self._CACHE_ENTRY_KEY_(id), perm)
        return perm

    def save(self, model: RolePermission, context: dict[str, Any]|None=None) -> RolePermission:
        role_id, resource_id = self._validate_ctx(context)
        perm = self._repo.save(model)
        self._cache_item(self._CACHE_ENTRY_KEY_(perm.id), perm)
        self._include_to_cache_set(self._CACHE_SET_KEY_(role_id, resource_id), [perm])
        return perm

    def delete(self, id: int, context: dict[str, Any]|None=None) -> None:
        self._repo.delete(id)
        self._valkey.delete(self._CACHE_ENTRY_KEY_(id))

    def list_by_id(self, role_id: int, resource_id: int) -> Sequence[Permission]:
        key = self._CACHE_SET_KEY_(role_id, resource_id)
        cache_entries = self._list_by_id_from_cache(key)
        if len(cache_entries) > 0:
            return cache_entries
        
        perms = self._repo.list_by_id(role_id, resource_id)

        for p in perms:
            self._cache_item(self._CACHE_ENTRY_KEY_(p.id), p)
        self._include_to_cache_set(key, perms)
        return perms


    def _list_by_id_from_cache(self, key: str) -> Sequence[Permission]:
        ids = cast(set, self._valkey.smembers(key))
        entries = []
        for _id in ids:
            entry = cast(dict, self._valkey.hgetall(self._CACHE_ENTRY_KEY_(int(_id.decode('utf-8')))))
            if len(entry) > 0:
                entries.append(self._entry(entry))
        return sorted(entries, key= lambda e: e.weight)

    def _include_to_cache_set(self, key: str, perms: Sequence[RolePermission]) -> None:
        self._valkey.sadd(key, *[p.id for p in perms])
        self._valkey.expire(key, self.TTL)

    def _exclude_from_cache_set(self, key: str, perms: Sequence[RolePermission]) -> None:
        self._valkey.srem(key, *[p.id for p in perms])
        self._valkey.expire(key, self.TTL)

    def _cache_item(self, key: str, perms: RolePermission) -> None:
        self._valkey.hset(key, mapping=perms.model_dump(exclude_none=True, exclude={'weight', 'name'}))
        self._valkey.expire(key, self.TTL)

    @staticmethod
    def _validate_ctx(ctx:dict[str, Any]|None) -> tuple[int, int]:
        if ctx is None:
            raise Exception('Missed context argument for cache repository')
        role_id:int|None = ctx.get('role_id')
        resource_id:int|None = ctx.get('resource_id')
        if role_id is None:
            raise Exception('Missed context role_id argument for cache repo')
        if resource_id is None:
            raise Exception('Missed context resource_id argument for cache repo')
        return role_id, resource_id

    @staticmethod
    def _entry(cached_item)-> Permission:
        return Permission.model_validate({k.decode('utf-8'):v.decode('utf-8') for k, v in cached_item.items()})

    @staticmethod
    def _CACHE_ENTRY_KEY_(id) -> str:
        return f'permission:{id}'

    @staticmethod
    def _CACHE_SET_KEY_(role_id: int, resource_id: int) -> str:
        return f'role:{role_id}:resource:{resource_id}:permissions'
