from flask import Flask, render_template, abort
from auth.routes import auth_bp
from admin_dashboard.routes import admin_bp
import json
import os

app = Flask(__name__)
app.config.from_object('config.Config')

# -----------------------
# Load Products
# -----------------------
def load_products():
    path = os.path.join(os.path.dirname(__file__), 'data', 'products.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_product(product_id):
    products = load_products()
    for p in products:
        if p["id"] == product_id:
            return p
    return None

# -----------------------
# Register Blueprints
# -----------------------
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')

# -----------------------
# Home Page
# -----------------------
@app.route('/')
def home():
    return render_template('home.html')

# -----------------------
# Catalog Page
# -----------------------
@app.route('/collection')
def collection():
    products = load_products()
    return render_template('jewelry_collection.html', products=products)

# -----------------------
# Category Page (Rings / Necklaces / etc.)
# -----------------------
@app.route('/collection/<category>')
def category_page(category):
    products = [p for p in load_products() if p.get("category") == category]
    if not products:
        abort(404)
    return render_template('jewelry_collection.html', products=products, category=category)

# -----------------------
# Product Detail Page
# -----------------------
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = get_product(product_id)
    if not product:
        abort(404)
    return render_template('jewelry_detail.html', product=product)

# -----------------------
# Run Server
# -----------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
