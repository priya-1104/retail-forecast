import pytest
from datetime import datetime, date, timedelta
from app import create_app
from app.database import db
from app.models.auth import User
from app.models.business import Product, Sale, Brand, Supplier, Warehouse, Customer, PurchaseOrder, StockTransfer
from app.models.hr import Employee, Attendance
from app.config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

@pytest.fixture
def app_ctx():
    app = create_app(TestConfig)
    with app.app_context():
        # Tables are created conditionally by app factory in testing mode
        yield app

def test_hr_models(app_ctx):
    """Tests saving Employee and Attendance logs and checks working hours calculations."""
    # 1. Create Employee
    emp = Employee(
        employee_id="EMP-9999",
        name="John Doe",
        department="Engineering",
        designation="Software Architect",
        salary=120000.0,
        shift="Day"
    )
    db.session.add(emp)
    db.session.commit()
    
    saved_emp = Employee.query.filter_by(employee_id="EMP-9999").first()
    assert saved_emp is not None
    assert saved_emp.name == "John Doe"
    assert saved_emp.status == "Active"
    
    # 2. Log Attendance
    today = date.today()
    check_in_time = datetime(today.year, today.month, today.day, 9, 0, 0)
    check_out_time = datetime(today.year, today.month, today.day, 17, 30, 0) # 8.5 hours
    
    att = Attendance(
        employee_id=saved_emp.id,
        date=today,
        check_in=check_in_time,
        check_out=check_out_time,
        working_hours=8.5,
        overtime_hours=0.5
    )
    db.session.add(att)
    db.session.commit()
    
    saved_att = Attendance.query.filter_by(employee_id=saved_emp.id).first()
    assert saved_att is not None
    assert saved_att.working_hours == 8.5
    assert saved_att.overtime_hours == 0.5

def test_enterprise_relations(app_ctx):
    """Tests product metadata expansion (Brands, Suppliers, Warehouses)."""
    # 1. Create Brand
    brand = Brand(name="Logitech", manufacturer="Logitech Inc.", description="Computer peripherals")
    # 2. Create Supplier
    supplier = Supplier(name="Global Distributing", email="orders@global.com", phone="12345678", rating=4.8)
    # 3. Create Warehouse
    warehouse = Warehouse(name="North Central Hub", location="Building B, Section 4", capacity_sqft=50000)
    
    db.session.add_all([brand, supplier, warehouse])
    db.session.commit()
    
    # 4. Create Product with links
    prod = Product(
        name="MX Master 3S Mouse",
        sku="SKU-MX-MOUSE",
        category="Peripherals",
        price=99.99,
        quantity=100,
        brand_id=brand.id,
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        barcode="097855170360",
        unit="pcs"
    )
    db.session.add(prod)
    db.session.commit()
    
    saved_prod = Product.query.filter_by(sku="SKU-MX-MOUSE").first()
    assert saved_prod is not None
    assert saved_prod.brand.name == "Logitech"
    assert saved_prod.supplier.name == "Global Distributing"
    assert saved_prod.warehouse.name == "North Central Hub"
    assert saved_prod.unit == "pcs"

def test_purchase_orders_and_transfers(app_ctx):
    """Tests PurchaseOrder and StockTransfer tracking."""
    # Seed base elements
    supplier = Supplier(name="Electronics Inc.")
    source_wh = Warehouse(name="Primary Warehouse")
    dest_wh = Warehouse(name="Outlet Store")
    db.session.add_all([supplier, source_wh, dest_wh])
    db.session.commit()
    
    prod = Product(
        name="Wireless Keyboard",
        sku="SKU-KB-WIRELESS",
        category="Accessories",
        price=49.99,
        quantity=50,
        warehouse_id=source_wh.id
    )
    db.session.add(prod)
    db.session.commit()
    
    # 1. Test Purchase Order
    po = PurchaseOrder(
        product_id=prod.id,
        supplier_id=supplier.id,
        warehouse_id=source_wh.id,
        quantity=100,
        order_date=date.today(),
        status='Pending',
        total_amount=4999.00
    )
    db.session.add(po)
    db.session.commit()
    
    saved_po = PurchaseOrder.query.filter_by(product_id=prod.id).first()
    assert saved_po is not None
    assert saved_po.quantity == 100
    assert saved_po.status == 'Pending'
    
    # 2. Test Stock Transfer
    transfer = StockTransfer(
        product_id=prod.id,
        source_warehouse_id=source_wh.id,
        dest_warehouse_id=dest_wh.id,
        quantity=20,
        status='Pending'
    )
    db.session.add(transfer)
    db.session.commit()
    
    saved_tr = StockTransfer.query.filter_by(product_id=prod.id).first()
    assert saved_tr is not None
    assert saved_tr.quantity == 20
    assert saved_tr.status == 'Pending'

def test_customer_sales(app_ctx):
    """Tests Customer membership and links to purchase logs."""
    cust = Customer(name="Alice Green", email="alice@test.com", membership_tier="Silver", loyalty_points=120)
    db.session.add(cust)
    db.session.commit()
    
    prod = Product(name="Smart Thermostat", sku="SKU-THERM", category="Smart Home", price=150.00, quantity=10)
    db.session.add(prod)
    db.session.commit()
    
    # Log Sale with Customer ID
    sale = Sale(
        date=date.today(),
        product_id=prod.id,
        quantity_sold=1,
        price=150.00,
        revenue=150.00,
        customer_id=cust.id
    )
    db.session.add(sale)
    db.session.commit()
    
    saved_cust = Customer.query.filter_by(name="Alice Green").first()
    assert saved_cust is not None
    assert saved_cust.sales.count() == 1
    assert saved_cust.sales.first().revenue == 150.00
