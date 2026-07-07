# AI Content Planner

**An AI-powered content planning platform.** Generate ideas, captions, SEO titles, keywords, scripts, and full content calendars using Google's Gemini API — with a real dashboard, history, categories, tags, and saved prompts behind proper authentication.

!\[Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python\&logoColor=white)
!\[Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask\&logoColor=white)
!\[SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00)
!\[Gemini API](https://img.shields.io/badge/Google\_Gemini-API-8E75B2?logo=googlegemini\&logoColor=white)
!\[License](https://img.shields.io/badge/License-MIT-green)
!\[Status](https://img.shields.io/badge/Status-Active-success)

\---

## Overview

AI Content Planner is a full-stack SaaS-style web app built to demonstrate production-grade backend architecture, clean database design, and real third-party AI integration — not a toy CRUD demo. It's built with a modular Flask application factory, a 7-table relational schema, server-side validated forms, and a dark-themed glassmorphic UI.

> \*\*Live Demo:\*\* deploy your own copy in minutes — see \[Deployment](#deployment) below.

\---

## Features

|Area|Details|
|-|-|
|**AI Content Generation**|Content ideas, captions, SEO titles, keyword research, scripts, 7-day content calendars, rewriting, and writing improvement — all via Gemini API|
|**Dashboard**|Live stats (total / published / scheduled / drafts), recent content feed, 7-day activity chart|
|**Content Planner**|Full form-based generator with live AJAX preview before saving|
|**History**|Search by title, filter by content type, paginated table, inline status updates, delete|
|**Categories \& Tags**|Custom categories with color labels; free-form tags per content item|
|**Saved Prompts**|Save and reuse your best prompt templates|
|**Authentication**|Register, login, logout, forgot/reset password (signed time-limited tokens)|
|**Profile \& Settings**|Edit profile, dark/light mode toggle, activity log|
|**Error Handling**|Graceful handling of 404/500/403, AI timeouts, AI rate limits, invalid API key, DB errors|
|**UI**|Glassmorphism, dark theme by default, responsive sidebar, skeleton loaders, toast notifications|

\---

## Tech Stack

**Backend:** Python, Flask, SQLAlchemy, Flask-Login, Flask-WTF, Flask-Migrate
**Database:** SQLite (development) → PostgreSQL (production)
**Frontend:** Jinja2, Tailwind CSS (CDN), vanilla JavaScript
**AI:** Google Gemini API (`generateContent` REST endpoint)
**Auth:** Flask-Login sessions + Werkzeug password hashing + itsdangerous signed tokens
**Deployment:** Render / Railway / Vercel-compatible (Gunicorn WSGI)

\---

## Architecture

```
Browser
  │
  ▼
Flask App Factory (app/\_\_init\_\_.py)
  ├── auth.py        → Blueprint: register / login / logout / password reset
  ├── routes.py       → Blueprint: dashboard / planner / history / categories / prompts / profile / settings
  ├── ai\_engine.py    → Isolated Gemini API client (swappable provider layer)
  ├── models.py       → SQLAlchemy ORM (7 tables)
  ├── forms.py        → Flask-WTF validated forms
  └── extensions.py   → db / login\_manager / migrate singletons
         │
         ▼
   SQLite (dev) / PostgreSQL (prod)
```

Key design decisions:

* **Application factory pattern** (`create\_app()`) — enables clean testing with isolated app instances (`create\_app("testing")`).
* **Blueprints** separate auth concerns from core app logic.
* **AI provider isolation** — `ai\_engine.py` is the only file that talks to Gemini. Swapping providers (OpenAI, Claude, etc.) touches one file, not the routes.
* **Repository-lite via SQLAlchemy relationships** — `User.contents`, `Content.tags`, etc. keep query logic declarative instead of scattering raw queries across routes.

\---

## Folder Structure

```
content-planner/
├── app/
│   ├── \_\_init\_\_.py       # Application factory
│   ├── auth.py           # Auth blueprint
│   ├── routes.py         # Main blueprint
│   ├── models.py         # User, Content, History, Category, Tag, SavedPrompt, ActivityLog
│   ├── forms.py          # WTForms
│   ├── ai\_engine.py      # Gemini API client + prompt templates
│   ├── config.py         # Env-based config classes
│   ├── extensions.py     # db, login\_manager, migrate
│   └── utils.py          # log\_activity, parse\_tags
├── static/
│   ├── css/style.css     # Design tokens, glassmorphism, animations
│   ├── js/main.js        # Theme toggle, AJAX generation, toasts
│   ├── images/
│   └── icons/
├── templates/            # 13 Jinja2 templates (base, dashboard, planner, history, ...)
├── run.py                # Dev entrypoint + `flask init-db` CLI command
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

\---

## Database Schema

|Model|Purpose|
|-|-|
|`User`|Account, hashed password, dark-mode preference|
|`Content`|Generated content item (title, type, prompt, AI output, status, schedule)|
|`History`|Immutable audit trail of every generation performed on a `Content`|
|`Category`|User-defined, color-labeled grouping|
|`Tag`|Free-form label, many-to-many with `Content`|
|`SavedPrompt`|Reusable prompt templates|
|`ActivityLog`|User action audit trail (login, generation, edits)|

\---

## Installation

```bash
git clone https://github.com/your-username/ai-content-planner.git
cd ai-content-planner

python -m venv venv
source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

cp .env.example .env            # then fill in GEMINI\_API\_KEY and SECRET\_KEY

python run.py                   # creates the SQLite DB automatically on first run
```

Visit `http://127.0.0.1:5000`, register an account, and start generating content.

\---

## Environment Variables

|Variable|Required|Description|
|-|-|-|
|`SECRET\_KEY`|✅|Flask session signing key — use a long random string|
|`GEMINI\_API\_KEY`|✅|Your Google Gemini API key ([get one here](https://aistudio.google.com/apikey))|
|`GEMINI\_MODEL`|–|Defaults to `gemini-2.5-flash`|
|`DATABASE\_URL`|–|Postgres URL for production; omit for local SQLite|
|`FLASK\_ENV`|–|`development` / `production` / `testing`|
|`ITEMS\_PER\_PAGE`|–|History pagination size (default `10`)|

Never commit `.env` — it's already excluded via `.gitignore`.

\---

## Deployment

### Render

1. Push this repo to GitHub.
2. New → Web Service → connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn run:app`
5. Add environment variables from `.env.example` in the Render dashboard.
6. Attach a Render PostgreSQL instance and set `DATABASE\_URL`.

### Railway

1. `railway init` in the project folder.
2. `railway add` → provision a PostgreSQL plugin (sets `DATABASE\_URL` automatically).
3. Set `SECRET\_KEY` and `GEMINI\_API\_KEY` in Railway's variables tab.
4. Deploy: Railway auto-detects `requirements.txt`; set the start command to `gunicorn run:app`.

### Vercel

Vercel's Python runtime is optimized for serverless functions rather than long-running Flask apps with SQLAlchemy connection pools — Render or Railway is recommended for this app. If you still want Vercel, wrap `app` as a serverless handler and use a hosted Postgres (e.g. Neon or Supabase) for `DATABASE\_URL`.

\---

## Running Tests

```bash
pip install pytest
FLASK\_ENV=testing pytest
```

The `TestingConfig` uses an in-memory SQLite database and disables CSRF so route tests can post forms directly.

\---

## Scaling Notes

* Swap `SQLALCHEMY\_DATABASE\_URI` to PostgreSQL (already wired via `DATABASE\_URL`) for concurrent writes beyond SQLite's single-writer limit.
* `ai\_engine.py` is stateless and safe to call concurrently; add a request queue (Celery/RQ) if generation volume grows enough to need background processing.
* Add Redis-backed rate limiting (`Flask-Limiter`) in front of `/api/generate` before opening the app to the public.
* Move Tailwind from the CDN build to a compiled build step for production (`npx tailwindcss -o static/css/tailwind.css --minify`) to drop the CDN dependency and cut page weight.

\---

## Contributing

1. Fork the repo and create a feature branch: `git checkout -b feature/your-feature`
2. Follow PEP8 and keep functions small and single-purpose.
3. Add/update tests for any new route or model behavior.
4. Open a PR describing the change and why it's needed.

\---

## Known Limitations / Future Improvements

* Forgot-password currently logs the reset link server-side instead of emailing it — wire up SendGrid/Mailgun/SES via `send\_reset\_email()` in `app/auth.py` for production use.
* Calendar view is table-based; a drag-and-drop month view (FullCalendar.js) is a natural next step.
* No automated test suite is included yet — `TestingConfig` is ready for one.
* Rate limiting on `/api/generate` is not yet implemented (see Scaling Notes).

\---

## Author

Built as a full-stack portfolio project demonstrating: SaaS architecture, REST-style AI integration, authentication, relational schema design, and production deployment practices.

## License

MIT — see [LICENSE](LICENSE).

