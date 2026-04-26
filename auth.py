"""User authentication and login management."""

from flask_login import UserMixin, LoginManager
from werkzeug.security import check_password_hash, generate_password_hash
from config import LOGIN_VIEW, ADMIN_USERNAME, ADMIN_PASSWORD

login_manager = LoginManager()


class User(UserMixin):
    """User model for Flask-Login."""

    def __init__(self, username: str, password_hash: str):
        self.id = username
        self.password_hash = password_hash


USERS = {
    ADMIN_USERNAME: User(ADMIN_USERNAME, generate_password_hash(ADMIN_PASSWORD)),
}


def init_login(app) -> None:
    """Initialize login manager for the Flask app."""
    login_manager.init_app(app)
    login_manager.login_view = LOGIN_VIEW


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    """Load user by ID from in-memory users."""
    return USERS.get(user_id)


def authenticate_user(username: str, password: str) -> User | None:
    """Authenticate user credentials."""
    user = USERS.get(username)
    if not user:
        return None
    return user if check_password_hash(user.password_hash, password) else None
