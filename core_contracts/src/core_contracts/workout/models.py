from enum import IntEnum
from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, StringConstraints, model_serializer, Field

from core_contracts.metainfo import FieldLength


class ExerciseEnum(IntEnum):
    planned = 0
    inprogress = 1
    completed = 2


class MuscleGroupSubject(BaseModel):
    name: Annotated[str, StringConstraints(max_length=FieldLength.l_100)]


class MuscleGroup(MuscleGroupSubject):
    id: int


class ExerciseSubject(BaseModel):
    name: Annotated[str, StringConstraints(max_length=FieldLength.l_100)]
    description: Annotated[str, StringConstraints(max_length=FieldLength.l_100)]
    muscle_group_id: int|None


class Exercise(ExerciseSubject):
    id: int


class WorkoutSubject(BaseModel):
    athlete_identity_id: int
    coach_identity_id: int|None
    description: Annotated[str, StringConstraints(max_length=FieldLength.l_100)]
    date: datetime


class Workout(WorkoutSubject):
    id: int


class WorkoutExerciseSubject(BaseModel):
    wo_id: int
    exr_id: int

    order: int
    status: int         # 0-planned, 1-inprogress, 2-completed
    
    mass: int|None      #(grams)
    reps: int|None      #(repetitions of the exercise)
    distance: int|None  #(meters)
    start_time: datetime|None
    end_time: datetime|None

    duration: int|None = None   #(calculated: end_time - start_time  or null) int seconds

    def model_post_init(self, context: Any) -> None:
        if self.start_time is None or self.end_time is None:
            return
        self.duration = (self.end_time - self.start_time).seconds


class WorkoutExercise(WorkoutExerciseSubject):
    id: int
