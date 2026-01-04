from flask import (
    Flask, render_template, abort,
    session, redirect, url_for, request, jsonify
)
from auth.routes import auth_bp
from admin_dashboard.routes import admin_bp
from dotenv import load_dotenv
from uuid import uuid4
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# PayPal SDK
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment
from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest

# =====================================================
# Environment
# =====================================================

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET")
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")  # sandbox | live

# =====================================================
# App init
# =====================================================

app = Flask(__name__)
app.config.from_object("config.Config")

# =====================================================
# PayPal client
# =====================================================

paypal_env = (
    LiveEnvironment(client_id=PAYPAL_CLIENT_ID, client_secret=PAYPAL_SECRET)
    if PAYPAL_MODE == "live"
    else SandboxEnvironment(client_id=PAYPAL_CLIENT_ID, client_secret=PAYPAL_SECRET)
)

paypal_client = PayPalHttpClient(paypal_env)

# =====================================================
# Products helpers
# =====================================================

def load_products():
    path = os.path.join(os.path.dirname(__file__), "data", "products.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_product(product_id):
    for p in load_products():
        if p["id"] == product_id:
            return p
    return None

# =====================================================
# 🧺 Cart helpers
# =====================================================

def build_cart_items():
    cart = session.get("cart", {})
    products = load_products()

    items = []
    total = 0

    for p in products:
        pid = str(p["id"])
        if pid in cart:
            qty = cart[pid]
            subtotal = qty * p["price"]
            total += subtotal
            items.append({
                "product": p,
                "qty": qty,
                "subtotal": subtotal
            })

    return items, total

# =====================================================
# Email helper
# =====================================================

def send_email(to, subject, html):
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASSWORD)
        s.send_message(msg)

# =====================================================
# Blueprints
# =====================================================

app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(admin_bp, url_prefix="/admin")

# =====================================================
# Pages
# =====================================================

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/collection")
def collection():
    return render_template("jewelry_collection.html", products=load_products())


@app.route("/collection/<category>")
def category_page(category):
    products = [p for p in load_products() if p.get("category") == category]
    if not products:
        abort(404)
    return render_template("jewelry_collection.html", products=products, category=category)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = get_product(product_id)
    if not product:
        abort(404)
    return render_template("jewelry_detail.html", product=product)

# =====================================================
# 🧺 Cart routes
# =====================================================

@app.route("/add-to-cart/<int:product_id>")
def add_to_cart(product_id):
    cart = session.get("cart", {})
    pid = str(product_id)
    cart[pid] = cart.get(pid, 0) + 1
    session["cart"] = cart
    return redirect(request.referrer or url_for("cart"))


@app.route("/update-cart/<int:product_id>", methods=["POST"])
def update_cart(product_id):
    cart = session.get("cart", {})
    pid = str(product_id)
    action = request.form.get("action")

    if pid in cart:
        if action == "increase":
            cart[pid] += 1
        elif action == "decrease":
            cart[pid] -= 1
            if cart[pid] <= 0:
                cart.pop(pid)

    session["cart"] = cart
    return redirect(url_for("cart"))


@app.route("/cart")
def cart():
    items, total = build_cart_items()
    return render_template("cart.html", cart_items=items, total=total)


@app.route("/remove-from-cart/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):
    cart = session.get("cart", {})
    cart.pop(str(product_id), None)
    session["cart"] = cart
    return redirect(url_for("cart"))


@app.route("/clear-cart")
def clear_cart():
    session.pop("cart", None)
    return redirect(url_for("cart"))

# =====================================================
# Checkout page
# =====================================================

@app.route("/checkout")
def checkout():
    items, total = build_cart_items()
    if not items:
        return redirect(url_for("cart"))

    return render_template(
        "checkout.html",
        cart_items=items,
        total=total,
        PAYPAL_CLIENT_ID=PAYPAL_CLIENT_ID
    )

# =====================================================
# PayPal API
# =====================================================

@app.route("/paypal/create-order", methods=["POST"])
def paypal_create_order():
    items, total = build_cart_items()
    shipping = request.json or {}

    # Save shipping info in session
    session["shipping"] = shipping

    req = OrdersCreateRequest()
    req.prefer("return=representation")
    req.request_body({
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {
                "currency_code": "ILS",
                "value": str(total)
            }
        }]
    })

    res = paypal_client.execute(req)
    return jsonify({"id": res.result.id})


@app.route("/paypal/capture-order/<order_id>", methods=["POST"])
def paypal_capture_order(order_id):
    paypal_client.execute(OrdersCaptureRequest(order_id))

    items, total = build_cart_items()
    shipping = session.get("shipping", {})
    order_short_id = uuid4().hex[:8].upper()

    # =========================
    # Build email content
    # =========================

    address_html = f"""
    <h3>Shipping Details</h3>
    <p>
      <strong>Name:</strong> {shipping.get('name')}<br>
      <strong>Email:</strong> {shipping.get('email')}<br>
      <strong>Phone:</strong> {shipping.get('phone')}<br><br>

      <strong>Address:</strong><br>
      {shipping.get('street')} {shipping.get('house')}<br>
      {f"Apt {shipping.get('apartment')}<br>" if shipping.get('apartment') else ""}
      {shipping.get('city')} {shipping.get('postcode','')}
    </p>
    """

    items_html = "".join(
        f"<li>{i['product']['name']} × {i['qty']}</li>"
        for i in items
    )

    email_body = f"""
    <h2>New Paid Order #{order_short_id}</h2>
    {address_html}
    <h3>Items</h3>
    <ul>{items_html}</ul>
    <p><strong>Total:</strong> {total} ₪</p>
    """

    send_email(
        ADMIN_EMAIL,
        f"New Paid Order #{order_short_id}",
        email_body
    )

    session.pop("cart", None)
    session.pop("shipping", None)

    return jsonify({"status": "success"})

# =====================================================
# Success page
# =====================================================

@app.route("/checkout-success")
def checkout_success():
    return render_template("checkout_success.html")

# =====================================================
# Run
# =====================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
