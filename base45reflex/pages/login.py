import reflex as rx
from ..page_view import PageView
from ..state import LoginState


@rx.page('/login', on_load=LoginState.reload_page)
def login():
    comp_list = [
        rx.heading("Welcome to Base 45"),
        rx.vstack(
            rx.form(
                rx.vstack(
                    rx.form_control(
                        rx.input(placeholder=LoginState.placeholder_email, on_blur=LoginState.get_login_email),
                        rx.cond(LoginState.email_is_valid,
                                rx.form_error_message("Invalid Email Address"),
                                rx.form_helper_text('Valid Email')),
                        is_invalid=LoginState.email_is_valid,
                        is_required=True
                    ),
                    rx.password(placeholder=LoginState.placeholder_pass, on_change=LoginState.get_login_pass),
                    rx.button(LoginState.button_name, type_='submit')
                ),
                on_submit=LoginState.authenticate
            ),
            width="100%",
            height="15rem",
            justify_content="center",
            spacing="1.35rem"
        ),
    ]
    return PageView(comp_list).build()