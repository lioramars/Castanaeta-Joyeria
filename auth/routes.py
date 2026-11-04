from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse
from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            next_page = request.form.get("next") or request.args.get("next")
            if next_page:
                # Reject external redirects (open-redirect prevention)
                if urlparse(next_page).netloc:
                    next_page = None
            return redirect(next_page or url_for("home"))

        flash("Invalid email or password.", "error")

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.", "error")
            return render_template("auth/register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "error")
            return render_template("auth/register.html")

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()

        login_user(user, remember=True)
        flash(f"Welcome, {name}! Your account has been created.", "success")
        return redirect(url_for("home"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))
