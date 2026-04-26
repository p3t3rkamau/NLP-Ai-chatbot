"""
auth.py - User authentication and login management
"""

from flask_login import UserMixin, LoginManager

login_manager = LoginManager()


class User(UserMixin):
    """User model for Flask-Login."""

    def __init__(self, username: str, password: str):
        self.id = username
        self.password = password


# Hardcoded users (in production, use a database)
USERS = {
    "user1": User("user1", "password1"),
    "user2": User("user2", "password2"),
}


def init_login(app) -> None:
    """Initialize login manager for the Flask app."""
    login_manager.init_app(app)
    login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    """Load user by ID."""
    return USERS.get(user_id)


def authenticate_user(username: str, password: str) -> User | None:
    """Authenticate user credentials."""
    user = USERS.get(username)
    return user if user and user.password == password else None
