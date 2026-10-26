from abc import abstractmethod
from typing import Sequence, Any

from core_contracts.base import IRepository, AccessMode
from core_contracts.workout.models import MuscleGroup, Exercise, Workout, WorkoutExercise
from core_contracts.workout.models import WorkoutSubject, WorkoutExerciseSubject, MuscleGroupSubject



class IMuscleGroupRepository(IRepository[MuscleGroup]):

    @abstractmethod
    def list(self, predicate: dict[str, Any]) -> Sequence[MuscleGroup]:
        raise NotImplementedError


class IExerciseRepository(IRepository[Exercise]):

    @abstractmethod
    def list(self, predicate: dict[str, Any]) -> Sequence[Exercise]:
        raise NotImplementedError
