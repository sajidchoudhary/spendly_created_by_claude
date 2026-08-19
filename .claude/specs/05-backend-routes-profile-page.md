# Spec: Profile Page Backend Routes

## Overview
Step 4 (Profile Page) built the `/profile` view and `templates/profile.html` against fully hardcoded data so the layout could be validated in isolation. This step replaces that hardcoded data with real queries against the `expenses` table, so the identity card, summary stats, transaction history, and category breakdown all reflect the logged-in user's actual rows. No new routes, templates, or schema — this is purely wiring the existing `/profile` view and template up to the database.

## Depends on
- Step 1 — Database Setup (`users`/`expenses` schema, `get_db()`).
- Step 2 — Registration (`create_user`, `get_user_by_email`).
- Step 3 — Login & Logout (`session["user_id"]` convention; `/profile` already redirects to `/login` when logged out).
- Step 4 — Profile Page (`templates/profile.html` and the `/profile` view currently pass four hardcoded context variables: `user`, `stats`, `transactions`, `categories`). This step keeps that same shape but fills it from the database instead of literals.

## Routes
No new routes. `GET /profile` (already implemented, logged-in only) keeps its existing signature — only the body of the view function changes, from hardcoded literals to database-driven values.

## Database changes
No schema changes. Two new read-only data-access functions in `database/db.py`, alongside the existing `get_user_by_id`:
- `get_expenses_by_user(user_id)` — `SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC, id DESC` — returns every expense row for the user, most recent first.
- `get_category_totals(user_id)` — `SELECT category, SUM(amount) AS total FROM expenses WHERE user_id = ? GROUP BY category ORDER BY total DESC` — per-category totals, largest first.

## Templates
- **Create:** none.
- **Modify:** `templates/profile.html` — no structural changes expected; it already iterates `stats`, `transactions`, `categories` and reads `user.name` / `user.initials` / `user.email` / `user.member_since`. Only touch it if the real data requires a genuinely empty state (e.g. a "No expenses yet" row) that the current markup can't express.

## Files to change
- `app.py` — rewrite the `/profile` view body:
  - Fetch the current user via `get_user_by_id(session["user_id"])` for name/email/initials/member-since.
  - Fetch expenses via `get_expenses_by_user(user_id)` and category totals via `get_category_totals(user_id)`.
  - Build `user`, `stats`, `transactions`, `categories` dicts/lists in the exact shape `profile.html` already expects (same keys as the current hardcoded version: `user.initials/name/email/member_since`; `stats[].label/value/note`; `transactions[].date/description/category/amount`; `categories[].name/amount/bar_class`).
  - Format currency as `₹{amount:,.0f}` (matches existing hardcoded values like `₹18,240`) and dates as `%d %b` (matches `12 Aug`); derive `member_since` from `users.created_at` formatted as `%B %Y`.
  - Limit the transaction history to the 5 most recent expenses (`transactions[:5]`), while stats/category totals use the full expense set.
  - Handle the zero-expenses case: total spent `₹0`, transaction count `0`, top category `—`, empty `transactions`/`categories` lists — must not raise (e.g. no indexing into an empty `get_category_totals()` result).
  - Compute `bar_class` for category rows by scaling each category's share of the largest category's total against the four existing `.profile-bar-1`–`.profile-bar-4` CSS steps (largest category gets `profile-bar-1`, and so on in ranked order) — do not add new CSS classes.
- `database/db.py` — add `get_expenses_by_user(user_id)` and `get_category_totals(user_id)`, following the same connect/execute/close pattern as `get_user_by_id`.

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (no auth changes in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- No inline styles, and no new CSS classes — reuse the existing `.cat-*` (already covers all 7 `CATEGORIES`) and `.profile-bar-1`–`.profile-bar-4` classes
- Do not change the `user`/`stats`/`transactions`/`categories` context shape — `profile.html` must not need structural edits
- Do not touch `/expenses/*` placeholder routes, login/registration logic, or unrelated CSS/templates
- All currency/date formatting happens in `app.py` (or small helper functions there), not in the template

## Definition of done
- [ ] Logging in as the seeded demo user (`demo@spendly.com` / `demo123`) and visiting `/profile` shows their real name, email, and member-since date (not "Nitish Kumar")
- [ ] The transaction history table shows up to 5 of the demo user's actual seeded expenses, most recent first, with correctly formatted dates and ₹ amounts
- [ ] The category breakdown shows the demo user's real per-category totals, ranked largest to smallest, using only the existing `.profile-bar-1`–`.profile-bar-4` classes
- [ ] "Total spent" and "Transactions" stats match the actual sum/count of the demo user's expenses; "Top category" matches the highest-total category
- [ ] Registering a brand-new user (no expenses yet) and visiting `/profile` renders without errors, showing zero/empty states instead of a crash
- [ ] Visiting `/profile` while logged out still redirects to `/login` (unchanged from Step 4)
- [ ] Restarting the app (`python app.py`) still works without errors
