import re

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import create_user, get_db, get_user_by_email, init_db, seed_db

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


@app.route("/profile")
def profile():
    if session.get("user_id") is None:
        return redirect(url_for("login"))

    user = {
        "name": "Nitish Kumar",
        "initials": "NK",
        "email": "nitish@example.com",
        "member_since": "March 2025",
    }
    stats = [
        {"label": "Total spent", "value": "₹18,240", "note": "this month"},
        {"label": "Transactions", "value": "34", "note": "logged"},
        {"label": "Top category", "value": "Food", "note": "₹6,200 spent"},
    ]
    transactions = [
        {"date": "12 Aug", "description": "Grocery run", "category": "Food", "amount": "₹1,240"},
        {"date": "10 Aug", "description": "Electricity bill", "category": "Bills", "amount": "₹2,100"},
        {"date": "09 Aug", "description": "Cab to airport", "category": "Transport", "amount": "₹640"},
        {"date": "07 Aug", "description": "Movie night", "category": "Entertainment", "amount": "₹450"},
        {"date": "05 Aug", "description": "Pharmacy", "category": "Health", "amount": "₹380"},
    ]
    categories = [
        {"name": "Food", "amount": "₹6,200", "bar_class": "profile-bar-1"},
        {"name": "Bills", "amount": "₹4,300", "bar_class": "profile-bar-2"},
        {"name": "Transport", "amount": "₹2,860", "bar_class": "profile-bar-3"},
        {"name": "Entertainment", "amount": "₹1,540", "bar_class": "profile-bar-4"},
    ]
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
