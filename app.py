"""
app.py - Flask application factory and entry point
"""

from flask import Flask
from config import SECRET_KEY, DEBUG, THREADED
from auth import init_login
from routes import register_routes


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["DEBUG"] = DEBUG
    
    # Initialize login manager
    init_login(app)
    
    # Register routes
    register_routes(app)
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=DEBUG, threaded=THREADED)
