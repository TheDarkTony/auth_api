from datetime import datetime

from core_contracts.workout import models
from core_contracts.metainfo import get_metainfo

from sqlalchemy import String, ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from repo_sqlalchemy.schema import Base, IntPK, TBL


class MuscleGroup(Base):
    __tablename__ = TBL.MUSCLE_GROUP.value

    id: Mapped[IntPK]
    name: Mapped[str|None] = mapped_column(String(get_metainfo(models.MuscleGroup, 'name').max_length), nullable=False)


class Exercise(Base):
    __tablename__ = TBL.EXERCISE.value

    id: Mapped[IntPK]
    name: Mapped[str] = mapped_column(String(get_metainfo(models.Exercise, 'name').max_length), nullable=False)
    description: Mapped[str] = mapped_column(String(get_metainfo(models.Exercise, 'description').max_length), nullable=False)
    muscle_group_id: Mapped[int|None] = mapped_column(ForeignKey(f"{TBL.MUSCLE_GROUP.value}.id"), nullable=True, index=True)


class Workout(Base):
    __tablename__ = TBL.WORKOUT.value

    id: Mapped[IntPK]
    athlete_identity_id: Mapped[int] = mapped_column(ForeignKey(f'{TBL.IDENTITY.value}.id'), index=True, nullable=False)
    coach_identity_id: Mapped[int|None] = mapped_column(ForeignKey(f'{TBL.IDENTITY.value}.id'), index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(get_metainfo(models.Exercise, 'description').max_length), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    status: Mapped[int] = mapped_column(Integer(), nullable=False)


class WorkoutExercise(Base):
    __tablename__ = TBL.WORKOUT_EXERCISES.value

    id: Mapped[IntPK]
    wo_id: Mapped[int] = mapped_column(ForeignKey(f'{TBL.WORKOUT.value}.id'), index=True, nullable=False)
    exr_id: Mapped[int] = mapped_column(ForeignKey(f'{TBL.EXERCISE.value}.id'), index=True, nullable=False)

    order: Mapped[int] = mapped_column(Integer(), nullable=False)
    status: Mapped[int] = mapped_column(Integer(), nullable=False)        # 0-planned, 1-inprogress, 2-completed
    
    mass: Mapped[int|None] = mapped_column(Integer(), nullable=True)      #(grams)
    reps: Mapped[int|None] = mapped_column(Integer(), nullable=True)      #(repetitions of the exercise)
    distance: Mapped[int|None] = mapped_column(Integer(), nullable=True)  #(meters)

    start_time: Mapped[datetime|None] = mapped_column(DateTime(timezone=False), nullable=True)
    end_time: Mapped[datetime|None] = mapped_column(DateTime(timezone=False), nullable=True)
