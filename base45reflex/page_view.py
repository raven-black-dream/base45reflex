import reflex as rx
from base45reflex.state import DrawerState


class PageView:
    def __init__(self, components: list) -> None:
        self.drawer_toggle = rx.button(rx.icon(tag='hamburger'), on_click=DrawerState.left, bg='#1a472a',
                                       color='#ffffff')
        self.components = components

        self.drawer = self.compose_drawer()

        self.stack = rx.vstack(
            rx.box(
                self.drawer_toggle,
                self.drawer,
                width='100%',
                height='5rem',
                display='flex',
                justify_content='right',

            ),
            height='100vh',
            width="100%",
            padding='2rem',
            display='flex',
            align_items="center",
            spacing='1rem',
            bg='#1c1c1c'

        )
        super().__init__()

    def build(self) -> rx.Component:
        for component in self.components:
            self.stack.children.append(component)
        return self.stack

    def compose_drawer(self):
        if DrawerState.check_login:
            return rx.drawer(
                    rx.drawer_overlay(
                        rx.drawer_content(
                            rx.drawer_header("Base 45 Training"),
                            rx.drawer_body(
                                rx.vstack(
                                    rx.link(rx.button('Profile', bg='#1a472a', color='#ffffff'), href='/', button=True),
                                    rx.link(rx.button('Workouts', bg='#1a472a', color='#ffffff'), href='/workouts', button=True),
                                    rx.link(rx.button('Record Workout', bg='#1a472a', color='#ffffff'), href='/record', button=True),
                                    rx.link(rx.button('View Current Program', bg='#1a472a', color='#ffffff'), href='/', button=True),
                                    rx.link(rx.button('Edit Current Program', bg='#1a472a', color='#ffffff'), href='/', button=True),
                                    rx.link(rx.button("Create New Program", bg='#1a472a', color='#ffffff'), href='/', button=True),
                                    rx.link(rx.button("View Program List", bg='#1a472a', color='#ffffff'), href='/', button=True)
                                )


                            )
                        , bg='#1c1c1c', color='#ffffff')
                    ),
                    placement='left',
                    is_open=DrawerState.show_left,
                    on_overlay_click=DrawerState.left,
                )
        else:
            return rx.drawer(
                rx.drawer_overlay(
                    rx.drawer_content(
                        rx.drawer_header("Base 45 Training"),
                        rx.drawer_body(
                            rx.vstack(
                                rx.link(rx.button('Login'), href='/login', button=True)
                            )
                        )
                    )
                ),
                placement='left',
                is_open=DrawerState.show_left,
                on_overlay_click=DrawerState.left
            )

