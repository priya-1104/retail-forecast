import pytest
from app import create_app
from app.database import db
from app.models.auth import User
from app.config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False  # Disable CSRF for simplified test requests

@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.test_client() as client:
        with app.app_context():
            # Seed a default admin and staff
            admin = User(username='testadmin', email='admin@test.com', role='Admin', is_verified=True)
            admin.set_password('AdminPass123!')
            staff = User(username='teststaff', email='staff@test.com', role='Staff', is_verified=True)
            staff.set_password('StaffPass123!')
            db.session.add(admin)
            db.session.add(staff)
            db.session.commit()
        yield client

def test_registration(client):
    """Tests that a new user can register successfully."""
    response = client.post('/auth/register', data={
        'username': 'newuser',
        'email': 'new@test.com',
        'password': 'NewUserPass123!',
        'role': 'Staff'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Your account has been created successfully' in response.data

def test_duplicate_registration(client):
    """Tests that registering an existing username/email fails."""
    response = client.post('/auth/register', data={
        'username': 'teststaff',
        'email': 'staff@test.com',
        'password': 'StaffPass123!',
        'role': 'Staff'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Username already registered' in response.data or b'Email address already registered' in response.data

def test_login_success(client):
    """Tests successful user sign-in and OTP 2FA verification."""
    # 1. Submit login credentials (should prompt for OTP)
    response = client.post('/auth/login', data={
        'email': 'staff@test.com',
        'password': 'StaffPass123!'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'enter the 6-digit OTP code' in response.data
    
    # 2. Retrieve OTP from the database in app context
    with client.application.app_context():
        user = User.query.filter_by(email='staff@test.com').first()
        otp = user.otp_secret
        assert otp is not None
        
    # 3. Verify OTP
    response = client.post('/auth/verify-otp', data={
        'code': otp
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'OTP verified successfully' in response.data

def test_login_failure(client):
    """Tests user sign-in with incorrect password."""
    response = client.post('/auth/login', data={
        'email': 'staff@test.com',
        'password': 'WrongPassword'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Invalid email or password' in response.data

def test_logout(client):
    """Tests user log-out."""
    # 1. Login and OTP Verify
    client.post('/auth/login', data={
        'email': 'staff@test.com',
        'password': 'StaffPass123!'
    })
    with client.application.app_context():
        user = User.query.filter_by(email='staff@test.com').first()
        otp = user.otp_secret
    client.post('/auth/verify-otp', data={'code': otp})
    
    # 2. Logout
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out successfully' in response.data

def test_admin_only_access(client):
    """Tests that non-admins cannot access admin user manager panel."""
    # 1. Login as Staff
    client.post('/auth/login', data={
        'email': 'staff@test.com',
        'password': 'StaffPass123!'
    })
    with client.application.app_context():
        user = User.query.filter_by(email='staff@test.com').first()
        otp = user.otp_secret
    client.post('/auth/verify-otp', data={'code': otp})
    
    # Try to access users list (should get 403)
    response = client.get('/users')
    assert response.status_code == 403
    
    # Log out
    client.get('/auth/logout')
    
    # 2. Login as Admin
    client.post('/auth/login', data={
        'email': 'admin@test.com',
        'password': 'AdminPass123!'
    })
    with client.application.app_context():
        user = User.query.filter_by(email='admin@test.com').first()
        otp = user.otp_secret
    client.post('/auth/verify-otp', data={'code': otp})
    
    # Try again (should get 200)
    response = client.get('/users')
    assert response.status_code == 200
    assert b'Registered Users' in response.data
