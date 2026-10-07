from typing import Any, Sequence

from sqlalchemy import select, and_, Row
from sqlalchemy.sql.expression import ColumnExpressionArgument
from sqlalchemy.orm import InstrumentedAttribute

from core_contracts import issues
from core_contracts.base import PagginationArguments, AccessArguments, AccessMode
from core_contracts.identity import models
from core_contracts.identity.repositories import IIdentityRepository, IUserRepository

from repo_sqlalchemy.schema import BaseRepo, SeanceManager
from repo_sqlalchemy.identity import entities
from repo_sqlalchemy.permission import entities as perm_entities


class _CursorPaginationBuilder:

    def __init__(self, arguments: dict[str, Any], cursor_ref: InstrumentedAttribute[int]):
        self._arguments: dict[str, Any] = arguments
        self._cursor_ref: InstrumentedAttribute[int] = cursor_ref
        self._predicates: list[ColumnExpressionArgument[bool]] = []

        direction = 1
        cursor = arguments.get(PagginationArguments.NEXT_CURSOR)
        
        if cursor is None:
            cursor = arguments.get(PagginationArguments.PREV_CURSOR, 0)
            if cursor > 0:
                direction = -1

        self._cursor: int = int(cursor)
        self._direction: int = direction

    @property
    def predicate(self):
        if len(self._predicates) == 0:
            return self._batch_filter
        else:
            return and_(self._batch_filter, *self._predicates)

    @property
    def batch_size(self) -> int:
        batch_size = self._arguments.get(PagginationArguments.BATCH_SIZE, 0)
        if batch_size <= 0:
            batch_size = 20
        return batch_size


    @property
    def _batch_filter(self) -> ColumnExpressionArgument[bool]:
        if self._direction < 0:
            return self._cursor_ref < self._cursor
        else:
            return self._cursor_ref > self._cursor

    def use_filter(self, filter: ColumnExpressionArgument[bool]):
        self._predicates.append(filter)


class IdentityRepository(BaseRepo[entities.Identity, models.Identity], IIdentityRepository):

    def __init__(self, seance_manager: SeanceManager) -> None:
        super().__init__(entities.Identity, models.Identity, seance_manager)

    def list(self, predicate: dict[str, Any]) -> Sequence[models.IdentityItem]:

        pagginator = _CursorPaginationBuilder(predicate, entities.Identity.id)

        for k, v in predicate.items():
            if v is None:
                continue

            if k == models.IdentityFields.FNAME:
                pagginator.use_filter(entities.Identity.fname == v)
            elif k == models.IdentityFields.LNAME:
                pagginator.use_filter(entities.Identity.lname == v)
            elif k == models.IdentityFields.EMAIL:
                pagginator.use_filter(entities.Identity.email == v)

        only_ = predicate.get(AccessArguments.MODE)
        current_identity_id = predicate.get(AccessArguments.CURRENT_IDENTITY, 0)
        if only_ == AccessMode.own:
            pagginator.use_filter(entities.Identity.id == current_identity_id)
        elif only_ == AccessMode.nonown:
            pagginator.use_filter(entities.Identity.id != current_identity_id)

        stmt = (
            select(entities.Identity.id, entities.Identity.fname, entities.Identity.lname)
            .where(pagginator.predicate)
            .limit(pagginator.batch_size)
            .order_by(entities.Identity.id)
        )

        seance = self._seance()
        entries: Sequence[Row[tuple[int, str|None, str|None]]]
        with seance.begin():
            entries = seance.execute(stmt).all()

        return [models.IdentityItem(id=id, fname=fname, lname=lname) for id, fname, lname in entries]


    def update_and_attach_user(self, identity:models.Identity, user: models.UserSubject) -> tuple[models.Identity, models.User]:
        
        usr = self._to_entity_obj(user, entities.User)
        
        seance = self._seance()
        with seance.begin():
            entry: entities.Identity|None = seance.get(self._entity, identity.id)
            if entry is None:
                stmt = select(entities.Identity).where(entities.Identity.id == identity.id)
                entry = seance.scalar(stmt)

            if entry is None:
                raise issues.NotFoundEntryIssue('Identity entry is not located')

            self._model_obj_to_entry(identity, entry)
            seance.add(usr)

        return self._to_model_obj(entry, models.Identity), self._to_model_obj(usr, models.User)


    def fetch_by_email(self, email: str) -> models.Identity | None:

        seance = self._seance()
        entry = next(
            (obj for obj in seance.identity_map.values() 
                if isinstance(obj, entities.Identity) and obj.email == email)
            , None
        )

        if entry is not None:
            return self._to_model_obj(entry, models.Identity)

        stmt = select(entities.Identity).where(entities.Identity.email == email)
        with seance.begin():
            entry = seance.scalar(stmt)

        if entry is None:
            return None

        return self._to_model_obj(entry, models.Identity)


class UserRepository(BaseRepo[entities.User, models.User], IUserRepository):

    def __init__(self, seance_manager: SeanceManager) -> None:
        super().__init__(entities.User, models.User, seance_manager)

    def fetch_active_by_usrname(self, usrname: str) -> models.User | None:

        usr: entities.User|None = None
        seance = self._seance()

        stmt = (select(entities.User)
                .join(entities.Identity, entities.User.identity_id == entities.Identity.id)
                .where(entities.User.username == usrname and entities.Identity.is_activated == True))

        with seance.begin():
            usr = seance.scalar(stmt)

        if usr is None:
            return None

        return self._to_model_obj(usr, models.User)


    def fetch_by_usrname(self, usrname: str) -> models.User | None:

        usr: entities.User|None = None
        seance = self._seance()

        usr = next(
            (obj for obj in seance.identity_map.values()
                if isinstance(obj, entities.User) and obj.username == usrname)
            , None
        )

        if usr is not None:
            return self._to_model_obj(usr, models.User)

        stmt = select(entities.User).where(entities.User.username == usrname)
        with seance.begin():
            entry = seance.scalar(stmt)

        if entry is None:
            return entry

        return self._to_model_obj(entry, models.User)


    def list(self, predicate: dict[str, Any]) -> Sequence[models.User]:

        pagginator = _CursorPaginationBuilder(predicate, entities.User.id)
        for k, v in predicate.items():
            if v is None:
                continue

            if k == models.UserFields.USERNAME:
                pagginator.use_filter(entities.User.username == v)
            elif k == models.UserFields.ROLE_ID:
                pagginator.use_filter(entities.User.role_id == v)
            elif k == models.UserFields.IDENTITY_ID:
                pagginator.use_filter(entities.User.identity_id == v)

        #only active BY default
        pagginator.use_filter(entities.User.deleted_date == None)

        only_ = predicate.get(AccessArguments.MODE)
        current_user_id = predicate.get(AccessArguments.CURRENT_USR, 0)
        if only_ == AccessMode.own:
            pagginator.use_filter(entities.User.id == current_user_id)
        elif only_ == AccessMode.nonown:
            pagginator.use_filter(entities.User.id != current_user_id)

        stmt = (
            select(entities.User)
            .where(pagginator.predicate)
            .limit(pagginator.batch_size)
            .order_by(entities.User.id)
        )

        entries: Sequence[entities.User]
        seance = self._seance()
        with seance.begin():
            entries = seance.scalars(stmt).all()

        return [self._to_model_obj(e, models.User) for e in entries]
