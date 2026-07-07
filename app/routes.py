"""
routes.py
---------
Main application blueprint: dashboard, AI content planner, history,
categories, tags, saved prompts, profile, settings.
"""

from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import func

from app.extensions import db
from app.models import Content, Category, Tag, SavedPrompt, ActivityLog, History
from app.forms import ContentGenerateForm, CategoryForm, SavedPromptForm, ProfileForm
from app.utils import log_activity, parse_tags
from app.ai_engine import generate_content, AIEngineError, AITimeoutError, AIRateLimitError, AIConfigError

main_bp = Blueprint("main", __name__)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@main_bp.route("/")
@main_bp.route("/dashboard")
@login_required
def dashboard():
    total_content = current_user.contents.count()
    published = current_user.contents.filter_by(status="published").count()
    scheduled = current_user.contents.filter_by(status="scheduled").count()
    drafts = current_user.contents.filter_by(status="draft").count()

    recent_content = current_user.contents.order_by(Content.created_at.desc()).limit(5).all()

    # Simple 7-day activity chart data (count of generations per day)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    daily_counts = (
        db.session.query(func.date(Content.created_at), func.count(Content.id))
        .filter(Content.user_id == current_user.id, Content.created_at >= seven_days_ago)
        .group_by(func.date(Content.created_at))
        .all()
    )
    chart_labels = [d[0] for d in daily_counts]
    chart_values = [d[1] for d in daily_counts]

    stats = {
        "total": total_content,
        "published": published,
        "scheduled": scheduled,
        "drafts": drafts,
    }

    return render_template(
        "dashboard.html",
        stats=stats,
        recent_content=recent_content,
        chart_labels=chart_labels,
        chart_values=chart_values,
    )


# ---------------------------------------------------------------------------
# Content Planner (AI Generation)
# ---------------------------------------------------------------------------
@main_bp.route("/planner", methods=["GET", "POST"])
@login_required
def planner():
    form = ContentGenerateForm()
    form.category_id.choices = [(0, "-- No Category --")] + [
        (c.id, c.name) for c in current_user.categories.order_by(Category.name).all()
    ]

    if form.validate_on_submit():
        try:
            ai_output = generate_content(form.content_type.data, form.prompt_input.data)
        except AIConfigError as exc:
            flash(str(exc), "danger")
            return render_template("planner.html", form=form)
        except AITimeoutError as exc:
            flash(str(exc), "warning")
            return render_template("planner.html", form=form)
        except AIRateLimitError as exc:
            flash(str(exc), "warning")
            return render_template("planner.html", form=form)
        except AIEngineError as exc:
            flash(f"AI generation failed: {exc}", "danger")
            return render_template("planner.html", form=form)

        content = Content(
            title=form.title.data,
            content_type=form.content_type.data,
            prompt_input=form.prompt_input.data,
            ai_output=ai_output,
            status="draft",
            scheduled_date=form.scheduled_date.data,
            user_id=current_user.id,
            category_id=form.category_id.data or None,
        )

        tag_names = parse_tags(form.tags.data)
        for name in tag_names:
            tag = Tag.query.filter_by(name=name, user_id=current_user.id).first()
            if not tag:
                tag = Tag(name=name, user_id=current_user.id)
                db.session.add(tag)
            content.tags.append(tag)

        db.session.add(content)
        db.session.commit()

        db.session.add(History(content_id=content.id, action="generated", snapshot=ai_output))
        db.session.commit()

        log_activity(current_user.id, "content_generated", f"{form.content_type.data}: {form.title.data}")
        flash("Content generated successfully!", "success")
        return redirect(url_for("main.history"))

    return render_template("planner.html", form=form)


@main_bp.route("/api/generate", methods=["POST"])
@login_required
def api_generate():
    """AJAX endpoint used by planner.html for inline 'regenerate' without a full page reload."""
    data = request.get_json(silent=True) or {}
    content_type = data.get("content_type")
    prompt_input = data.get("prompt_input")

    if not content_type or not prompt_input:
        return jsonify({"error": "Missing content_type or prompt_input."}), 400

    try:
        ai_output = generate_content(content_type, prompt_input)
        return jsonify({"result": ai_output})
    except AIConfigError as exc:
        return jsonify({"error": str(exc)}), 400
    except AITimeoutError as exc:
        return jsonify({"error": str(exc)}), 504
    except AIRateLimitError as exc:
        return jsonify({"error": str(exc)}), 429
    except AIEngineError as exc:
        return jsonify({"error": str(exc)}), 502


# ---------------------------------------------------------------------------
# History (with search + pagination)
# ---------------------------------------------------------------------------
@main_bp.route("/history")
@login_required
def history():
    page = request.args.get("page", 1, type=int)
    query_text = request.args.get("q", "", type=str).strip()
    content_type = request.args.get("type", "", type=str)

    query = current_user.contents.order_by(Content.created_at.desc())
    if query_text:
        query = query.filter(Content.title.ilike(f"%{query_text}%"))
    if content_type:
        query = query.filter(Content.content_type == content_type)

    per_page = current_app.config.get("ITEMS_PER_PAGE", 10)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "history.html",
        pagination=pagination,
        contents=pagination.items,
        query_text=query_text,
        content_type=content_type,
    )


@main_bp.route("/content/<int:content_id>/delete", methods=["POST"])
@login_required
def delete_content(content_id):
    content = Content.query.filter_by(id=content_id, user_id=current_user.id).first_or_404()
    db.session.delete(content)
    db.session.commit()
    log_activity(current_user.id, "content_deleted", content.title)
    flash("Content deleted.", "info")
    return redirect(url_for("main.history"))


@main_bp.route("/content/<int:content_id>/status", methods=["POST"])
@login_required
def update_status(content_id):
    content = Content.query.filter_by(id=content_id, user_id=current_user.id).first_or_404()
    new_status = request.form.get("status")
    if new_status in ("draft", "scheduled", "published"):
        content.status = new_status
        db.session.commit()
        flash("Status updated.", "success")
    return redirect(url_for("main.history"))


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------
@main_bp.route("/categories", methods=["GET", "POST"])
@login_required
def categories():
    form = CategoryForm()
    if form.validate_on_submit():
        exists = Category.query.filter_by(name=form.name.data, user_id=current_user.id).first()
        if exists:
            flash("Category already exists.", "warning")
        else:
            cat = Category(name=form.name.data, color=form.color.data or "#6366f1", user_id=current_user.id)
            db.session.add(cat)
            db.session.commit()
            flash("Category created.", "success")
        return redirect(url_for("main.categories"))

    all_categories = current_user.categories.order_by(Category.name).all()
    return render_template("categories.html", form=form, categories=all_categories)


@main_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@login_required
def delete_category(category_id):
    cat = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
    db.session.delete(cat)
    db.session.commit()
    flash("Category deleted.", "info")
    return redirect(url_for("main.categories"))


# ---------------------------------------------------------------------------
# Saved Prompts
# ---------------------------------------------------------------------------
@main_bp.route("/saved-prompts", methods=["GET", "POST"])
@login_required
def saved_prompts():
    form = SavedPromptForm()
    if form.validate_on_submit():
        prompt = SavedPrompt(title=form.title.data, prompt_text=form.prompt_text.data, user_id=current_user.id)
        db.session.add(prompt)
        db.session.commit()
        flash("Prompt saved.", "success")
        return redirect(url_for("main.saved_prompts"))

    prompts = current_user.saved_prompts.order_by(SavedPrompt.created_at.desc()).all()
    return render_template("saved_prompts.html", form=form, prompts=prompts)


@main_bp.route("/saved-prompts/<int:prompt_id>/delete", methods=["POST"])
@login_required
def delete_saved_prompt(prompt_id):
    prompt = SavedPrompt.query.filter_by(id=prompt_id, user_id=current_user.id).first_or_404()
    db.session.delete(prompt)
    db.session.commit()
    flash("Prompt deleted.", "info")
    return redirect(url_for("main.saved_prompts"))


# ---------------------------------------------------------------------------
# Profile & Settings
# ---------------------------------------------------------------------------
@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.email = form.email.data
        current_user.avatar_url = form.avatar_url.data
        db.session.commit()
        log_activity(current_user.id, "profile_updated")
        flash("Profile updated.", "success")
        return redirect(url_for("main.profile"))

    recent_activity = current_user.activity_logs.order_by(ActivityLog.created_at.desc()).limit(10).all()
    return render_template("profile.html", form=form, recent_activity=recent_activity)


@main_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        current_user.dark_mode = request.form.get("dark_mode") == "on"
        db.session.commit()
        flash("Settings saved.", "success")
        return redirect(url_for("main.settings"))
    return render_template("settings.html")


@main_bp.route("/api/toggle-theme", methods=["POST"])
@login_required
def toggle_theme():
    current_user.dark_mode = not current_user.dark_mode
    db.session.commit()
    return jsonify({"dark_mode": current_user.dark_mode})
