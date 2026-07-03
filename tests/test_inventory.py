import pytest
from datetime import datetime, timedelta
from app import create_app
from app.database import db
from app.models.business import Product, Sale, Inventory
from app.models.system import Alert
from app.services.inventory_ops import InventoryOps
from app.config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

@pytest.fixture
def client_with_sales():
    app = create_app(TestConfig)
    with app.app_context():
        # Setup Product
        prod = Product(
            name="Test Widget",
            sku="SKU-TEST-WIDGET",
            category="Appliances",
            price=50.0,
            quantity=15  # low quantity to trigger low stock warning
        )
        db.session.add(prod)
        db.session.commit()
        
        # Add 10 days of sales records (average daily sales = 10 units, max = 20)
        today = datetime.utcnow().date()
        sales_records = []
        for i in range(10):
            qty = 10 if i % 2 == 0 else 20
            sale = Sale(
                date=today - timedelta(days=i),
                product_id=prod.id,
                quantity_sold=qty,
                price=50.0,
                revenue=qty * 50.0
            )
            sales_records.append(sale)
            
        db.session.bulk_save_objects(sales_records)
        db.session.commit()
        
    with app.test_client() as client:
        yield client

def test_inventory_optimization_calculations(client_with_sales):
    """Tests ROP, Safety Stock, and EOQ values against simulated sales history."""
    app = client_with_sales.application
    with app.app_context():
        prod = Product.query.filter_by(sku="SKU-TEST-WIDGET").first()
        
        # Run optimization calculations
        # Default lead_time=5, max_lead_time=10
        # Sales: 10 days. Total sales = 150 units. Avg Daily = 15. Max Daily = 20.
        # Safety Stock = (Max * MaxLead) - (Avg * AvgLead) = (20 * 10) - (15 * 5) = 200 - 75 = 125
        # ROP = (Avg * AvgLead) + Safety Stock = 75 + 125 = 200
        # Annual Demand D = 15 * 365 = 5475
        # Holding Cost H = 0.18 * 50 = 9.0
        # Ordering Cost S = 15
        # EOQ = sqrt((2 * 5475 * 15) / 9.0) = sqrt(164250 / 9) = sqrt(18250) ≈ 135
        
        inv = InventoryOps.calculate_optimization_metrics(prod.id)
        
        assert inv is not None
        assert abs(inv.safety_stock - 125.0) < 1.0
        assert abs(inv.reorder_point - 200.0) < 1.0
        assert abs(inv.eoq - 135.1) < 1.0
        assert inv.stock_status == "Critical Low"  # Since current quantity is 15 (which is <= safety_stock of 125)

def test_alert_generation(client_with_sales):
    """Tests that low stock results in automatic Alert creation."""
    app = client_with_sales.application
    with app.app_context():
        prod = Product.query.filter_by(sku="SKU-TEST-WIDGET").first()
        
        # Clear existing alerts
        Alert.query.delete()
        db.session.commit()
        
        # Recalculate which should trigger low stock alert
        InventoryOps.calculate_optimization_metrics(prod.id)
        
        # Verify alert was created
        alert = Alert.query.filter_by(product_id=prod.id, type="Low Stock").first()
        assert alert is not None
        assert "Critical Low" in alert.message
        assert str(prod.quantity) in alert.message
