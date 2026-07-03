from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user, login_user, logout_user
from app.services.auth_service import AuthService
from app.models.auth import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handles web user sign-in processes and redirects to OTP verification."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember_me') else False
        
        success, res = AuthService.authenticate_user(email, password, remember)
        if success:
            user = res
            # Generate OTP code for 2FA
            AuthService.generate_otp(user)
            
            # Temporarily store credentials and logout until OTP is verified
            session['otp_user_id'] = user.id
            session['remember_me'] = remember
            logout_user()
            
            flash('Sign-in authenticated. Please enter the 6-digit OTP code sent to your device/console.', 'info')
            return redirect(url_for('auth.verify_otp'))
        else:
            flash(res, 'danger')
            
    return render_template('auth/login.html')

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """Verifies the 2FA OTP code and completes user sign-in."""
    user_id = session.get('otp_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
        
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        code = request.form.get('code')
        success, msg = AuthService.verify_otp_code(user, code)
        if success:
            # Login user completely
            login_user(user, remember=session.get('remember_me', False))
            session.pop('otp_user_id', None)
            session.pop('remember_me', None)
            flash('OTP verified successfully. Welcome back!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash(msg, 'danger')
            
    return render_template('auth/verify_otp.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handles web account creation workflows and triggers email verification."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'Staff')
        
        user, err = AuthService.register_user(username, email, password, role)
        if user:
            # Trigger email verification token
            AuthService.generate_verification_token(user)
            flash('Your account has been created successfully! A verification link has been sent (check logs). Please verify before logging in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(err, 'danger')
            
    return render_template('auth/register.html')

@auth_bp.route('/verify-email/<token>', methods=['GET'])
def verify_email(token):
    """Verifies user email using the verification token."""
    success, msg = AuthService.verify_email_token(token)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Triggers password reset link generation and delivery."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        success, msg = AuthService.generate_reset_token(email)
        if success:
            flash(msg, 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(msg, 'danger')
            
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Validates reset token and modifies user password."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        success, msg = AuthService.verify_and_reset_password(token, password)
        if success:
            flash(msg, 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(msg, 'danger')
            
    return render_template('auth/reset_password.html', token=token)

@auth_bp.route('/logout')
@login_required
def logout():
    """Sign-out user and redirect to login page."""
    AuthService.signout_user(current_user)
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
