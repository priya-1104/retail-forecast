import pytest
import os
from app import create_app
from app.database import db
from app.models.auth import User
from app.models.business import Product
from app.models.system import SystemLog
from app.config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.test_client() as client:
        with app.app_context():
            # Seed default admin and staff
            admin = User(username='testadmin', email='admin@test.com', role='Admin', is_verified=True)
            admin.set_password('AdminPass123!')
            staff = User(username='teststaff', email='staff@test.com', role='Staff', is_verified=True)
            staff.set_password('StaffPass123!')
            db.session.add(admin)
            db.session.add(staff)
            
            # Seed a default product
            prod = Product(
                name="Database Test Gadget",
                sku="SKU-DB-GADGET",
                category="Gadgets",
                price=19.99,
                quantity=50
            )
            db.session.add(prod)
            db.session.commit()
        yield client

def login_admin(client):
    """Helper to perform Admin login and verify OTP."""
    client.post('/auth/login', data={'email': 'admin@test.com', 'password': 'AdminPass123!'})
    with client.application.app_context():
        user = User.query.filter_by(email='admin@test.com').first()
        otp = user.otp_secret
    client.post('/auth/verify-otp', data={'code': otp})

def login_staff(client):
    """Helper to perform Staff login and verify OTP."""
    client.post('/auth/login', data={'email': 'staff@test.com', 'password': 'StaffPass123!'})
    with client.application.app_context():
        user = User.query.filter_by(email='staff@test.com').first()
        otp = user.otp_secret
    client.post('/auth/verify-otp', data={'code': otp})

def test_unauthorized_dashboard_access(client):
    """Tests that unauthorized guest users are blocked from DB manager."""
    response = client.get('/db/dashboard')
    assert response.status_code == 302 # Redirect to login

def test_staff_blocked_from_dashboard(client):
    """Tests that Staff users are forbidden from accessing database settings."""
    login_staff(client)
    response = client.get('/db/dashboard')
    assert response.status_code == 403

def test_admin_dashboard_telemetry(client):
    """Tests that Admin can fetch database size and telemetry stats successfully."""
    login_admin(client)
    response = client.get('/db/dashboard')
    assert response.status_code == 200
    assert b'Database Health' in response.data
    assert b'products' in response.data

def test_admin_explorer_schema(client):
    """Tests that Table Schema explorer resolves structural details."""
    login_admin(client)
    response = client.get('/db/explorer')
    assert response.status_code == 200
    assert b'products' in response.data
    assert b'users' in response.data

def test_db_explorer_dynamic_crud(client):
    """Tests dynamic reflected insert, edit, and delete operations via DB Explorer."""
    login_admin(client)
    
    # 1. ADD RECORD
    response = client.post('/db/table/products/add', data={
        'name': 'Dynamic Added Item',
        'sku': 'SKU-EXPLORER-ADD',
        'category': 'Gadgets',
        'price': '29.99',
        'quantity': '200'
    })
    assert response.status_code == 200
    assert response.get_json()['success'] is True
    
    with client.application.app_context():
        p = Product.query.filter_by(sku='SKU-EXPLORER-ADD').first()
        assert p is not None
        assert p.name == 'Dynamic Added Item'
        prod_id = p.id
        
    # 2. EDIT RECORD
    response = client.post('/db/table/products/edit', data={
        'id': str(prod_id),
        'name': 'Dynamic Updated Item',
        'sku': 'SKU-EXPLORER-ADD',
        'category': 'Gadgets',
        'price': '34.99',
        'quantity': '180'
    })
    assert response.status_code == 200
    assert response.get_json()['success'] is True
    
    with client.application.app_context():
        p = Product.query.filter_by(sku='SKU-EXPLORER-ADD').first()
        assert p.name == 'Dynamic Updated Item'
        assert p.quantity == 180
        
    # 3. DELETE RECORD
    response = client.post('/db/table/products/delete', data={
        'id': str(prod_id)
    })
    assert response.status_code == 200
    assert response.get_json()['success'] is True
    
    with client.application.app_context():
        p = Product.query.filter_by(sku='SKU-EXPLORER-ADD').first()
        assert p is None

def test_sql_console_queries(client):
    """Tests execution of raw SQL queries via the query console."""
    login_admin(client)
    
    # 1. SELECT query
    response = client.post('/db/console', data={
        'query': 'SELECT username, role FROM users ORDER BY username ASC;'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['type'] == 'select'
    assert 'username' in data['columns']
    assert data['count'] == 2
    assert data['rows'][0]['username'] == 'testadmin'
    
    # 2. COMMAND query (INSERT)
    response = client.post('/db/console', data={
        'query': 'INSERT INTO system_logs (type, message) VALUES ("Security", "Console insert test message");'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['type'] == 'command'
    assert data['rows_affected'] == 1
    
    with client.application.app_context():
        log = SystemLog.query.filter_by(type='Security').first()
        assert log is not None
        assert log.message == "Console insert test message"

def test_table_records_view_and_export(client):
    """Tests table records query pagination, search filtering, and exporting."""
    login_admin(client)
    
    # 1. Browse records page
    response = client.get('/db/table/products')
    assert response.status_code == 200
    assert b'SKU-DB-GADGET' in response.data
    
    # 2. Search record
    response = client.get('/db/table/products?search_col=sku&search_val=SKU-DB-GADGET')
    assert response.status_code == 200
    assert b'SKU-DB-GADGET' in response.data
    
    # 3. Export to CSV
    response = client.get('/db/table/products/export?format=csv')
    assert response.status_code == 200
    assert response.headers['Content-Type'].startswith('text/csv')
    assert b'SKU-DB-GADGET' in response.data
