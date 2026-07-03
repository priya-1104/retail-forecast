import pytest
from datetime import datetime, timedelta
from app import create_app
from app.database import db
from app.models.auth import User
from app.models.business import Product, Sale
from app.config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    JWT_SECRET_KEY = 'test_jwt_secret_key'

@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.test_client() as client:
        with app.app_context():
            # Seed users
            admin = User(username='apiadmin', email='apiadmin@test.com', role='Admin', is_verified=True)
            admin.set_password('AdminPass123!')
            staff = User(username='apistaff', email='apistaff@test.com', role='Staff', is_verified=True)
            staff.set_password('StaffPass123!')
            
            # Seed product
            prod = Product(
                name="API Test Laptop",
                sku="SKU-API-LAPTOP",
                category="Electronics",
                price=1000.0,
                quantity=10
            )
            
            db.session.add(admin)
            db.session.add(staff)
            db.session.add(prod)
            db.session.commit()
        yield client

def test_api_login_success(client):
    """Tests logging in via REST API and retrieving a JWT token."""
    response = client.post('/api/auth/login', json={
        'email': 'apiadmin@test.com',
        'password': 'AdminPass123!'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data
    assert data['user']['username'] == 'apiadmin'

def test_api_login_failure(client):
    """Tests logging in with incorrect credentials."""
    response = client.post('/api/auth/login', json={
        'email': 'apiadmin@test.com',
        'password': 'WrongPassword'
    })
    
    assert response.status_code == 401
    assert b'Invalid email or password' in response.data

def test_api_get_profile(client):
    """Tests fetching profile details using a JWT Bearer token."""
    # 1. Login
    login_res = client.post('/api/auth/login', json={
        'email': 'apiadmin@test.com',
        'password': 'AdminPass123!'
    })
    token = login_res.get_json()['access_token']
    
    # 2. Fetch Profile without token (should get 401)
    res_no_token = client.get('/api/auth/profile')
    assert res_no_token.status_code == 401
    
    # 3. Fetch Profile with token
    res_with_token = client.get('/api/auth/profile', headers={
        'Authorization': f'Bearer {token}'
    })
    assert res_with_token.status_code == 200
    data = res_with_token.get_json()
    assert data['username'] == 'apiadmin'
    assert data['role'] == 'Admin'

def test_api_dashboard_summary(client):
    """Tests retrieval of dashboard parameters."""
    login_res = client.post('/api/auth/login', json={
        'email': 'apiadmin@test.com',
        'password': 'AdminPass123!'
    })
    token = login_res.get_json()['access_token']
    
    response = client.get('/api/dashboard/summary', headers={
        'Authorization': f'Bearer {token}'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['total_products'] == 1
    assert 'total_revenue' in data
    assert 'low_stock_count' in data

def test_api_product_crud(client):
    """Tests full Product CRUD via API routes."""
    # 1. Login as Admin
    login_res = client.post('/api/auth/login', json={
        'email': 'apiadmin@test.com',
        'password': 'AdminPass123!'
    })
    token = login_res.get_json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # 2. Get all products
    get_res = client.get('/api/products', headers=headers)
    assert get_res.status_code == 200
    assert len(get_res.get_json()) == 1
    
    # 3. Create product
    create_res = client.post('/api/products', json={
        'name': 'API Smartphone',
        'sku': 'SKU-API-PHONE',
        'category': 'Electronics',
        'price': 499.99,
        'quantity': 30,
        'description': 'A smartphone'
    }, headers=headers)
    assert create_res.status_code == 201
    new_prod_id = create_res.get_json()['id']
    
    # 4. Get single product
    single_res = client.get(f'/api/products/{new_prod_id}', headers=headers)
    assert single_res.status_code == 200
    assert single_res.get_json()['name'] == 'API Smartphone'
    
    # 5. Update product
    update_res = client.put(f'/api/products/{new_prod_id}', json={
        'price': 449.99,
        'quantity': 25
    }, headers=headers)
    assert update_res.status_code == 200
    assert update_res.get_json()['price'] == 449.99
    
    # 6. Delete product
    delete_res = client.delete(f'/api/products/{new_prod_id}', headers=headers)
    assert delete_res.status_code == 200
    
    # Confirm deletion
    check_deleted = client.get(f'/api/products/{new_prod_id}', headers=headers)
    assert check_deleted.status_code == 404

def test_api_sales_crud(client):
    """Tests logging and querying sales transactions via API."""
    # 1. Login as Staff
    login_res = client.post('/api/auth/login', json={
        'email': 'apistaff@test.com',
        'password': 'StaffPass123!'
    })
    token = login_res.get_json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Fetch product ID
    with client.application.app_context():
        prod = Product.query.filter_by(sku="SKU-API-LAPTOP").first()
        prod_id = prod.id
        
    # 2. Post a sale
    sale_res = client.post('/api/sales', json={
        'product_id': prod_id,
        'quantity_sold': 2,
        'price': 1000.0,
        'date': '2026-06-26'
    }, headers=headers)
    assert sale_res.status_code == 201
    
    # Verify stock reduction
    with client.application.app_context():
        p = Product.query.get(prod_id)
        assert p.quantity == 8  # 10 - 2
        
    # 3. List sales
    list_res = client.get('/api/sales', headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.get_json()) == 1
    assert list_res.get_json()[0]['quantity_sold'] == 2

def test_api_inventory_recalculate(client):
    """Tests inventory recalculations via API."""
    login_res = client.post('/api/auth/login', json={
        'email': 'apiadmin@test.com',
        'password': 'AdminPass123!'
    })
    token = login_res.get_json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    response = client.post('/api/inventory/recalculate', headers=headers)
    assert response.status_code == 200
    assert b'Recalculated parameters' in response.data
