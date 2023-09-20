import pandas as pd
import reflex as rx
from ..SQLModels import Workout, WorkoutSet, WorkoutComment, UserClients, UserProgramHistory, ProgramDay
from ..state import State
from ..page_view import PageView
from typing import Any, Dict, List, Union


class WorkoutState(State):

    @rx.var
    def verify(self) -> bool:
        if not self.user:
            return False
        workout_id = self.get_query_params().get("pid", "no pid")
        if workout_id == "no pid":
            return False
        else:
            workout_id = int(workout_id)
            return workout_id in self.workout_list or workout_id in self.client_workouts

    @rx.var
    def workout_list(self):
        with rx.session() as session:
            statement = Workout.select.where(Workout.user_id == self.user['id'])
            workouts = session.exec(statement).all()
            return [workout.id for workout in workouts]

    @rx.var
    def client_workout_list(self):
        with rx.session() as session:
            client_list = session.query(UserClients).filter(UserClients.user_id == self.user['id']).all()
            for client in client_list:
                client_workouts = session.query(Workout).filter(Workout.user_id == client.client_id).all()
            return [workout.id for workout in client_workouts]

    @rx.var
    def workout_id(self):
        return self.get_query_params().get("pid", "no pid")

    @rx.var
    def get_workout_data(self) -> Dict[str, Any]:
        if self.workout_id == "no pid":
            return {}
        with rx.session() as session:
            statement = Workout.select.where(Workout.id == self.workout_id)
            workout = session.exec(statement).first()
            data = {
                'id': workout.id,
                'date': workout.date,
                'day': workout.day.name,
                'deload': workout.deload,
                'complete': workout.complete
            }
            return data

    @rx.var
    def get_workout_sets(self) -> pd.DataFrame:
        if self.workout_id == "no pid":
            return pd.DataFrame()
        with rx.session() as session:
            statement = WorkoutSet.select.where(WorkoutSet.workout_id == self.workout_id)
            sets = session.exec(statement).all()
            return pd.DataFrame.from_records([{
                'id': ex_set.id,
                'exercise': ex_set.exercise.name,
                'weight': ex_set.weight,
                'unit': ex_set.workout_set_unit.name,
                'total_reps': ex_set.reps,
                'reps_per_ser': ex_set.reps / ex_set.num_sets,
                'num_sets': ex_set.num_sets,
                'avg_rpe': ex_set.avg_rpe,
            } for ex_set in sets])

    @rx.var
    def get_workout_comments(self) -> List[dict]:
        if self.workout_id == "no pid":
            return []
        with rx.session() as session:
            statement = WorkoutComment.select.where(WorkoutComment.workout_id == self.workout_id)
            comments = session.exec(statement).all()
            return [{
                'id': comment.id,
                'comment': comment.comment
            } for comment in comments]

    @rx.var
    def all_workout_data(self) -> List[dict]:
        with rx.session() as session:
            statement = Workout.select.where(Workout.user_id == self.user['id']).order_by(Workout.date.desc())
            workouts = session.exec(statement).fetchmany(42)
            return [{
                'id': workout.id,
                'date': workout.date,
                'day': workout.day.name,
                'deload': workout.deload,
                'complete': workout.complete
            } for workout in workouts]


class WorkoutFormState(WorkoutState):
    form_data: dict
    program_day: str
    items: List[dict]
    new_item: dict

    def submit(self, form_data: dict):
        self.form_data = form_data

    def add_item(self):
        self.items += [self.new_item]

    def remove_item(self, item):
        self.items = [i for i in self.items if i is not item]


def record_workout():
    return PageView([
        rx.heading("Record Workout"),
        rx.form(rx.vstack(

        ), on_submit=WorkoutFormState.submit
        )
    ]).build()


def list_workouts():
    return PageView(
        [
            rx.heading("Workouts", font_size="2em", color="#aaaaaa"),
                rx.foreach(
                    WorkoutState.all_workout_data,
                    lambda workout: rx.cond(
                        workout['complete'],
                        rx.cond(
                            workout['deload'],
                            rx.hstack(
                                rx.link(
                                    rx.button(f"{workout['day']} - {workout['date']}", bg_color='#1a472a',
                                              color='#aaaaaa'),
                                    href=f"/workout/{workout['id']}", button=True,),
                                rx.badge("Complete", color='green'),
                                rx.badge("Deload", color="purple"),
                                bg_color='#262626', color='#aaaaaa'
                                ),
                            rx.hstack(
                                rx.link(
                                    rx.button(f"{workout['day']} - {workout['date']}", bg_color='#1a472a',
                                              color='#aaaaaa'),
                                    href=f"/workout/{workout['id']}", button=True, ),
                                rx.badge("Complete", color='green'),
                                bg_color='#262626', color='#aaaaaa'
                            )
                        ),
                        rx.cond(
                            workout['deload'],
                            rx.hstack(
                                rx.link(
                                    rx.button(f"{workout['day']} - {workout['date']}", bg_color='#1a472a',
                                              color='#aaaaaa'),
                                    href=f"/workout/{workout['id']}", button=True, ),
                                rx.badge("Deload", color="purple"),
                                bg_color='#262626', color='#aaaaaa', button=True
                            ),
                            rx.hstack(
                                rx.link(
                                    rx.button(f"{workout['day']} - {workout['date']}", bg_color='#1a472a',
                                              color='#aaaaaa'),
                                    href=f"/workout/{workout['id']}", button=True, ),
                                bg_color='#262626', color='#aaaaaa'
                            )
                        )
                    )
                ),

        ]
    ).build()


def view_workout():
    return PageView([
        rx.cond(WorkoutState.verify,
                rx.vstack(
                    rx.heading(f"Program Day: {WorkoutState.get_workout_data['day']}",
                               font_size="2em", color="#aaaaaa"),
                    rx.card(
                        header=rx.heading("Sets", font_size="1.5em", color="#aaaaaa"),
                        body=rx.data_table(
                            data=WorkoutState.get_workout_sets,
                        ),
                        bg_color='#262626', color='#aaaaaa'
                    ),
                    rx.card(
                        header=rx.heading("Comments", font_size="1.5em", color="#aaaaaa"),
                        body=rx.foreach(
                            WorkoutState.get_workout_comments,
                            lambda comment: rx.text(comment['comment'], color='#aaaaaa')
                        ),
                        bg_color='#262626', color='#aaaaaa'

                    )

                ),
                rx.text('DUMB ASS', color='#aaaaaa'))
    ]).build()


def update_workout():
    return PageView([rx.text(f"Update Workout {WorkoutState.workout_id} here")]).build()
