import re
from datetime import datetime

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import (
    create_user,
    get_category_totals,
    get_db,
    get_expenses_by_user,
    get_user_by_email,
    get_user_by_id,
    init_db,
    seed_db,
)

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

def build_transaction_history(expenses):
    """Return the transactions list for profile.html: date/description/category/amount, most recent 5."""
    transactions = []
    for expense in expenses[:5]:
        date = datetime.strptime(expense["date"], "%Y-%m-%d").strftime("%d %b")
        transactions.append({
            "date": date,
            "description": expense["description"] or "—",
            "category": expense["category"],
            "amount": f"₹{expense['amount']:,.0f}",
        })
    return transactions


def build_summary_stats(expenses, category_totals):
    """Return the 3-item stats list for profile.html: total spent, transaction count, top category."""
    total_spent = sum(row["total"] for row in category_totals)

    if category_totals:
        top_category = category_totals[0]
        top_value = top_category["category"]
        top_note = f"₹{top_category['total']:,.0f} spent"
    else:
        top_value = "—"
        top_note = "No expenses yet"

    return [
        {"label": "Total spent", "value": f"₹{total_spent:,.0f}", "note": "all time"},
        {"label": "Transactions", "value": str(len(expenses)), "note": "logged"},
        {"label": "Top category", "value": top_value, "note": top_note},
    ]


def build_category_breakdown(category_totals):
    """Return the categories list for profile.html: name/amount/bar_class (profile-bar-1..4)."""
    categories = []
    for rank, row in enumerate(category_totals[:4], start=1):
        categories.append({
            "name": row["category"],
            "amount": f"₹{row['total']:,.0f}",
            "bar_class": f"profile-bar-{rank}",
        })
    return categories


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

    expenses = get_expenses_by_user(user_id)
    category_totals = get_category_totals(user_id)

    stats = build_summary_stats(expenses, category_totals)
    transactions = build_transaction_history(expenses)
    categories = build_category_breakdown(category_totals)

    return render_template(
        "profile.html", user=user, stats=stats, transactions=transactions, categories=categories,
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
