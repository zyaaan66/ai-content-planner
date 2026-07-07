"""
run.py
------
Local development entrypoint. In production, use a WSGI server
(gunicorn) pointing at `app:create_app()` -- see README for deployment.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.extensions import db

app = create_app(os.environ.get("FLASK_ENV", "development"))


@app.cli.command("init-db")
def init_db():
    """Usage: flask --app run.py init-db"""
    with app.app_context():
        db.create_all()
        print("Database tables created.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=app.config.get("DEBUG", True), port=int(os.environ.get("PORT", 5000)))
