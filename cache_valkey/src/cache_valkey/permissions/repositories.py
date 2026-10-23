from dataclasses import dataclass
from typing import Sequence, cast, Any

import valkey

from core_contracts.issues import ConfigurationIssue
from core_contracts.permission.models import Permission, RolePermission
from core_contracts.permission.repositories import IRolePermissionRepository


@dataclass
class CacheSettings:
    ttl_seconds: int


# Lua-script: check if the key exists before it is added
ADD_ITEM_IF_SET_EXISTS_LUA_SCRIPT = """
if redis.call('EXISTS', KEYS[1]) == 1 then
    -- the key exists then adds item
    return redis.call('SADD', KEYS[1], ARGV[1])
else
    -- the key is expired and does not exist, nothing do
    return nil
end
"""


# LIST_HITEMS_BY_KEYS_SCRIPT = """
#     local results = {}

#     for i, p_key in ipairs(ARGV) do
#         local raw_hgetall = redis.call('HGETALL', p_key)
#         if #raw_hgetall > 0 then
#             table.insert(results, raw_hgetall)
#         end
#     end

#     return results
# """


LIST_HITEMS_BY_SET_SCRIPT = """
    local entries = {}
    local permissions = redis.call('SMEMBERS', KEYS[1])
    for i = 1, #permissions do
        local p_key = "permission:" .. permissions[i]
        local raw = redis.call('HGETALL', p_key)
        if #raw > 0 then
            table.insert(entries, raw)
        end
    end
    return entries
"""


class RolePermissionCacheRepository(IRolePermissionRepository):

    def __init__(self, repo: IRolePermissionRepository, valkey_client: valkey.Valkey, settings: CacheSettings) -> None:
        if settings is None or settings.ttl_seconds is None:
            raise ConfigurationIssue('Missed configuration: ttl_seconds of cache permissions repo')
        self._settings: CacheSettings = settings
        self._repo: IRolePermissionRepository = repo
        self._valkey: valkey.Valkey = valkey_client
        self._decoded_response = self._valkey.connection_pool.connection_kwargs.get('decode_responses', False)

    #can be removed from interface
    def list_by_resource_name(self, role_id: int, resource_name: str) -> Sequence[tuple[RolePermission, int]]:
        return self._repo.list_by_resource_name(role_id, resource_name)

    def fetch_by_id(self, id: int) -> RolePermission | None:
        cached_entry = cast(dict, self._valkey.hgetall(self._ENTRY_CACHE_KEY_(id)))
        if len(cached_entry) > 0:
            return self._entry(cached_entry)
        perm = self._repo.fetch_by_id(id)
        if perm is None:
            return None
        self._cache_item(self._ENTRY_CACHE_KEY_(id), perm)
        return perm

    def save(self, model: RolePermission, context: dict[str, Any]|None=None) -> RolePermission:
        role_id, resource_id = self._validate_ctx(context)
        perm = self._repo.save(model)

        self._cache_item(self._ENTRY_CACHE_KEY_(perm.id), perm)
        self._include_item_to_cache_set(self._ENTRIES_CACHE_KEY_(role_id, resource_id), perm)
        return perm

    def delete(self, id: int, context: dict[str, Any]|None=None) -> None:
        self._repo.delete(id)
        self._valkey.delete(self._ENTRY_CACHE_KEY_(id))

    def list_by_id(self, role_id: int, resource_id: int) -> Sequence[Permission]:
        key = self._ENTRIES_CACHE_KEY_(role_id, resource_id)
        cache_entries = self._list_perms_from_cache(key)
        if len(cache_entries) > 0:
            return cache_entries
        
        perms = self._repo.list_by_id(role_id, resource_id)
        self._include_cache_set(key, perms)
        return perms

    def _include_item_to_cache_set(self, key:str, perm:RolePermission):
        add_item_if_set_exists = self._valkey.register_script(ADD_ITEM_IF_SET_EXISTS_LUA_SCRIPT)
        result = add_item_if_set_exists(keys=[key], args=[perm.id])

    def _include_cache_set(self, key: str, perms:Sequence[RolePermission]) -> None:
        if len(perms) == 0:
            return
        ttl = self._settings.ttl_seconds
        with self._valkey.pipeline(transaction=True) as pipe:
            pipe.sadd(key, *[p.id for p in perms])
            pipe.expire(key, ttl)
            for p in perms:
                p_key = self._ENTRY_CACHE_KEY_(p.id)
                pipe.hset(p_key, mapping=p.model_dump(exclude_none=True, exclude={'weight', 'name'}))
                pipe.expire(p_key, ttl)
            result = pipe.execute()

    def _list_perms_from_cache(self, key) -> Sequence[Permission]:
        args = []
        keys = [key]
        script = self._valkey.register_script(LIST_HITEMS_BY_SET_SCRIPT)
        rows = cast(list[list[str|bytes]], script(keys=keys, args=args))

        #odd items is key and even items is values
        #entries = [Permission.model_validate(dict(zip(row[::2], row[1::2]))) for row in rows if len(row) > 0]

        entries = [Permission.model_validate(entry) for entry in self._unserialize(rows)]
        return sorted(entries, key= lambda e: e.weight)

    def _unserialize(self, rows:list[list[str|bytes]]):
        decoded = self._decoded_response
        for row in rows:
            if len(row) == 0:
                continue
            entry = {}
            for k, v in zip(row[::2], row[1::2]):
                k = k if decoded else cast(bytes, k).decode('utf-8')
                v = v if decoded else cast(bytes, v).decode('utf-8')
                entry[k] = v            
            yield entry

    def _cache_item(self, key: str, perms: RolePermission) -> None:
        self._valkey.hset(key, mapping=perms.model_dump(exclude_none=True, exclude={'weight', 'name'}))
        self._valkey.expire(key, self._settings.ttl_seconds)

    def _entry(self, cached_item:dict)-> Permission:
        if self._decoded_response:
            return Permission.model_validate(cached_item)
        return Permission.model_validate({k.decode('utf-8'):v.decode('utf-8') for k, v in cached_item.items()})

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
    def _ENTRY_CACHE_KEY_(id) -> str:
        return f'permission:{id}'

    @staticmethod
    def _ENTRIES_CACHE_KEY_(role_id: int, resource_id: int) -> str:
        return f'role:{role_id}:resource:{resource_id}:permissions'
