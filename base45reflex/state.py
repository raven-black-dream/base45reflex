import json
import pyrebase as pb
import re
import reflex as rx
import requests.exceptions

from rxconfig import ENVIRONMENT

from base45reflex.SQLModels import User, Workout
from pprint import pprint
from typing import Optional


config_path = "base45reflex/firebaseConfig.json"
config_data = json.load(open(config_path, 'r'))
firebase = pb.initialize_app(config_data)
auth = firebase.auth()


with rx.session() as session:
    dev_user = session.exec(User.select.where(User.id == 'XZtDPyiyebWPhCAXYJ8BKuaBJWg2')).first().dict()
    dev_user['date_of_birth'] = dev_user['date_of_birth'].isoformat()


class State(rx.State):
    """The app state."""
    user: Optional[dict] = dev_user if ENVIRONMENT == 'DEV' else None
    refresh_token: str = ''

    def logout(self):
        """Log out a user."""
        self.reset()
        return rx.redirect("/")

    def save_data(self, key, value):
        return rx.set_local_storage(key, value)

    def load_data(self):
        return rx.get_local_storage('refresh')

    @rx.var
    def get_user(self) -> dict:
        return self.user

    @rx.var
    def get_refresh_token(self) -> str:
        return self.refresh_token

    def refresh(self):
        """Get cookies and refresh IdToken"""
        user = auth.refresh(self.refresh_token)
        with rx.session() as session:
            user = session.exec(User.select.where(User.id == user['userId'])).first().dict()
            self.user = user

    def check_login(self):
        """Check if a user is logged in."""
        if not self.logged_in:
            try:
                self.refresh()
            except KeyError:
                return rx.redirect("/login")
            except requests.exceptions.HTTPError:
                return rx.redirect("/login")

    @rx.var
    def logged_in(self) -> bool:
        """Check if a user is logged in."""
        return self.user is not None


class LoginState(State):

    email: str = ''
    password: str = ''

    placeholder_email = 'Please enter you email address'
    placeholder_pass = 'Please enter your password'

    border_email: str = ''
    border_pass: str = ''

    button_name = 'Login'

    def get_login_email(self, email):
        self.email = email

    def get_login_pass(self, password):
        self.password = password

    def authenticate(self):
        try:
            user = auth.sign_in_with_email_and_password(self.email, self.password)
            self.refresh_token = user['refreshToken']
            self.save_data('refresh', self.refresh_token)
        except requests.exceptions.HTTPError as e:
            error = json.loads(e.strerror)
            return rx.window_alert(error['error']['message'])
        with rx.session() as session:
            user = session.exec(User.select.where(User.id == user['localId'])).first().dict()
            self.user = user
        return rx.redirect("/")

    def reload_page(self):
        self.email = ""
        self.password = ""
        self.button_name = "Login"
        self.border_email = ""
        self.border_pass = ""
        self.placeholder_email = "Please enter your email address"
        self.placeholder_pass = "Please enter you password"

    @rx.var
    def email_is_valid(self) -> bool:
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        if re.fullmatch(regex, self.email):
            return False
        else:
            return True


class DrawerState(State):

    show_left: bool = False

    def left(self):
        self.show_left = not self.show_left


