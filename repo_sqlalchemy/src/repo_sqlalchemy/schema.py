from enum import Enum
from typing import Iterable, Type, Annotated, Protocol

from sqlalchemy import create_engine, select, Engine, Integer, Boolean
from sqlalchemy.orm import Session, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.orm.util import identity_key

from pydantic import BaseModel

from core_contracts.metainfo import DataclassModel
from core_contracts import issues


class TBL(Enum):
    ROLE = 'roles'
    APPLICATION_RESOURCE = 'application_resources'
    ROLE_PERMISSION = 'roles_permissions'
    IDENTITY = 'identities'
    USER = 'users'
    TEMP_TOKEN = 'temp_tokens'
    EVENTS_LOG = 'events_log'


IntPK = Annotated[int, mapped_column(Integer, primary_key=True, autoincrement=True)]
BoolFlag = Annotated[bool, mapped_column(Boolean)]


class Base(DeclarativeBase): ...


class IntIdentifiableModel(DataclassModel, Protocol):
    id:int


class IntIdentifiableEntity(Protocol):
    id: Mapped[IntPK]


class ZeroPKFilteredSession(Session):

    def add(self, instance: object, _warn: bool = True) -> None:
        self._strip_zero_pk(instance)
        return super().add(instance, _warn)


    def add_all(self, instances: Iterable[object]) -> None:
        items = [self._strip_zero_pk(item) for item in instances]
        return super().add_all(items)


    def _strip_zero_pk(self, instance) -> object:
        if not hasattr(instance, 'id') or not instance.id:
            setattr(instance, 'id', None)

        return instance


class SeanceManager:

    def __init__(self, engine: Engine, scoped: bool) -> None:
        self.__engine: Engine = engine

        self.__scoped: bool = scoped
        self.__disposed: bool = False
        self.__seances: list[Session] = []

    def __del__(self):
        self.dispose()

    def get_seance(self) -> Session:
        if self.__disposed:
            raise issues.ResourceDisposedIssue("DB seance is disposed")

        if self.__scoped:
            if len(self.__seances) == 0:
                seance = ZeroPKFilteredSession(self.__engine, autobegin=False, expire_on_commit=False)
                self.__seances.append(seance)

            return self.__seances[0]

        seance = ZeroPKFilteredSession(self.__engine, autobegin=False, expire_on_commit=False)
        self.__seances.append(seance)

        return seance


    def dispose(self):
        if self.__disposed:
            return None

        for item in self.__seances:
            item.close()

        self.__disposed = True


class Schema:

    def __init__(self, seance_manager: SeanceManager )  -> None:
        self.__seance_manager: SeanceManager = seance_manager
        self._disposed: bool = False

    def dispose(self):
        self.__seance_manager.dispose()

    def _seance(self) -> Session:
        return self.__seance_manager.get_seance()


class BaseRepo[TEntity: IntIdentifiableEntity, TModel: IntIdentifiableModel](Schema):

    def __init__(self, entity: Type[TEntity], model:Type[TModel], seance_manager: SeanceManager) -> None:
        super().__init__(seance_manager)
        self._data_cls: Type[TModel] = model
        self._entity: Type[TEntity] = entity


    def dispose(self):
        super().dispose()

    def fetch_by_id(self, id: int) -> TModel|None:

        seance = self._seance()
        entry = seance.identity_map.get(identity_key(class_=self._entity, ident=(id,)))
        if entry is not None:
            return self._to_model_obj(entry, self._data_cls)

        stmt = select(self._entity).where(self._entity.id == id)

        with seance.begin():
            entry = seance.scalar(stmt)

        if entry is None:
            return None
        
        return self._to_model_obj(entry, self._data_cls)


    def delete(self, id: int) -> None:

        seance = self._seance()
        entry: TEntity|None = seance.identity_map.get(identity_key(class_=self._entity, ident=(id,)))
        
        with seance.begin():
            if entry is None:
                stmt = select(self._entity).where(self._entity.id == id)
                entry = seance.scalar(stmt)

            if entry is None:
                raise issues.NotFoundEntryIssue(f'{self._entity.__name__} entry is not located')

            seance.delete(entry)        


    def add(self, model: TModel) -> TModel:

        entry: TEntity | None = None
        seance = self._seance()
        with seance.begin():
            entry = self._to_entity_obj(model, self._entity)
            seance.add(entry)

        return self._to_model_obj(entry, self._data_cls)


    def edit(self, id: int, model: TModel) -> TModel:

        seance = self._seance()
        entry: TEntity|None = seance.identity_map.get(identity_key(class_=self._entity, ident=(id,)))

        with seance.begin():
            if entry is None:
                stmt = select(self._entity).where(self._entity.id == model.id)
                entry = seance.scalar(stmt)

            if entry is None:
                raise issues.NotFoundEntryIssue(f'{self._entity.__name__} entry is not located')

            self._model_obj_to_entry(model, entry)

        return self._to_model_obj(entry, self._data_cls)


    def save(self, model: TModel) -> TModel:

        edit_mode = hasattr(model, 'id') and model.id > 0
        if edit_mode:
            return self.edit(model.id, model)
        else:
            return self.add(model)


    def _to_model_obj[M:DataclassModel|BaseModel](self, entry: IntIdentifiableEntity, model: Type[M]) -> M:

        if issubclass(model, BaseModel):
            obj = model.model_validate(entry, from_attributes=True)
            return obj

        fields = model.__dataclass_fields__
        args = {
            prop: getattr(entry, prop)
            for prop in fields
            if hasattr(entry, prop)
        }

        obj = model(**args)
        return obj


    def _to_entity_obj[E:IntIdentifiableEntity](self, model:DataclassModel, entity: Type[E]) -> E:

        if isinstance(model, BaseModel):
            args = model.model_dump()
            entry = entity(**args)
            entry.id = getattr(model, 'id', 0)
            return entry

        fields = model.__dataclass_fields__
        args = {
            f: getattr(model, f)
            for f in fields
        }

        entry = entity(**args)
        entry.id = getattr(model, 'id', 0)

        return entry


    def _model_obj_to_entry(self, obj: TModel, entry: TEntity):

        if issubclass(self._data_cls, BaseModel):
            for k, v in self._data_cls.model_fields.items():
                if hasattr(entry, k):
                    setattr(entry, k, getattr(obj, k))
            return

        fields = self._data_cls.__dataclass_fields__
        for f in fields:
            if hasattr(entry, f):
                setattr(entry, f, getattr(obj, f))
