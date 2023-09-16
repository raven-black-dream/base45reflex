import reflex as rx
from ..SQLModels import Workout, WorkoutSet, WorkoutComment, UserClients, UserProgramHistory, Program
from ..state import State
from ..page_view import PageView
from typing import List
import sqlmodel as sqlm


class ProgramState(State):
    @rx.var
    def user_programs(self) -> List[dict]:
        with rx.session() as session:
            statement = Program.select.where(sqlm.or_(Program.public == True, Program.author == self.user['id']))
            program_list = session.exec(statement)
            return [program.dict() for program in program_list]
        
    @rx.var
    def program_names(self) -> List[str]:
        names = [program['name'] for program in self.user_programs]
        names.sort()
        return names


def view_program_list():
    comp_list = [rx.heading(f"Program List", color='#aaaaaa', font_size="2em"),
                 rx.divider(),
                 build_program_block(),
                 rx.divider(),
                 ]
    return PageView(comp_list).build()

def build_program_block():
    return rx.foreach(
        ProgramState.user_programs,
        lambda x: rx.vstack(
            rx.text(x["name"], font_size='2em', color='#aaaaaa'),
            rx.text("Author ID: " + x["author"], font_size='1em', color='#aaaaaa'),
            rx.text("Weeks: " + x["length_in_weeks"], font_size='1em', color='#aaaaaa'),
            rx.text(rx.cond(x["public"], "Publicly Visible", "Private Program"), font_size='1em', color='#aaaaaa'),
        )
    )
