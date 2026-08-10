# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

"Spendly" is a personal expense-tracker web app built with Flask, server-rendered Jinja2 templates, and vanilla JS/CSS (no frontend framework, no build step). The project is being built incrementally as a learning exercise — `app.py` and `database/db.py` contain explicit comments marking placeholder routes and unwritten functions that are implemented step by step (see `prompts.txt` for the running log of prompts/steps used to build features so far, e.g. terms/privacy pages, hero section styling, the "See how it works" modal).

## Running the app

```
python app.py
```

Runs the Flask dev server on `http://localhost:5001` with `debug=True`. There is no separate build/lint/test-runner config beyond `pytest`/`pytest-flask` in `requirements.txt` (no test files exist yet).

Install dependencies into the existing `venv/`:
```
pip install -r requirements.txt
```

## Architecture

- **`app.py`** — single Flask application entrypoint. All routes are defined directly on the `app` object (no blueprints). Routes fall into two groups:
  - Implemented: `/`, `/register`, `/login`, `/terms`, `/privacy` — each just renders a template.
  - Placeholder stubs returning plain strings ("coming in Step N"): `/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`. These are intentionally unimplemented — do not build them out unless asked.
- **`database/db.py`** — currently a stub. Intended (per its header comment) to expose `get_db()` (SQLite connection with `row_factory` and foreign keys enabled), `init_db()` (create tables with `CREATE TABLE IF NOT EXISTS`), and `seed_db()` (sample data). No schema exists yet — when implementing DB features, this is the file to fill in.
- **`templates/`** — Jinja2 templates. `base.html` is the shared layout (nav + footer) that other pages `{% extends %}`; it defines `title`, `head`, `content`, and `scripts` blocks. Auth pages (`login.html`, `register.html`) share an `auth-section`/`auth-card` markup pattern. `landing.html` is more custom (hero section, feature sections, "how it works" modal) and does not necessarily reuse the auth card patterns.
- **`static/css/style.css`** — single global stylesheet for the whole site (no per-page CSS files despite `prompts.txt` referring to a hypothetical `landing.css` — that file doesn't exist; landing styles live in `style.css` too).
- **`static/js/main.js`** — single global JS file, vanilla JS only (explicitly no libraries/frameworks per project convention — see the modal requirement in `prompts.txt` #5).

## Conventions to preserve

- No JS frameworks or frontend build tooling — plain HTML/CSS/JS only.
- New pages should `{% extends "base.html" %}` and match the existing visual style (fonts: DM Serif Display + DM Sans via Google Fonts, loaded in `base.html`).
- When asked to change one page/section, don't touch unrelated markup — several past prompts (`prompts.txt`) explicitly scope changes to a single file/section, and that pattern of narrow, targeted edits should continue.
- Currency/domain context: expense tracking is rupee-denominated (see landing copy "Track every rupee").
