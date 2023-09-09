import reflex as rx

ENVIRONMENT = 'DEV'


class BasereflexConfig(rx.Config):
    pass


if not ENVIRONMENT == 'DEV':
    config = BasereflexConfig(
        app_name="base45reflex",
        db_url="sqlite:///reflex.db",
    )

else:
    config = BasereflexConfig(
        app_name="base45reflex",
        db_url="sqlite:///reflex_dev.db",
    )
