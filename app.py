from flask import (
    Flask, render_template, abort,
    session, redirect, url_for
)
from auth.routes import auth_bp
from admin_dashboard.routes import admin_bp
from dotenv import load_dotenv   # ⬅️ חדש
import json
import os

# ⬅️ טוען משתני סביבה
load_dotenv(override=False)

app = Flask(__name__)
app.config.from_object("config.Config")


# -----------------------
# Load Products
# -----------------------
def load_products():
    path = os.path.join(
        os.path.dirname(__file__),
        "data", "products.json"
    )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_product(product_id):
    for p in load_products():
        if p["id"] == product_id:
            return p
    return None

# -----------------------
# Blueprints
# -----------------------
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(admin_bp, url_prefix="/admin")

# -----------------------
# Home
# -----------------------
@app.route("/")
def home():
    return render_template("home.html")

# -----------------------
# Collection (All)
# -----------------------
@app.route("/collection")
def collection():
    return render_template(
        "jewelry_collection.html",
        products=load_products()
    )

# -----------------------
# Collection by Category
# -----------------------
@app.route("/collection/<category>")
def category_page(category):
    products = [
        p for p in load_products()
        if p.get("category") == category
    ]
    if not products:
        abort(404)
    return render_template(
        "jewelry_collection.html",
        products=products,
        category=category
    )

# -----------------------
# Product Detail
# -----------------------
@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = get_product(product_id)
    if not product:
        abort(404)
    return render_template(
        "jewelry_detail.html",
        product=product
    )

# =====================================================
# 🧺 CART (Session-based)
# =====================================================

# Add product to cart
@app.route("/add-to-cart/<int:product_id>")
def add_to_cart(product_id):
    cart = session.get("cart", {})

    pid = str(product_id)
    cart[pid] = cart.get(pid, 0) + 1

    session["cart"] = cart
    session.modified = True

    return redirect(url_for("cart"))

# View cart
@app.route("/cart")
def cart():
    cart = session.get("cart", {})
    products = load_products()

    cart_items = []
    total = 0

    for p in products:
        pid = str(p["id"])
        if pid in cart:
            qty = cart[pid]
            subtotal = qty * p["price"]
            total += subtotal

            cart_items.append({
                "product": p,
                "qty": qty,
                "subtotal": subtotal
            })

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total=total
    )

# Remove one product completely
@app.route("/remove-from-cart/<int:product_id>")
def remove_from_cart(product_id):
    cart = session.get("cart", {})
    cart.pop(str(product_id), None)
    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart"))

# Clear entire cart
@app.route("/clear-cart")
def clear_cart():
    session.pop("cart", None)
    return redirect(url_for("cart"))

# -----------------------
# Run
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
