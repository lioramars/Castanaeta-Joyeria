import os

class Config:
    # Flask
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

    # Admin
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
    ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")

    # Uploads
    UPLOAD_FOLDER = "static/img/uploads"

    # PayPal
    PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
    PAYPAL_SECRET = os.getenv("PAYPAL_SECRET")
    PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")
