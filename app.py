from flask import Flask
from auth.routes import auth_bp
from admin_dashboard.routes import admin_bp

app = Flask(__name__)
app.config.from_object('config.Config')

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
