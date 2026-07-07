"""
forms.py
--------
Flask-WTF forms with server-side validation for every user-facing form.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, DateField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError
from app.models import User


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, message="Password must be at least 8 characters.")])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match.")]
    )

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Username already taken.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("Email already registered.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])


class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match.")]
    )


class ProfileForm(FlaskForm):
    full_name = StringField("Full Name", validators=[Optional(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    avatar_url = StringField("Avatar URL", validators=[Optional(), Length(max=255)])


class ContentGenerateForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    content_type = SelectField(
        "Type",
        choices=[
            ("idea", "Content Idea"),
            ("caption", "Caption"),
            ("seo_title", "SEO Title"),
            ("keyword", "Keyword Research"),
            ("script", "Video/Content Script"),
            ("calendar", "Content Calendar"),
            ("rewrite", "Rewrite Content"),
            ("improve", "Improve Writing"),
        ],
        validators=[DataRequired()],
    )
    prompt_input = TextAreaField("Details / Topic", validators=[DataRequired(), Length(max=4000)])
    category_id = SelectField("Category", coerce=int, validators=[Optional()])
    tags = StringField("Tags (comma separated)", validators=[Optional(), Length(max=255)])
    scheduled_date = DateField("Scheduled Date", validators=[Optional()])


class CategoryForm(FlaskForm):
    name = StringField("Category Name", validators=[DataRequired(), Length(max=80)])
    color = StringField("Color", validators=[Optional(), Length(max=20)])


class SavedPromptForm(FlaskForm):
    title = StringField("Prompt Title", validators=[DataRequired(), Length(max=150)])
    prompt_text = TextAreaField("Prompt Text", validators=[DataRequired(), Length(max=4000)])
