"""
models.py
---------
SQLAlchemy ORM models: User, Content, History, Category, Tag, SavedPrompt,
ActivityLog. Relationships are declared explicitly for clarity and to keep
queries efficient (avoiding N+1 via backrefs / lazy='joined' where sensible).
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


# ---------------------------------------------------------------------------
# Association table: many-to-many between Content and Tag
# ---------------------------------------------------------------------------
content_tags = db.Table(
    "content_tags",
    db.Column("content_id", db.Integer, db.ForeignKey("content.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    avatar_url = db.Column(db.String(255))
    dark_mode = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    contents = db.relationship("Content", backref="author", lazy="dynamic", cascade="all, delete-orphan")
    categories = db.relationship("Category", backref="owner", lazy="dynamic", cascade="all, delete-orphan")
    tags = db.relationship("Tag", backref="owner", lazy="dynamic", cascade="all, delete-orphan")
    saved_prompts = db.relationship("SavedPrompt", backref="owner", lazy="dynamic", cascade="all, delete-orphan")
    activity_logs = db.relationship("ActivityLog", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self):
        return f"<User {self.username}>"


class Category(db.Model):
    __tablename__ = "category"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    color = db.Column(db.String(20), default="#6366f1")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    contents = db.relationship("Content", backref="category", lazy="dynamic")

    __table_args__ = (db.UniqueConstraint("name", "user_id", name="uq_category_name_user"),)


class Tag(db.Model):
    __tablename__ = "tag"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    __table_args__ = (db.UniqueConstraint("name", "user_id", name="uq_tag_name_user"),)


class Content(db.Model):
    __tablename__ = "content"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  # idea, caption, seo_title, keyword, script, calendar, rewrite, improve
    prompt_input = db.Column(db.Text)
    ai_output = db.Column(db.Text)
    status = db.Column(db.String(20), default="draft")  # draft, scheduled, published
    scheduled_date = db.Column(db.Date, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tags = db.relationship("Tag", secondary=content_tags, backref=db.backref("contents", lazy="dynamic"))
    history_entries = db.relationship("History", backref="content", lazy="dynamic", cascade="all, delete-orphan")


class History(db.Model):
    """Immutable audit trail of every AI generation performed on a Content item."""

    __tablename__ = "history"

    id = db.Column(db.Integer, primary_key=True)
    content_id = db.Column(db.Integer, db.ForeignKey("content.id"), nullable=False)
    action = db.Column(db.String(50))  # generated, rewritten, improved
    snapshot = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SavedPrompt(db.Model):
    __tablename__ = "saved_prompt"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    prompt_text = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ActivityLog(db.Model):
    __tablename__ = "activity_log"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    action = db.Column(db.String(120), nullable=False)
    details = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
