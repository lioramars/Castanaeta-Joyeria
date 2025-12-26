from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session, current_app
)
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import json
import os

admin_bp = Blueprint(
    "admin",
    __name__,
    template_folder="templates"
)

# -----------------------
# Helpers
# -----------------------
def products_path():
    return os.path.join(
        os.path.dirname(__file__),
        "..", "data", "products.json"
    )

def load_products():
    with open(products_path(), "r", encoding="utf-8") as f:
        return json.load(f)

def save_products(products):
    with open(products_path(), "w", encoding="utf-8") as f:
        json.dump(products, f, indent=4, ensure_ascii=False)

# -----------------------
# Admin protection
# -----------------------
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return wrapper

# -----------------------
# Login
# -----------------------
@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if (
            request.form["username"] == current_app.config["ADMIN_USERNAME"]
            and check_password_hash(
                current_app.config["ADMIN_PASSWORD_HASH"],
                request.form["password"]
            )
        ):
            session["admin_logged_in"] = True
            return redirect(url_for("admin.products"))

        return render_template(
            "admin_login.html",
            error="Invalid credentials"
        )

    return render_template("admin_login.html")

# -----------------------
# Logout
# -----------------------
@admin_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("admin.login"))

# -----------------------
# Products page
# -----------------------
@admin_bp.route("/products")
@admin_required
def products():
    return render_template(
        "admin_products.html",
        products=load_products()
    )

# -----------------------
# Add product (WITH IMAGE UPLOAD)
# -----------------------
@admin_bp.route("/products/add", methods=["POST"])
@admin_required
def add_product():
    products = load_products()

    file = request.files["image"]
    filename = secure_filename(file.filename)

    upload_dir = os.path.join(
        current_app.root_path,
        current_app.config["UPLOAD_FOLDER"]
    )
    os.makedirs(upload_dir, exist_ok=True)

    file.save(os.path.join(upload_dir, filename))

    new_product = {
        "id": max(p["id"] for p in products) + 1 if products else 1,
        "name": request.form["name"],
        "description": request.form["description"],
        "price": int(request.form["price"]),
        "category": request.form["category"],
        # ⬇️ חשוב: נתיב יחסי ל־static
        "image": f"img/uploads/{filename}"
    }

    products.append(new_product)
    save_products(products)

    return redirect(url_for("admin.products"))

# -----------------------
# Delete product
# -----------------------
@admin_bp.route("/products/delete/<int:product_id>")
@admin_required
def delete_product(product_id):
    products = [p for p in load_products() if p["id"] != product_id]
    save_products(products)
    return redirect(url_for("admin.products"))
