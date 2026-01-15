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
from markupsafe import Markup, escape

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

def send_email(to_email, subject, html_body, from_name="Castanaeta", from_email=None):
    """Send a simple HTML email (uses SMTP env vars)."""
    if not to_email:
        return False
    from_email = from_email or SMTP_USER
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_email

    part = MIMEText(html_body, "html", "utf-8")
    msg.attach(part)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.sendmail(from_email, [to_email], msg.as_string())
        return True
    except Exception as e:
        # optional: log exception
        print("send_email error:", e)
        return False

# register nl2br jinja filter
def nl2br(value):
    if value is None:
        return ''
    # escape to avoid XSS, then replace newlines with <br>
    return Markup('<br>').join(escape(value).splitlines())

app.jinja_env.filters['nl2br'] = nl2br

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
    session.modified = True
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
    session.modified = True
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
    session.modified = True
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

def _build_items_html(items):
    return "".join(
        f"<li>{i['product']['name']} × {i['qty']} — {i['subtotal']} ₪</li>"
        for i in items
    )


def _build_shipping_html(shipping: dict):
    street = shipping.get("street", "")
    house = shipping.get("house", "")
    apartment = shipping.get("apartment", "")
    city = shipping.get("city", "")
    postcode = shipping.get("postcode", "")
    phone = shipping.get("phone", "")
    name = shipping.get("name", "")
    email = shipping.get("email", "")

    apt_line = f"Apt {apartment}<br>" if apartment else ""

    return f"""
    <h3>Shipping Details</h3>
    <p>
      <strong>Name:</strong> {name}<br>
      <strong>Email:</strong> {email}<br>
      <strong>Phone:</strong> {phone}<br><br>
      <strong>Address:</strong><br>
      {street} {house}<br>
      {apt_line}
      {city} {postcode}
    </p>
    """


@app.route("/paypal/create-order", methods=["POST"])
def paypal_create_order():
    items, total = build_cart_items()
    shipping = request.get_json(silent=True) or {}

    # Save shipping info in session (used in capture step)
    session["shipping"] = shipping
    session.modified = True

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
    # 1) Capture in PayPal
    paypal_client.execute(OrdersCaptureRequest(order_id))

    # 2) Build order details from session/cart
    items, total = build_cart_items()
    shipping = session.get("shipping", {}) or {}
    order_short_id = uuid4().hex[:8].upper()

    # make a small serializable items list for the success page / session
    serial_items = [
        {"name": i["product"]["name"], "qty": i["qty"], "subtotal": i["subtotal"]}
        for i in items
    ]

    # build order object and store in session for the success page
    order = {
        "id": order_short_id,
        "items": serial_items,
        "total": total,
        "customer": {
            "name": shipping.get("name", ""),
            "email": shipping.get("email", ""),
            "phone": shipping.get("phone", ""),
            "address": {
                "street": shipping.get("street", ""),
                "house": shipping.get("house", ""),
                "apartment": shipping.get("apartment", ""),
                "city": shipping.get("city", ""),
                "postcode": shipping.get("postcode", "")
            }
        }
    }

    # store last order in session so /checkout-success can read it
    session["last_order"] = order
    session.modified = True

    items_html = _build_items_html(items)
    shipping_html = _build_shipping_html(shipping)

    admin_body = f"""
    <h2>New Paid Order #{order_short_id}</h2>
    {shipping_html}
    <h3>Items</h3>
    <ul>{items_html}</ul>
    <p><strong>Total:</strong> {total} ₪</p>
    """

    # 3) Send email to ADMIN
    if ADMIN_EMAIL:
        send_email(ADMIN_EMAIL, f"New Paid Order #{order_short_id}", admin_body)

    # 4) Send email to CUSTOMER
    customer_email = shipping.get("email")
    customer_name = shipping.get("name", "")

    if customer_email:
        customer_body = f"""
        <h2>Thank you for your order 🎉</h2>
        <p>Hi {customer_name},</p>
        <p>Your order <strong>#{order_short_id}</strong> has been confirmed.</p>
        {shipping_html}
        <h3>Items</h3>
        <ul>{items_html}</ul>
        <p><strong>Total Paid:</strong> {total} ₪</p>
        <p>We will contact you shortly.</p>
        """
        send_email(customer_email, "Your order is confirmed 🎁", customer_body)

    # 5) Clear session cart/shipping but keep last_order
    session.pop("cart", None)
    session.pop("shipping", None)

    return jsonify({"status": "success"})


# =====================================================
# Success page (keep it simple / no variables needed)
# =====================================================

@app.route("/checkout-success")
def checkout_success():
    # read and remove last order from session (fallback safe object if missing)
    order = session.pop("last_order", None)
    if not order:
        order = {
            "id": "N/A",
            "items": [],
            "total": 0.0,
            "customer": {"name": "", "email": "", "address": ""}
        }

    # convert address dict to a newline string for template (nl2br filter will render <br>)
    addr = order["customer"].get("address")
    if isinstance(addr, dict):
        parts = []
        for k in ("street", "house", "apartment", "city", "postcode"):
            v = addr.get(k)
            if v:
                parts.append(str(v))
        order["customer"]["address"] = "\n".join(parts)

    return render_template("checkout_success.html", order=order)

# =====================================================
# Cart Counter
# =====================================================

@app.context_processor
def inject_cart_count():
    cart = session.get("cart", {})
    try:
        count = sum(int(v) for v in cart.values())
    except Exception:
        count = 0
    return {"cart_count": count}


# =====================================================
# Run
# =====================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
