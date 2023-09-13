from datetime import date
import reflex as rx
import pandas as pd
from ..page_view import PageView
import plotly.graph_objects as go
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
    def metrics(self) -> Dict[str, Dict[str, Dict[str, float]]]:
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
        df['prev'] = df.groupby(['day_name', 'exercise', 'metric'])['value'].shift(1).fillna(0)
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
                    metrics[day_name][exercise][rec['metric']] = round(rec["value"], 2)
                    metrics[day_name][exercise][f"{rec['metric']}_prev"] = round(rec['prev'], 2)
                    var = temp[(temp['exercise'] == exercise) & (temp['metric'] == rec['metric'])].copy()
                    metrics[day_name][exercise][f'{rec["metric"]}_var'] = round(var['value'].var(), 2)
                    metrics[day_name][exercise][f'{rec["metric"]}_unit'] = rec['unit']
        return metrics

    @rx.var
    def indicators(self) -> Dict[str, Dict[str, go.Figure]]:
        data = self.metrics
        indicators = {}
        for day_name in data.keys():
            ex_metrics = data[day_name]
            indicators[day_name] = {}
            for exercise in ex_metrics:
                metrics = ex_metrics[exercise]
                unit = metrics['TotalLoad_unit']
                ref = metrics['TotalLoad_prev']
                value = metrics['TotalLoad']
                var = metrics['TotalLoad_var']
                fig = go.Figure()
                fig.add_trace(
                    go.Indicator(
                        mode="number+delta",
                        value=value,
                        number={'suffix': f" {unit}"},
                        delta={'reference': ref, 'relative': True, 'position': "top"},
                        domain={'row': 0, 'column': 0},
                        title={'text': "Total Load"}
                    )
                )
                fig.add_trace(
                    go.Indicator(
                        mode="number+delta",
                        value=var,
                        domain={'row': 1, 'column': 0},
                        title={'text': "Total Load Variance"}
                    )
                )
                ref = metrics['AvgRPE_prev']
                value = metrics['AvgRPE']
                var = metrics['AvgRPE_var']
                fig.add_trace(
                    go.Indicator(
                        mode="number+delta",
                        value=value,
                        number={},
                        delta={'reference': ref, 'relative': True, 'position': "top"},
                        domain={'row': 0, 'column': 1},
                        title={'text': "Avg RPE"}
                    )
                )
                fig.add_trace(
                    go.Indicator(
                        mode="number+delta",
                        value=var,
                        domain={'row': 1, 'column': 1},
                        title={'text': "Avg RPE Variance"}
                    )
                )
                ref = metrics['AvgRepsPerSet_prev']
                value = metrics['AvgRepsPerSet']
                var = metrics['AvgRepsPerSet_var']
                fig.add_trace(
                    go.Indicator(
                        mode="number+delta",
                        value=value,
                        number={'suffix': ' reps'},
                        delta={'reference': ref, 'relative': True, 'position': "top"},
                        domain={'row': 0, 'column': 2},
                        title={'text': "Reps Per Set"}
                    )
                )
                fig.add_trace(
                    go.Indicator(
                        mode="number+delta",
                        value=var,
                        domain={'row': 1, 'column': 2},
                        title={'text': "Reps Per Set Variance"}
                    )
                )
                indicators[day_name][exercise] = fig

        return indicators



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
    figs = LandingState.indicators[day_name]
    return rx.tab_panel(
        rx.foreach(
            figs,
            lambda x: rx.plotly(data=x[1], layout=dict(grid={'rows': 2, 'columns': 3, 'pattern': "independent"},
                                                       paper_bgcolor='#262626'))
        ),

        width='100%'
    )

