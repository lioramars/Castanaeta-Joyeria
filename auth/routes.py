from flask import Blueprint, render_template, redirect, url_for, request, flash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        flash('Login functionality coming soon.', 'error')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        flash('Registration functionality coming soon.', 'error')
    return render_template('auth/register.html')

@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    return redirect(url_for('auth.login'))
