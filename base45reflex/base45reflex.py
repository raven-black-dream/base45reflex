"""Welcome to Reflex! This file outlines the steps to create a basic app."""

from .pages import exercise, index, login, program, trainer, workout
from .state import State
import reflex as rx

from rxconfig import config
from rxconfig import ENVIRONMENT


if not ENVIRONMENT == "DEV":
    # Add state and page to the app.
    app = rx.App(state=State, stylesheets=[
        "https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css",
    ])
    app.add_page(index.index, route='/', on_load=State.check_login())
    app.add_page(login.login)
    app.add_page(workout.choose_day, route='/record', on_load=State.check_login())
    app.add_page(workout.record_workout, route='/record/[day_name]', on_load=State.check_login())
    app.add_page(workout.view_workout, route='/workout/[pid]', on_load=State.check_login())
    app.add_page(workout.update_workout, route='workout/update/[pid]', on_load=State.check_login())
    app.add_page(exercise.exercise_list, route='/exercises', on_load=State.check_login())
    app.compile()

else:
    app = rx.App(state=State, stylesheets=[
        "styles.css",
    ],)
    app.add_page(index.landing, route='/')
    app.add_page(login.login)
    app.add_page(workout.choose_day, route='/record')
    app.add_page(workout.record_workout, route='/record/[day_name]')
    app.add_page(workout.view_workout, route='/workout/[pid]')
    app.add_page(workout.list_workouts, route='/workouts')
    app.add_page(workout.update_workout, route='workout/update/[pid]')
    app.add_page(exercise.exercise_list, route='/exercises')
    app.add_page(exercise.create_exercise, route='/exercises/create')
    app.compile()
