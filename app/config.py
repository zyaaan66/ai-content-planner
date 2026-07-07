"""
config.py
---------
Central configuration. All secrets are pulled from environment variables
(via python-dotenv) -- NEVER hard-code API keys or secrets here.
"""

import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # AI
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    GEMINI_TIMEOUT = int(os.environ.get("GEMINI_TIMEOUT", "30"))

    # Pagination
    ITEMS_PER_PAGE = int(os.environ.get("ITEMS_PER_PAGE", "10"))


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'app.db')}"
    )


class ProductionConfig(BaseConfig):
    DEBUG = False
    # Render/Railway/Vercel provide DATABASE_URL for Postgres.
    # SQLAlchemy 1.4+ requires 'postgresql://' not 'postgres://'.
    _db_url = os.environ.get("DATABASE_URL", "")
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url or f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'app.db')}"


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
