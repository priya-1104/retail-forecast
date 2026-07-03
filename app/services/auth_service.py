from flask import request
from flask_login import login_user, logout_user
import secrets
from datetime import datetime, timedelta
from app.database import db
from app.models.auth import User
from app.models.system import AuditLog

class AuthService:
    @staticmethod
    def log_action(user_id, action, description, ip_address=None):
        """Helper to create and write audit log records to the database."""
        if not ip_address:
            try:
                ip_address = request.remote_addr
            except Exception:
                ip_address = '127.0.0.1'
        
        log = AuditLog(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            description=description
        )
        db.session.add(log)
        db.session.commit()

    @classmethod
    def register_user(cls, username, email, password, role='Staff'):
        """Registers a new user, hashing their password and logging the event."""
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return None, 'Username already registered.'
        if User.query.filter_by(email=email).first():
            return None, 'Email address already registered.'
            
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Log audit action
        cls.log_action(user.id, 'Register', f"User '{username}' registered with role '{role}'")
        return user, None

    @classmethod
    def authenticate_user(cls, email, password, remember_me=False):
        """Validates credentials, logs in via Flask-Login, and logs the audit event."""
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return False, 'Invalid email or password.'
            
        # Log in the user via Flask-Login
        login_user(user, remember=remember_me)
        
        cls.log_action(user.id, 'Login', f"User '{user.username}' successfully logged in")
        return True, user

    @classmethod
    def signout_user(cls, user):
        """Logs out the user and writes an audit log."""
        if user and user.is_authenticated:
            user_id = user.id
            username = user.username
            logout_user()
            cls.log_action(user_id, 'Logout', f"User '{username}' logged out")
            return True
        return False

    @classmethod
    def generate_verification_token(cls, user):
        """Generates email verification token and simulates email delivery."""
        token = secrets.token_hex(32)
        user.verification_token = token
        db.session.commit()
        
        # Simulates sending an email
        print(f"\n==================================================")
        print(f"MOCK EMAIL: Verify Email address for user {user.username}")
        print(f"Verification URL: http://127.0.0.1:5000/auth/verify-email/{token}")
        print(f"==================================================\n")
        return token

    @classmethod
    def verify_email_token(cls, token):
        """Verifies email token and marks user as verified."""
        user = User.query.filter_by(verification_token=token).first()
        if not user:
            return False, 'Invalid verification token.'
            
        user.is_verified = True
        user.verification_token = None
        db.session.commit()
        
        cls.log_action(user.id, 'Verify Email', f"User '{user.username}' email verified")
        return True, 'Email verified successfully!'

    @classmethod
    def generate_otp(cls, user):
        """Generates a 6-digit OTP code with 10 minutes expiry."""
        otp = "".join([str(secrets.randbelow(10)) for _ in range(6)])
        user.otp_secret = otp
        user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
        db.session.commit()
        
        # Simulates sending an SMS or Email
        print(f"\n==================================================")
        print(f"MOCK SMS/OTP: One-Time Password for user {user.username}")
        print(f"Your OTP Code is: {otp} (Expires in 10 minutes)")
        print(f"==================================================\n")
        return otp

    @classmethod
    def verify_otp_code(cls, user, code):
        """Validates the 6-digit OTP code against database."""
        if not user.otp_secret or not user.otp_expiry:
            return False, 'No OTP requested or OTP has expired.'
            
        if datetime.utcnow() > user.otp_expiry:
            # Clear expired OTP
            user.otp_secret = None
            user.otp_expiry = None
            db.session.commit()
            return False, 'OTP has expired. Please request a new one.'
            
        if user.otp_secret != code:
            return False, 'Incorrect OTP code.'
            
        # OTP correct, clear it
        user.otp_secret = None
        user.otp_expiry = None
        db.session.commit()
        
        cls.log_action(user.id, 'Verify OTP', f"User '{user.username}' verified OTP")
        return True, 'OTP verified successfully!'

    @classmethod
    def generate_reset_token(cls, email):
        """Generates password reset token and prints mock URL."""
        user = User.query.filter_by(email=email).first()
        if not user:
            return False, 'No user found with that email address.'
            
        token = secrets.token_hex(32)
        user.reset_token = token
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        
        # Simulates password reset email
        print(f"\n==================================================")
        print(f"MOCK EMAIL: Reset Password for user {user.username}")
        print(f"Reset URL: http://127.0.0.1:5000/auth/reset-password/{token}")
        print(f"==================================================\n")
        return True, 'Password reset link sent to your email.'

    @classmethod
    def verify_and_reset_password(cls, token, new_password):
        """Verifies reset token, sets new password, and logs activity."""
        user = User.query.filter_by(reset_token=token).first()
        if not user or not user.reset_token_expiry:
            return False, 'Invalid password reset token.'
            
        if datetime.utcnow() > user.reset_token_expiry:
            user.reset_token = None
            user.reset_token_expiry = None
            db.session.commit()
            return False, 'Password reset token has expired.'
            
        # Reset password
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        cls.log_action(user.id, 'Reset Password', f"User '{user.username}' reset password successfully")
        return True, 'Password reset successfully! Please log in.'
