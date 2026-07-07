"""
auth.py
-------
Authentication blueprint: register, login, logout, forgot/reset password.

Note on "Forgot Password": a real production deployment needs a transactional
email provider (SendGrid/Mailgun/SES) to send reset links. That is an external
paid service the app can't invent credentials for, so this implementation
generates a signed reset token and prints/logs the reset link to the console
(via flash message in DEBUG) instead of emailing it. Swapping in real email
sending later only requires editing the `send_reset_email` function below.
"""

from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from app.extensions import db
from app.models import User
from app.forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from app.utils import log_activity

auth_bp = Blueprint("auth", __name__)


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def send_reset_email(user: User) -> str:
    """Generates a reset link. Wire this up to a real email provider in production."""
    token = _serializer().dumps(user.email, salt="password-reset")
    reset_url = url_for("auth.reset_password", token=token, _external=True)
    current_app.logger.info(f"[Password Reset] Link for {user.email}: {reset_url}")
    return reset_url


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        log_activity(user.id, "account_created", "User registered")
        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            log_activity(user.id, "login", "User logged in")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))
        flash("Invalid email or password.", "danger")

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    log_activity(current_user.id, "logout", "User logged out")
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            reset_url = send_reset_email(user)
            if current_app.debug:
                flash(f"Debug mode - reset link: {reset_url}", "info")
        # Always show the same message to avoid leaking which emails are registered.
        flash("If that email exists, a reset link has been sent.", "info")
        return redirect(url_for("auth.login"))

    return render_template("forgot_password.html", form=form)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = _serializer().loads(token, salt="password-reset", max_age=3600)
    except SignatureExpired:
        flash("Reset link expired. Please request a new one.", "danger")
        return redirect(url_for("auth.forgot_password"))
    except BadSignature:
        flash("Invalid reset link.", "danger")
        return redirect(url_for("auth.forgot_password"))

    user = User.query.filter_by(email=email).first_or_404()
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        log_activity(user.id, "password_reset", "Password reset via email link")
        flash("Password updated. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", form=form)
