"""
__init__.py
-----------
Application factory. Keeps app creation testable (create_app("testing"))
and avoids circular imports by initializing extensions here and importing
blueprints lazily inside the factory function.
"""

import os
import logging
from flask import Flask, render_template
from app.config import config_map
from app.extensions import db, login_manager, migrate


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=os.path.join(root_dir, "templates"),
        static_folder=os.path.join(root_dir, "static"),
    )
    app.config.from_object(config_map.get(config_name, config_map["default"]))

    os.makedirs(app.instance_path, exist_ok=True)

    # --- Extensions ---
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # --- Blueprints ---
    from app.auth import auth_bp
    from app.routes import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # --- User loader ---
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- Error handlers ---
    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="Page not found"), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("error.html", code=500, message="Internal server error"), 500

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", code=403, message="Access forbidden"), 403

    # --- Logging ---
    if not app.debug and not app.testing:
        logging.basicConfig(level=logging.INFO)

    # --- Context processor (inject 'now' + current_user theme into all templates) ---
    from datetime import datetime

    @app.context_processor
    def inject_globals():
        return {"current_year": datetime.utcnow().year}

    return app
