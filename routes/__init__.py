"""
routes/__init__.py - Route modules initialization
"""

def register_routes(app):
    """Register all route blueprints with the Flask app."""
    from routes.chat import chat_bp
    from routes.api import api_bp
    from routes.admin import admin_bp
    from routes.misc import misc_bp

    app.register_blueprint(chat_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(misc_bp)
