import pandas as pd
import reflex as rx
from ..SQLModels import Workout, WorkoutSet, WorkoutComment, UserClients, UserProgramHistory, ProgramDay, Exercise
import sqlmodel as sqlm
from ..state import State
from ..page_view import PageView
from typing import Any, Dict, List, Union, TypedDict
from numbers import Number


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

    @rx.var
    def user_program(self) -> Dict[str, Any]:
        with rx.session() as session:
            statement = UserProgramHistory.select.where(sqlm.and_(UserProgramHistory.user_id == self.user['id'],
                                                                  UserProgramHistory.current == 1))
            current_program = session.exec(statement).first()
            program = {
                'start_date': current_program.start_date,
                'end_date': current_program.end_date,
                'program': current_program.history_program.dict(),
                'program_days': {
                    day.name: [{
                        'exercise': ex_set.exercise.name,
                        'exercise_id': ex_set.exercise_id,
                        'num_sets': ex_set.num_sets,
                        'min_reps': ex_set.min_reps,
                        'max_reps': ex_set.max_reps,
                        'avg_rpe': ex_set.avg_rpe,
                        'amrap': ex_set.amrap,
                        'myoreps': ex_set.myoreps,
                    } for ex_set in day.day_sets]
                    for day in current_program.history_program.program_days
                },
                'predictions': [{
                    'day_name': pred.program_day.name,
                    'exercise': pred.exercise.name,
                    'weight': pred.value,
                    'unit': pred.unit.name
                } for pred in current_program.predictions],

            }
            return program

    @rx.var
    def day_names(self) -> List[str]:
        names = list(self.user_program['program_days'].keys())
        names.sort()
        return names

    @rx.var
    def program_days(self) -> Dict[str, List[Dict[str, Any]]]:
        return self.user_program['program_days']


class DayChooserState(WorkoutState):
    days: List[Dict[str, Any]]
    selected_day: str

    @rx.var
    def days(self) -> List[str]:
        days = ['Custom']
        days.extend(self.day_names)
        return days

    def select_day(self, day: str):
        self.selected_day = day

    def submit(self):
        return rx.redirect(f"/record/{self.selected_day}")


def choose_day():
    return PageView([
        rx.heading("Choose Day", font_size="2em", color="#aaaaaa"),
        rx.select(
            DayChooserState.days,
            placeholder="Select a day",
            on_change=DayChooserState.select_day,
            color_scheme='green',
        ),
        rx.button("Submit", on_click=DayChooserState.submit, color_scheme='green')
    ]).build()


class WorkoutFormState(WorkoutState):
    form_data: dict
    # items: Dict[str, List[Dict[str, any]]]
    new_item: dict

    def submit(self, form_data: dict):
        self.form_data = form_data

    def add_item(self):
        self.items += [self.new_item]

    def remove_item(self, item):
        self.items = [i for i in self.items if i is not item]

    @rx.var
    def exercise_list(self) -> List[str]:
        statement = Exercise.select
        with rx.session() as session:
            exercises = session.exec(statement).all()
            return [ex.name for ex in exercises]

    @rx.var
    def day_name(self) -> str:
        return self.get_query_params().get("day_name", "no day")

    @rx.var
    def day(self) -> List[Dict[str, any]]:
        if self.day_name == "no day":
            return [{}]
        elif self.day_name == "Custom":
            return [{}]
        else:
            return self.program_days[self.day_name]

    @rx.var
    def items(self) -> List[Dict[str, str]]:
        preds = [pred for pred in self.user_program['predictions'] if pred['day_name'] == self.day_name]
        items = []
        if self.day == [{}]:
            return [{
                'exercise_name': '',
                'input_id_reps': '',
                'input_id_weight': '',
                'input_id_rpe': '',
                'reps': "0",
                'weight': "0",
                'unit': '',
                'rpe': "0.0"
            }]
        for item in self.day:
            exercise_name = item['exercise'] if not item['myoreps'] else f"{item['exercise']}-myoreps"
            exercise_pred = [exercise for exercise in preds if exercise['exercise'] == item['exercise']][0]
            for i in range(item['num_sets']):
                if i + 1 == item['num_sets'] and item['amrap']:
                    items.append({
                        'exercise_name': exercise_name,
                        'input_id_reps': f"{item['exercise']}_i_reps",
                        'input_id_weight': f"{item['exercise']}_i_weight",
                        'input_id_rpe': f"{item['exercise']}_i_rpe",
                        'reps': str(item['min_reps']),
                        'weight': str(exercise_pred['weight']),
                        'unit': exercise_pred['unit'],
                        'rpe': "10.0"
                    }

                    )
                else:
                    items.append(
                        {
                            'exercise_name': exercise_name,
                            'input_id_reps': f"{item['exercise']}_i_reps",
                            'input_id_weight': f"{item['exercise']}_i_weight",
                            'input_id_rpe': f"{item['exercise']}_i_rpe",
                            'reps': str(item['min_reps']),
                            'weight': str(exercise_pred['weight']),
                            'unit': exercise_pred['unit'],
                            'rpe': str(item['avg_rpe'])
                        }
                    )

        return items


def record_workout():
    return PageView([
        rx.heading("Record Workout", color='#aaaaaa', font_size="2em"),
        rx.center(rx.form(
            rx.vstack(
                rx.hstack(
                    rx.box(rx.text("Exercise"), width='20%', bg_color='#1a472a', color='#ffffff',
                           border_radius="md"),
                    rx.box(rx.text("Reps"), width='20%', bg_color='#1a472a', color='#ffffff',
                           border_radius="md"),
                    rx.box(rx.text("Weight"), width='20%', bg_color='#1a472a', color='#ffffff',
                           border_radius="md"),
                    rx.box(rx.text("RPE"), width='20%', bg_color='#1a472a', color='#ffffff',
                           border_radius="md"),
                    width='100%'
                ),
                rx.foreach(
                    WorkoutFormState.items,
                    lambda item: rx.hstack(
                        rx.box(rx.text(item['exercise_name']), width='20%', bg_color='#1a472a',
                               color='#ffffff', border_radius="md"),
                        rx.input(value=item['reps'], id=item["input_id_reps"], size='sm', width='20%'),
                        rx.input(value=item['weight'], input_mode='decimal',
                                 id=item["input_id_weight"], size='sm', width='20%'),
                        rx.input(value=item['rpe'], input_mode='decimal',
                                 id=item["input_id_rpe"], size='sm', width='20%'),
                        width='100%'


                    )
                )
            ),

            rx.button("Submit", type_="submit", color_scheme='green'),
            on_submit=WorkoutFormState.submit,
        ))
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
                                href=f"/workout/{workout['id']}", button=True, ),
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
