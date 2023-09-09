from datetime import date
import reflex as rx
import pandas as pd
from ..page_view import PageView
from base45reflex.SQLModels import UserProgramHistory, ProgramDay, Workout, WorkoutSet, UserWorkoutMetrics, Exercise
from ..state import State
import sqlmodel as sqlm
from typing import List, Dict

from pprint import pprint


class Calendar(rx.Component):
    library = 'react-event-calendar'
    tag = 'EventCalendar'
    month: rx.Var[int] = date.today().month
    year: rx.Var[int] = date.today().year


    @classmethod
    def get_controlled_triggers(cls) -> dict[str, rx.Var]:
        return {
        "on_day_click": rx.EVENT_ARG,
        "on_event_click": rx.EVENT_ARG,
        "on_event_mouse_over": rx.EVENT_ARG,
        "on_event_mouse_out": rx.EVENT_ARG}


calendar = Calendar.create


def index() -> rx.Component:
    comp_list = [rx.heading(f"Welcome to Base 45 Training!", font_size="2em"),
                ]
    return PageView(comp_list).build()


class LandingState(State):

    @rx.var
    def user_program(self) -> List[dict]:
        with rx.session() as session:
            statement = UserProgramHistory.select.where(sqlm.and_(UserProgramHistory.user_id == self.user['id'],
                                                                  UserProgramHistory.current == 1))
            current_program = session.exec(statement).first()
            program_days = session.query(ProgramDay).filter(ProgramDay.program_id == current_program.program_id).all()
            return [day.dict() for day in program_days]

    @rx.var
    def program_start_date(self) -> date:
        with rx.session() as session:
            statement = UserProgramHistory.select.where(sqlm.and_(UserProgramHistory.user_id == self.user['id'],
                                                                  UserProgramHistory.current == 1))
            current_program = session.exec(statement).first()
            return current_program.start_date.isoformat()

    @rx.var
    def metrics(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        data = []
        with rx.session() as session:
            workout_stmt = Workout.select.where(sqlm.and_(
                Workout.user_id == self.user['id'],
                Workout.date >= self.program_start_date
            ))
            workout_list = session.exec(workout_stmt).all()

            for workout in workout_list:
                day_name = workout.day.name
                sets = workout.workout_sets
                for ex_set in sets:
                    ex_metrics = ex_set.metrics
                    for metric in ex_metrics:
                        data.append({'day_name': day_name, 'exercise': metric.exercise,
                                     'metric': metric.metric, 'value': metric.value,
                                     'unit': 'lbs' if metric.unit_id == 1 else None, 'date': metric.date})
        df = pd.DataFrame.from_records(data)
        df.sort_values('date', ascending=True, inplace=True)
        df['diff'] = df.groupby(['day_name', 'exercise', 'metric'])['value'].diff().fillna(0)
        metrics = {}
        for day_name in df['day_name'].unique():
            metrics[day_name] = {}
            temp = df[df['day_name'] == day_name].copy()
            dates = temp['date'].unique()
            dates.sort()
            most_recent = dates[-1]
            for exercise in temp['exercise'].unique():
                metrics[day_name][exercise] = {}
                ex_metrics = temp[(temp['exercise'] == exercise) & (temp['date'] == most_recent)].to_records()
                for rec in ex_metrics:
                    metrics[day_name][exercise][rec['metric']] = f'{round(rec["value"], 2)} {rec["unit"]}'\
                        if rec['unit'] is not None else f'{round(rec["value"], 2)}'
                    metrics[day_name][exercise][f"{rec['metric']}_diff"] = f"{round(rec['diff'], 2)}"
                    var = temp[(temp['exercise'] == exercise) & (temp['metric'] == rec['metric'])].copy()
                    metrics[day_name][exercise][f'{rec["metric"]}_var'] = f"{round(var['value'].var(), 2)} {rec['unit']}"\
                        if rec['unit'] is not None else f'{round(var["value"].var(), 2)}'
        return metrics



    @rx.var
    def day_names(self) -> List[str]:
        names = [day['name'] for day in self.user_program]
        names.sort()
        return names

    @rx.var
    def first_name(self):
        return self.user['first_name']


def landing() -> rx.Component:
    comp_list = [rx.heading(f"Welcome {LandingState.first_name}", color='#aaaaaa', font_size="2em"),
                 # rx.box(calendar()),
                 rx.divider(),
                 rx.center(rx.tabs(
                     rx.tab_list(rx.foreach(
                         LandingState.day_names,
                         lambda x: build_tab_list(x)
                     )),
                     rx.tab_panels(rx.foreach(
                         LandingState.day_names,
                         lambda x: build_metric_block(x)
                     )),
                     width='75%', is_lazy=True, variant='solid-rounded', 
                 ),
                 width='100%'),
                 rx.divider(),
                 rx.center(

                 )

                 ]
    return PageView(comp_list).build()


def build_tab_list(day_name: str):
    return rx.tab(day_name)


def build_metric_block(day_name: str):
    data = LandingState.metrics[day_name]
    return rx.tab_panel(
        rx.foreach(
            data,
            lambda x: build_metrics(x)
        ),

        width='100%'
    )


def build_metrics(ex_metrics: List):
    return rx.box(rx.vstack(
        rx.text(ex_metrics[0]),
            rx.responsive_grid(
            rx.stat(
                rx.stat_label('Total Load'),
                rx.stat_number(ex_metrics[1]['TotalLoad']),
                rx.stat_help_text(ex_metrics[1]['TotalLoad_diff'])
            ),
            rx.stat(
                rx.stat_label('Average RPE'),
                rx.stat_number(ex_metrics[1]['AvgRPE']),
                rx.stat_help_text(ex_metrics[1]['AvgRPE_diff'])
            ),
            rx.stat(
                rx.stat_label('Reps per Set'),
                rx.stat_number(ex_metrics[1]['AvgRepsPerSet']),
                rx.stat_help_text(ex_metrics[1]['AvgRepsPerSet_diff'])
                ),
            rx.stat(
                rx.stat_label('Load Variance'),
                rx.stat_number(ex_metrics[1]['TotalLoad_var']),
            ),
            rx.stat(
                rx.stat_label('RPE Variance'),
                rx.stat_number(ex_metrics[1]['AvgRPE_var']),
            ),
            rx.stat(
                rx.stat_label('Rep Variance'),
                rx.stat_number(ex_metrics[1]['AvgRepsPerSet_var'])
            ), width='100%', columns=[3], spacing="4"
        ), rx.container(),
        align_items='center'
        ), border_color='black', border_radius='lg', border_width="thin", bg='darkgray')