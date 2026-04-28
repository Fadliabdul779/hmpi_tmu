from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'member':
            return redirect(url_for('main.index'))
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            if user.is_active:
                login_user(user, remember=remember)
                next_page = request.args.get('next')
                flash('Login successful!', 'success')
                if user.role == 'member':
                    return redirect(next_page or url_for('main.index'))
                return redirect(next_page or url_for('admin.dashboard'))
            else:
                flash('Account deactivated. Contact admin.', 'danger')
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/member-login', methods=['GET', 'POST'])
def member_login():
    """Login page specifically for members"""
    if current_user.is_authenticated:
        if current_user.role == 'member':
            return redirect(url_for('main.index'))
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            if user.is_active:
                if user.role != 'member':
                    flash('Login successful! Redirecting to appropriate dashboard...', 'info')
                    login_user(user, remember=remember)
                    return redirect(url_for('admin.dashboard'))
                login_user(user, remember=remember)
                next_page = request.args.get('next')
                flash('Login successful!', 'success')
                return redirect(next_page or url_for('main.index'))
            else:
                flash('Account deactivated. Contact admin.', 'danger')
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login-member.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))
