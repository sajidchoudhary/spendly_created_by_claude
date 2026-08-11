# Spec: Profile

## Overview
This feature implements the account profile page for Spendly, replacing the current placeholder response (`"Profile page — coming in Step 4"`). It's the first route that requires an active session to view: it looks up the logged-in user by the `user_id` stored in the session and renders their account details (name, email, member-since date). This also introduces the project's first login-required route guard, which later steps (`/expenses/*`) will reuse.

## Depends on
- Step 1 — Database Setup (`database/db.py` with `get_db()`, `init_db()`, `seed_db()`, and the `users`/`expenses` schema).
- Step 2 — Registration (`session["user_id"]` convention established on successful registration).
- Step 3 — Login & Logout (`session["user_id"]` set on successful login; `/logout` clears the session so the guard has something to redirect away from).

## Routes
- `GET /profile` — shows the logged-in user's name, email, and member-since date; if no active session (`user_id` not in `session`), redirect to `/login` — logged-in only

## Database changes
No schema changes. New data-access function to add to `database/db.py`:
- `get_user_by_id(user_id)` — parameterized `SELECT * FROM users WHERE id = ?`, used to fetch the current user's profile data

## Templates
- **Create:** `templates/profile.html` — extends `base.html`; displays the user's name, email, and `created_at` ("member since") in a card matching the existing `auth-card` visual style used by `login.html`/`register.html`
- **Modify:** none

## Files to change
- `app.py` — replace the `/profile` placeholder with a real handler: check `session["user_id"]`, redirect to `/login` if absent, otherwise fetch the user with `get_user_by_id` and render `profile.html`
- `database/db.py` — add `get_user_by_id(user_id)`

## Files to create
- `templates/profile.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (unaffected by this step — never fetch or display `password_hash` in the template)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Do not display or leak `password_hash` in `profile.html` or in any query result passed to the template
- Do not modify `base.html`'s nav (no logged-in-state nav links) — out of scope for this step
- Do not implement route-guarding for `/expenses/*` routes — those stay out of scope until their own steps
- Do not implement editing profile fields — this step is view-only; edit functionality is a future step
- Do not touch unrelated routes, templates, or CSS outside what's listed above

## Definition of done
- [ ] Visiting `/profile` while logged in (after login or registration) shows the current user's name, email, and member-since date
- [ ] Visiting `/profile` with no active session redirects to `/login`
- [ ] After `/logout`, visiting `/profile` redirects to `/login` instead of showing stale profile data
- [ ] `password_hash` never appears in the rendered `/profile` HTML (view page source to confirm)
- [ ] Restarting the app (`python app.py`) still works without errors
