import reflex as rx
from ..SQLModels import Workout, WorkoutSet, WorkoutComment, UserClients, UserProgramHistory, ProgramDay
from ..state import State
from ..page_view import PageView
from typing import List


class WorkoutState(State):

    @rx.var
    def verify(self) -> bool:
        if not self.user:
            return False
        workout_list = [workout['id'] for workout in self.data]
        client_workouts = [workout['id'] for workout in self.client_data]
        workout_id = self.get_query_params().get("pid", "no pid")
        if workout_id == "no pid":
            return False
        else:
            workout_id = int(workout_id)
            return workout_id in workout_list or id in client_workouts

    @rx.var
    def data(self) -> List[dict]:
        if not self.user:
            return []
        with rx.session() as session:
            data = session.query(Workout).filter(Workout.user_id == self.user['id']).all()
            data = self.parse_data(data)
        return data

    @rx.var
    def client_data(self) -> List[dict]:
        if not self.user:
            return []
        with rx.session() as session:
            client_list = session.query(UserClients).filter(UserClients.user_id == self.user['id']).all()
            for client in client_list:
                client_workouts = session.query(Workout).filter(Workout.user_id == client.id)
                client_workouts = self.parse_data(data=client_workouts)
            return client_workouts

    @staticmethod
    def parse_data(self, data: List[Workout]):
        data = [workout.dict() for workout in data]
        for workout in data:
            workout['date'] = workout['date'].isoformat()
        return data

    @rx.var
    def workout_id(self):
        return self.get_query_params().get("pid", "no pid")


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

        ))
    ]).build()


def view_workout():
    return PageView([rx.cond(WorkoutState.verify, rx.text(WorkoutState.workout_id), rx.text('DUMB ASS'))]).build()


def update_workout():
    return PageView([rx.text(f"Update Workout {WorkoutState.workout_id} here")]).build()
