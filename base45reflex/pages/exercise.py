import pandas as pd
import reflex as rx
from ..page_view import PageView
from base45reflex.SQLModels import Exercise, ProgramSet, Program
from ..state import State
from typing import List, Dict


class ExerciseState(State):

    @rx.var
    def exercise_cards(self) -> List[dict]:
        with rx.session() as session:
            exercise_list = session.query(Exercise).all()
            results = session.query(ProgramSet).all()
            program_count = session.query(Program).count()

        exercises = [exercise.dict() for exercise in exercise_list]
        exercises = {exercise['id']: exercise['name'] for exercise in exercises}
        results = [result.dict() for result in results]
        for result in results:
            result['exercise_name'] = exercises[result['exercise_id']]

        df = pd.DataFrame(results)
        df = df.groupby(['exercise_name', 'min_reps', 'max_reps']).agg({'id': 'count'}).reset_index()
        df = df.rename(columns={'id': 'count'})
        df['rep_range'] = df['min_reps'].astype(str) + '-' + df['max_reps'].astype(str)
        df = df.drop(columns=['min_reps', 'max_reps'])
        df['percent'] = round((df['count'] / program_count) * 100, 2)
        df = df.sort_values(by=['exercise_name', 'count'], ascending=False)
        cards = []
        for exercise in exercise_list:
            temp = df[df['exercise_name'] == exercise.name].copy()
            temp = temp.sort_values(by=['percent'], ascending=False)
            if temp.empty:
                cards.append({'header': exercise.name, 'body': 'No data'})
                continue
            temp['percent'] = temp['percent'].astype(str) + '%'
            temp = temp[['rep_range', 'percent']]
            temp = temp.values.tolist()
            data = {'header': exercise.name,
                    'body': temp}
            cards.append(data)

        return cards


def exercise_list():
    return PageView(
        [
            rx.heading("Exercises", font_size="2em"),
            rx.foreach(
                ExerciseState.exercise_cards,
                lambda card:
                rx.cond(
                    card['body'] != 'No data',
                    rx.card(header=card['header'],
                            body=rx.data_table(data=card['body'], columns=['Rep Range', 'Percent'],
                                               bg_color="#262626", color="#aaaaaa"),
                            footer=rx.text("Percent of programs that include this exercise at this rep range"),
                            bg_color="#262626",
                            color="#aaaaaa",
                            width="25%"
                            ),
                    rx.card(header=card['header'], body=rx.center(rx.text("No data")),
                            footer=rx.text("Percent of programs that include this exercise at this rep range"),
                            bg_color="#262626",
                            color="#aaaaaa",
                            width="25%")

                )

            )]
    ).build()


def create_exercise():
    pass
