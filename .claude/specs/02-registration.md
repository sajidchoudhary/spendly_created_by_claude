# Spec: Registration

## Overview
This feature implements user sign-up for Spendly. It wires the existing `templates/register.html` form (which already POSTs to `/register`) up to real account creation: validating input, hashing the password, inserting a new row into the `users` table, and logging the new user in via a Flask session. This is the first authentication feature built on top of the Step 1 database layer, and it establishes the session mechanism that later steps (logout, profile, expense CRUD) will depend on.

## Depends on
- Step 1 — Database Setup (`database/db.py` with `get_db()`, `init_db()`, `seed_db()`, and the `users`/`expenses` schema). Required so registration has a real `users` table and hashing utility available.

## Routes
- `GET /register` — renders the registration form — public (already implemented, unchanged)
- `POST /register` — validates submitted name/email/password, creates the user, starts a session, redirects to `/profile` on success; re-renders `register.html` with an error message on failure — public

## Database changes
No schema changes. The `users` table created in Step 1 (`id`, `name`, `email` UNIQUE, `password_hash`, `created_at`) already supports registration as-is.

New data-access functions to add to `database/db.py` (no new tables/columns):
- `get_user_by_email(email)` — `SELECT` by email, used to check for duplicates
- `create_user(name, email, password_hash)` — parameterized `INSERT` into `users`, returns the new user id

## Templates
- **Create:** none
- **Modify:** `templates/register.html` — no structural changes required; it already renders `{{ error }}` when present and posts `name`, `email`, `password` to `/register`. Only touch this file if server-side validation needs a field-specific error class (keep changes minimal).

## Files to change
- `app.py` — add `session` import and `app.secret_key`; replace the `/register` GET-only route with GET/POST handling (validation, duplicate-email check, password hashing, `create_user` call, session creation, redirect to `/profile`)
- `database/db.py` — add `get_user_by_email(email)` and `create_user(name, email, password_hash)` functions

## Files to create
None.

## New dependencies
No new dependencies. Uses `flask.session` (built in) and `werkzeug.security.generate_password_hash` (already used in `database/db.py`).

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (`generate_password_hash`), never stored or logged in plain text
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Validate on the server even though the form has `required`/`type="email"` attributes client-side: name non-empty, email format, password minimum length (8, matching the placeholder text "Min. 8 characters"), and email not already registered
- On any validation failure, re-render `templates/register.html` with `error` set and the form's entered values preserved where reasonable — do not redirect on failure
- Do not implement `/login` POST handling, `/logout`, or `/profile` beyond their current placeholder/GET behavior — out of scope for this step
- Do not touch unrelated routes, templates, or CSS outside what's listed above

## Definition of done
- [ ] Submitting the register form with a new name/email/password creates a row in `users` with a hashed (not plaintext) password
- [ ] After successful registration, the browser is redirected to `/profile` and a session is active (subsequent requests are "logged in")
- [ ] Submitting with an email that already exists in `users` re-renders `register.html` with an error and does not create a duplicate row
- [ ] Submitting with a password under 8 characters re-renders `register.html` with an error and does not create a user
- [ ] Submitting with an invalid email format re-renders `register.html` with an error and does not create a user
- [ ] Restarting the app (`python app.py`) still works without errors and does not duplicate the seeded demo user
- [ ] No plaintext passwords appear anywhere in `expense_tracker.db`
