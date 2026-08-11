# Spec: Login & Logout

## Overview
This feature implements sign-in and sign-out for Spendly. It wires the existing `templates/login.html` form (which already POSTs to `/login`) up to real authentication: looking up the user by email, verifying the password against the stored hash, and starting a Flask session. It also implements `/logout` to end that session. Together these complete the authentication loop that Step 2 (Registration) started.

## Depends on
- Step 1 — Database Setup (`database/db.py` with `get_db()`, `init_db()`, `seed_db()`, and the `users`/`expenses` schema).
- Step 2 — Registration (`database/db.py`'s `get_user_by_email(email)`; `app.secret_key` and the `session["user_id"]` convention established in `app.py`'s `/register` handler). Login must set the session the same way registration does, so `/profile` treats both as equivalently "logged in".

## Routes
- `GET /login` — renders the login form — public (already implemented, unchanged)
- `POST /login` — validates submitted email/password, verifies credentials, starts a session, redirects to `/profile` on success; re-renders `login.html` with an error message on failure — public
- `GET /logout` — clears the session, redirects to `/login` — replaces the current placeholder (`"Logout — coming in Step 3"`)

## Database changes
No schema changes and no new data-access functions. `get_user_by_email(email)` (added in Step 2) is reused to fetch the row for verification.

## Templates
- **Create:** none
- **Modify:** `templates/login.html` — no structural changes required; it already renders `{{ error }}` when present and posts `email`, `password` to `/login`. Only touch this file if server-side validation needs a field-specific error class (keep changes minimal).

## Files to change
- `app.py` — replace the `/login` GET-only route with GET/POST handling (lookup by email, password verification, session creation, redirect to `/profile`); replace the `/logout` placeholder with a real handler (`session.clear()`, redirect to `/login`)

## Files to create
None.

## New dependencies
No new dependencies. Uses `flask.session` (built in) and `werkzeug.security.check_password_hash` (pairs with `generate_password_hash`, already used in `database/db.py`).

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Verify passwords with `werkzeug.security.check_password_hash` — never compare plaintext, never log the submitted password
- Use a single generic error message for both "no user with that email" and "wrong password" (e.g. "Invalid email or password.") — do not reveal which part was wrong, so the form can't be used to enumerate registered emails
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- On any validation/auth failure, re-render `templates/login.html` with `error` set and the submitted email preserved (mirroring how `register.html` preserves `name`/`email`) — do not redirect on failure
- `/logout` must clear the whole session (`session.clear()`), not just delete `user_id`
- Do not implement route-guarding/redirect-if-not-logged-in for `/profile` or the `/expenses/*` routes — those stay out of scope until their own steps
- Do not touch unrelated routes, templates, or CSS outside what's listed above

## Definition of done
- [ ] Submitting the login form with the seeded demo user's credentials (`demo@spendly.com` / `demo123`) redirects to `/profile` with an active session
- [ ] Submitting the login form with a registered user's correct email/password redirects to `/profile` with an active session
- [ ] Submitting with an email not in `users` re-renders `login.html` with a generic "Invalid email or password." error
- [ ] Submitting with a correct email but wrong password re-renders `login.html` with the same generic error (no hint as to which field was wrong)
- [ ] Visiting `/logout` while logged in clears the session and redirects to `/login`
- [ ] After `/logout`, the session no longer carries `user_id` (a fresh session)
- [ ] Restarting the app (`python app.py`) still works without errors
