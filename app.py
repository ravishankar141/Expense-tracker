import sqlite3
from urllib.parse import urlparse

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

from werkzeug.security import check_password_hash

from database.db import init_db, seed_db, close_db, create_user, get_user_by_email

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"  # TODO: Move to env var before deployment

# Initialize database on startup
with app.app_context():
    init_db()
    seed_db()


@app.teardown_appcontext
def teardown_db(exception):
    """Close database connection after each request."""
    close_db(exception)


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Server-side validation
        if not name:
            flash("Name is required", "error")
            return render_template("register.html")

        if not email:
            flash("Email is required", "error")
            return render_template("register.html")

        if not password:
            flash("Password is required", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template("register.html")

        try:
            create_user(name, email, password)
            flash("Account created successfully!", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already registered", "error")
            return render_template("register.html")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # Get the next URL from query param (for redirecting after login)
    next_url = request.args.get("next", "")

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        next_url = request.form.get("next", "")

        if not email:
            flash("Email is required", "error")
            return render_template("login.html", next=next_url)

        if not password:
            flash("Password is required", "error")
            return render_template("login.html", next=next_url)

        user = get_user_by_email(email)
        if user is None or not check_password_hash(user['password_hash'], password):
            flash("Invalid credentials", "error")
            return render_template("login.html", next=next_url)

        # TODO: session.regenerate() before setting user data (Step 0X)
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        flash("Logged in successfully!", "success")

        # Redirect to next URL if it's safe, otherwise go to profile
        if next_url and _is_safe_redirect_url(next_url):
            return redirect(next_url)
        return redirect(url_for("profile"))

    return render_template("login.html", next=next_url)


def _is_safe_redirect_url(target):
    """Check if a redirect URL is safe (same host, not external)."""
    parsed = urlparse(target)
    # Only allow relative URLs (netloc empty) or same host redirects
    return not parsed.netloc and parsed.path.startswith("/")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    # Authentication guard - redirect to login if not authenticated
    if not session.get("user_id"):
        flash("Please log in to access your profile", "error")
        return redirect(url_for("login", next=request.url))

    # Hardcoded data for Step 4 (UI design phase)
    context = {
        "user": {
            "name": "Demo User",
            "email": "demo@spendly.com",
            "member_since": "April 2025"
        },
        "stats": {
            "total_spent": 575.50,
            "transaction_count": 8,
            "top_category": "Food"
        },
        "transactions": [
            {"date": "Apr 12, 2025", "description": "Dinner", "category": "Food", "amount": 60.00},
            {"date": "Apr 10, 2025", "description": "Groceries", "category": "Shopping", "amount": 150.00},
            {"date": "Apr 8, 2025", "description": "Movie tickets", "category": "Entertainment", "amount": 35.00},
            {"date": "Apr 6, 2025", "description": "Pharmacy", "category": "Health", "amount": 55.00},
            {"date": "Apr 5, 2025", "description": "Electric bill", "category": "Bills", "amount": 85.00},
            {"date": "Apr 3, 2025", "description": "Monthly bus pass", "category": "Transport", "amount": 120.00},
            {"date": "Apr 1, 2025", "description": "Lunch at cafe", "category": "Food", "amount": 45.50},
            {"date": "Apr 11, 2025", "description": "Misc items", "category": "Other", "amount": 25.00}
        ],
        "categories": [
            {"name": "Food", "amount": 105.50, "percentage": 100},
            {"name": "Transport", "amount": 120.00, "percentage": 100},
            {"name": "Bills", "amount": 85.00, "percentage": 70},
            {"name": "Health", "amount": 55.00, "percentage": 50},
            {"name": "Entertainment", "amount": 35.00, "percentage": 35},
            {"name": "Shopping", "amount": 150.00, "percentage": 100},
            {"name": "Other", "amount": 25.00, "percentage": 25}
        ]
    }

    return render_template("profile.html", **context)


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
    app.run(debug=True, port=5000)
