import calendar
import re
from datetime import date, datetime

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import (
    create_user,
    get_db,
    get_user_by_email,
    get_user_by_id,
    init_db,
    seed_db,
)
from database.queries import get_category_breakdown, get_recent_transactions, get_summary_stats

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-me"  # hardcoded for this learning project

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not name:
        return render_template("register.html", error="Name is required.", name=name, email=email)

    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not re.match(email_pattern, email):
        return render_template("register.html", error="Enter a valid email address.", name=name, email=email)

    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters.", name=name, email=email)

    if get_user_by_email(email) is not None:
        return render_template("register.html", error="An account with that email already exists.", name=name, email=email)

    password_hash = generate_password_hash(password)
    user_id = create_user(name, email, password_hash)

    session["user_id"] = user_id

    return redirect(url_for("profile"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = get_user_by_email(email)
    if user is None or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid email or password.", email=email)

    session["user_id"] = user["id"]

    return redirect(url_for("profile"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ------------------------------------------------------------------ #
# Profile data helpers — each builds one section of /profile's        #
# template context from the user's expenses / category totals         #
# ------------------------------------------------------------------ #

def build_transaction_history(rows):
    """Return the transactions list for profile.html: date/description/category/amount."""
    transactions = []
    for expense in rows:
        formatted_date = datetime.strptime(expense["date"], "%Y-%m-%d").strftime("%d %b")
        transactions.append({
            "date": formatted_date,
            "description": expense["description"] or "—",
            "category": expense["category"],
            "amount": f"₹{expense['amount']:,.0f}",
        })
    return transactions


def build_summary_stats(stats_row):
    """Return the 3-item stats list for profile.html: total spent, transaction count, top category."""
    total_spent = stats_row["total_spent"] or 0
    transaction_count = stats_row["transaction_count"] or 0
    top_category = stats_row["top_category"]

    if top_category is not None:
        top_value = top_category
        top_note = f"₹{stats_row['top_category_total']:,.0f} spent"
    else:
        top_value = "—"
        top_note = "No expenses yet"

    return [
        {"label": "Total spent", "value": f"₹{total_spent:,.0f}", "note": "all time"},
        {"label": "Transactions", "value": str(transaction_count), "note": "logged"},
        {"label": "Top category", "value": top_value, "note": top_note},
    ]


def build_category_breakdown(rows):
    """Return the categories list for profile.html: name/amount/bar_class (profile-bar-1..4)."""
    categories = []
    for rank, row in enumerate(rows[:4], start=1):
        categories.append({
            "name": row["category"],
            "amount": f"₹{row['total']:,.0f}",
            "bar_class": f"profile-bar-{rank}",
        })
    return categories


# ------------------------------------------------------------------ #
# Profile date-filter helpers                                        #
# ------------------------------------------------------------------ #

PRESET_ORDER = ["this-month", "last-3-months", "last-6-months", "all-time"]
PRESET_LABELS = {
    "this-month": "This Month",
    "last-3-months": "Last 3 Months",
    "last-6-months": "Last 6 Months",
    "all-time": "All Time",
}


def parse_date_param(value):
    """Parse a YYYY-MM-DD query-string value; return a date, or None if absent/malformed."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def shift_months(d, months_delta):
    """Return d shifted by months_delta calendar months, clamping day to the target month's length."""
    total_months = d.year * 12 + (d.month - 1) + months_delta
    year, month = divmod(total_months, 12)
    month += 1
    last_day_of_month = calendar.monthrange(year, month)[1]
    day = min(d.day, last_day_of_month)
    return date(year, month, day)


def get_presets():
    """Return {preset_key: (start_date, end_date)} as date objects; all-time is (None, None)."""
    today = date.today()
    return {
        "this-month": (today.replace(day=1), today),
        "last-3-months": (shift_months(today, -3), today),
        "last-6-months": (shift_months(today, -6), today),
        "all-time": (None, None),
    }


def resolve_active_preset(active_from, active_to, presets):
    """Map the currently-applied filter back to a preset key, or 'custom', for template highlighting."""
    if active_from is None and active_to is None:
        return "all-time"
    for key, (preset_from, preset_to) in presets.items():
        if key == "all-time":
            continue
        if preset_from.isoformat() == active_from and preset_to.isoformat() == active_to:
            return key
    return "custom"


@app.route("/profile")
def profile():
    if session.get("user_id") is None:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    user_row = get_user_by_id(user_id)
    initials = "".join(part[0] for part in user_row["name"].split()[:2]).upper()
    member_since = datetime.strptime(
        user_row["created_at"], "%Y-%m-%d %H:%M:%S"
    ).strftime("%B %Y")
    user = {
        "name": user_row["name"],
        "initials": initials,
        "email": user_row["email"],
        "member_since": member_since,
    }

    parsed_from = parse_date_param(request.args.get("date_from"))
    parsed_to = parse_date_param(request.args.get("date_to"))

    active_from = None
    active_to = None
    if parsed_from is not None and parsed_to is not None:
        if parsed_from > parsed_to:
            flash("Start date must be before end date.")
        else:
            active_from = parsed_from.isoformat()
            active_to = parsed_to.isoformat()

    stats_row = get_summary_stats(user_id, active_from, active_to)
    transaction_rows = get_recent_transactions(user_id, limit=5, date_from=active_from, date_to=active_to)
    category_rows = get_category_breakdown(user_id, active_from, active_to)

    stats = build_summary_stats(stats_row)
    transactions = build_transaction_history(transaction_rows)
    categories = build_category_breakdown(category_rows)

    presets = get_presets()
    preset_links = [
        {
            "key": key,
            "label": PRESET_LABELS[key],
            "date_from": presets[key][0].isoformat() if presets[key][0] else None,
            "date_to": presets[key][1].isoformat() if presets[key][1] else None,
        }
        for key in PRESET_ORDER
    ]
    active_preset = resolve_active_preset(active_from, active_to, presets)

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
        date_from=active_from,
        date_to=active_to,
        active_preset=active_preset,
        preset_links=preset_links,
    )


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
