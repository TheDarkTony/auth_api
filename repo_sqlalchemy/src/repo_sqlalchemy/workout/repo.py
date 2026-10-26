from typing import Any, Sequence

from sqlalchemy import select, and_, Row
from sqlalchemy.sql.expression import ColumnExpressionArgument
from sqlalchemy.orm import InstrumentedAttribute

from core_contracts.base import PagginationArguments
from core_contracts.workout import models
from core_contracts.workout.repositories import IMuscleGroupRepository, IExerciseRepository

from repo_sqlalchemy.schema import BaseRepo, SeanceManager
from repo_sqlalchemy.workout import entities

DEFAULT_BATCH_SIZE = 5

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
            batch_size = DEFAULT_BATCH_SIZE
        return batch_size


    @property
    def _batch_filter(self) -> ColumnExpressionArgument[bool]:
        if self._direction < 0:
            return self._cursor_ref < self._cursor
        else:
            return self._cursor_ref > self._cursor

    def use_filter(self, filter: ColumnExpressionArgument[bool]):
        self._predicates.append(filter)


class MuscleGroupRepository(BaseRepo[entities.MuscleGroup, models.MuscleGroup], IMuscleGroupRepository):

    def __init__(self, seance_manager: SeanceManager) -> None:
        super().__init__(entities.MuscleGroup, models.MuscleGroup, seance_manager)

    def list(self, predicate: dict[str, Any]) -> Sequence[models.MuscleGroup]:

        pagginator = _CursorPaginationBuilder(predicate, entities.MuscleGroup.id)
        for k, v in predicate.items():
            if v is None:
                continue

            if k == models.MuscleGroupFields.NAME:
                pagginator.use_filter(entities.MuscleGroup.name == v)

        stmt = (
            select(entities.MuscleGroup)
            .where(pagginator.predicate)
            .limit(pagginator.batch_size)
            .order_by(entities.MuscleGroup.id)
        )

        seance = self._seance()
        entries: Sequence[Row[entities.MuscleGroup]]
        with seance.begin():
            entries = seance.execute(stmt).all()

        return [models.MuscleGroup.model_validate(e, from_attributes=True) for e in entries]


class ExerciseRepository(BaseRepo[entities.Exercise, models.Exercise], IExerciseRepository):

    def __init__(self, seance_manager: SeanceManager) -> None:
        super().__init__(entities.Exercise, models.Exercise, seance_manager)

    
    def list(self, predicate: dict[str, Any]) -> Sequence[models.Exercise]:

        pagginator = _CursorPaginationBuilder(predicate, entities.Exercise.id)
        for k, v in predicate.items():
            if v is None:
                continue

            if k == models.ExerciseFields.NAME:
                pagginator.use_filter(entities.Exercise.name == v)
            if k == models.ExerciseFields.MUSCLE_GROUP_ID:
                pagginator.use_filter(entities.Exercise.muscle_group_id == v)

        seance = self._seance()
        entries: Sequence[Row[entities.Exercise]]

        stmt = (
            select(entities.Exercise)
            .where(pagginator.predicate)
            .limit(pagginator.batch_size)
            .order_by(entities.Exercise.id)
        )
        
        with seance.begin():
            entries = seance.execute(stmt).all()

        return [models.Exercise.model_validate(e, from_attributes=True) for e in entries]
