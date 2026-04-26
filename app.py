"""Flask application factory and entry point."""

import secrets
from flask import Flask, jsonify, request, session, abort
from config import SECRET_KEY, DEBUG, THREADED
from auth import init_login
from routes import register_routes

CSRF_EXEMPT_PATHS = {"/api/chat", "/feedback"}


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["DEBUG"] = DEBUG
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    init_login(app)
    register_routes(app)

    @app.context_processor
    def inject_csrf_token():
        token = session.get("csrf_token")
        if not token:
            token = secrets.token_urlsafe(24)
            session["csrf_token"] = token
        return {"csrf_token": lambda: token}

    @app.before_request
    def csrf_protect():
        if request.method == "POST" and request.path not in CSRF_EXEMPT_PATHS:
            token = session.get("csrf_token")
            posted = request.form.get("csrf_token") or request.headers.get("X-CSRFToken")
            if not token or token != posted:
                abort(400)

    @app.errorhandler(400)
    def bad_request(_):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Bad request"}), 400
        return "Bad request", 400

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=DEBUG, threaded=THREADED)
