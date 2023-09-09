import datetime
from datetime import date
import reflex as rx
from sqlmodel import Field, Column, Date, Relationship
from typing import Optional, List


class ExerciseType(rx.Model, table=True):
    __tablename__ = "exercise_type"

    id: int = Field(primary_key=True)
    name: int


class Exercise(rx.Model, table=True):
    __tablename__ = "exercises"

    id: int = Field(primary_key=True)
    name: str
    weight_step: float
    type: int = Field(foreign_key='exercise_type.id')

    sets: List["WorkoutSet"] = Relationship(back_populates='exercise')

class InputFeatures(rx.Model, table=True):
    __tablename__ = "input_features"

    id: int = Field(primary_key=True)
    reps: int
    reps_max: int
    reps_min: int
    rpe: float
    set_number: int


class Prediction(rx.Model, table=True):
    __tablename__ = "predictions"

    id: int = Field(primary_key=True)
    input_id: int = Field(foreign_key='input_features.id')
    exercise: int = Field(foreign_key='exercises.id')
    model: str
    prediction: int
    user_agrees: bool
    user_suggestion: Optional[int]


class Program(rx.Model, table=True):
    __tablename__ = "programs"

    id: int = Field(primary_key=True)
    author: str = Field(foreign_key='users.id')
    name: str
    length_in_weeks: int
    public: bool

    user_histories: List["UserProgramHistory"] = Relationship(back_populates='history_program')
    program_days: List['ProgramDay'] = Relationship(back_populates='day_program')


class ProgramDay(rx.Model, table=True):
    __tablename__ = "program_days"

    id: int = Field(primary_key=True)
    program_id: int = Field(foreign_key='programs.id')
    day_program: "Program" = Relationship(back_populates='program_days')
    name: str

    day_sets: List["ProgramSet"] = Relationship(back_populates='program_day')
    workouts: List['Workout'] = Relationship(back_populates='day')


class ProgramSet(rx.Model, table=True):
    __tablename__ = "program_sets"

    id: int = Field(primary_key=True)
    day_id: int = Field(foreign_key='program_days.id')
    program_day: ProgramDay = Relationship(back_populates='day_sets')
    exercise_order: int
    exercise_id: int = Field(foreign_key='exercises.id')
    min_reps: int
    max_reps: int
    avg_rpe: float
    num_sets: int
    myoreps: bool
    amrap: bool


class User(rx.Model, table=True):
    __tablename__ = "users"

    id: str = Field(primary_key=True)
    first_name: str
    last_name: str
    gender: str
    # model: str
    date_of_birth: Optional[date] = Field(default=None, sa_column=Column('date_of_birth', Date))
    role: str

    workout_metrics: List['UserWorkoutMetrics'] = Relationship(back_populates='user')
    program_history: List['UserProgramHistory'] = Relationship(back_populates='program_user')


class UserClients(rx.Model, table=True):
    __tablename__ = 'user_clients'

    id: int = Field(primary_key=True)
    user_id: str = Field(foreign_key='users.id')
    client_id: str = Field(foreign_key='users.id')


class UserProgramHistory(rx.Model, table=True):
    __tablename__ = "user_program_history"

    id: int = Field(primary_key=True)
    user_id: str = Field(foreign_key='users.id')
    current: bool
    program_id: int = Field(foreign_key='programs.id')
    history_program: Program = Relationship(back_populates='user_histories')
    start_date: date
    end_date: date

    program_user: User = Relationship(back_populates='program_history')
    predictions: List["UserProgramHistoryPrediction"] = Relationship(back_populates='program')


class UserProgramHistoryPrediction(rx.Model, table=True):
    __tablename__ = "program_history_prediction"

    id: int = Field(primary_key=True)
    user_program_history_id: int = Field(foreign_key='user_program_history.id')
    program: UserProgramHistory = Relationship(back_populates="predictions")
    program_day_id: int = Field(foreign_key='program_days.id')
    exercise_id: int
    unit_id: int
    value: float


class UserWeightHistory(rx.Model, table=True):
    __tablename__ = 'user_weight_history'

    id: int = Field(primary_key=True)
    user_id: str = Field(foreign_key='users.id')
    date: date
    unit: int
    value: float


class UnitType(rx.Model, table=True):
    __tablename__ = 'unit_types'

    id: int = Field(primary_key=True)
    name: str


class UnitConversion(rx.Model, table=True):
    __tablename__ = 'unit_conversion'

    id: int = Field(primary_key=True)
    first_unit: int = Field(foreign_key='unit_types.id')
    second_unit: int = Field(foreign_key='unit_types.id')
    factor: float


class Workout(rx.Model, table=True):
    __tablename__ = 'workouts'

    id: int = Field(primary_key=True)
    complete: bool
    date: date
    deload: bool
    program_day: Optional[int] = Field(foreign_key='program_days.id')
    day: ProgramDay = Relationship(back_populates='workouts')
    type: str
    user_id: str = Field(foreign_key='users.id')

    workout_sets: List["WorkoutSet"] = Relationship(back_populates='workout')


class WorkoutSet(rx.Model, table=True):
    __tablename__ = 'workout_sets'

    id: int = Field(primary_key=True)
    workout_id: int = Field(foreign_key='workouts.id')
    workout: Workout = Relationship(back_populates="workout_sets")
    exercise_id: int = Field(foreign_key='exercises.id')
    exercise: Exercise = Relationship(back_populates='sets')
    reps: int
    avg_rpe: float
    num_sets: int
    set_order: int
    weight: float
    unit_id: int

    metrics: List["UserWorkoutMetrics"] = Relationship(back_populates='ex_set')



class WorkoutComment(rx.Model, table=True):
    __tablename__ = "workout_comments"

    id: int = Field(primary_key=True)
    workout_id: int = Field(foreign_key='workouts.id')
    comment: str


class UserWorkoutMetrics(rx.Model, table=True):
    __tablename__ = 'user_workout_metrics'

    id: int = Field(primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    user: User = Relationship(back_populates='')
    set_id: int = Field(foreign_key="workout_sets.id")
    ex_set: WorkoutSet = Relationship(back_populates="metrics")
    unit_id: Optional[int] = Field(foreign_key="unit_types.id")
    date: datetime.date
    exercise: str
    metric: str
    value: float
