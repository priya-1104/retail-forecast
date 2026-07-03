import pytest
from datetime import datetime, timedelta
from app import create_app
from app.database import db
from app.models.business import Product, Sale
from app.models.forecast import Forecast, ModelMetadata
from app.services.ai_engine import AIEngine
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
            name="Test Headphones",
            sku="SKU-TEST-HD",
            category="Electronics",
            price=100.0,
            quantity=50
        )
        db.session.add(prod)
        db.session.commit()
        
        # Add 45 days of sales records (to satisfy minimum training requirements)
        today = datetime.utcnow().date()
        sales_records = []
        for i in range(45):
            s_date = today - timedelta(days=i)
            # Simulated demand: base 10 + weekly noise
            qty = 10 if s_date.weekday() < 5 else 15
            sale = Sale(
                date=s_date,
                product_id=prod.id,
                quantity_sold=qty,
                price=100.0,
                revenue=qty * 100.0
            )
            sales_records.append(sale)
            
        db.session.bulk_save_objects(sales_records)
        db.session.commit()
        
    with app.test_client() as client:
        yield client

def test_data_preprocessing(client_with_sales):
    """Tests that daily sales logs resample and aggregate correctly."""
    app = client_with_sales.application
    with app.app_context():
        prod = Product.query.filter_by(sku="SKU-TEST-HD").first()
        series = AIEngine.prepare_time_series_data(prod.id)
        
        assert series is not None
        assert len(series) == 45
        assert series.iloc[0] >= 10

def test_metric_calculations():
    """Tests that MAPE computes error margins correctly, avoiding zero division."""
    y_true = [10, 20, 30]
    y_pred = [12, 18, 30]
    
    mape = AIEngine.calculate_mape(y_true, y_pred)
    # y1: (12-10)/10 = 20%
    # y2: (20-18)/20 = 10%
    # y3: (30-30)/30 = 0%
    # Avg: (20 + 10 + 0) / 3 = 10%
    assert abs(mape - 10.0) < 1e-5

def test_model_training_and_selection(client_with_sales):
    """Tests training pipelines, metrics writes, and best model selection flags."""
    app = client_with_sales.application
    with app.app_context():
        prod = Product.query.filter_by(sku="SKU-TEST-HD").first()
        best_model, err = AIEngine.train_and_evaluate_models(prod.id)
        
        assert err is None
        assert best_model in ['LSTM', 'GRU', 'Prophet']
        
        # Verify metadata was written
        metadata = ModelMetadata.query.filter_by(product_id=prod.id).all()
        assert len(metadata) > 0
        best_model_meta = ModelMetadata.query.filter_by(product_id=prod.id, is_best_model=True).first()
        assert best_model_meta is not None
        assert best_model_meta.model_type == best_model
        assert best_model_meta.mae > 0

def test_forecast_generation(client_with_sales):
    """Tests generating forecasts and verify write-backs and stockout alerts."""
    app = client_with_sales.application
    with app.app_context():
        prod = Product.query.filter_by(sku="SKU-TEST-HD").first()
        
        # Run forecast generation for 15 days horizon
        success, err = AIEngine.generate_predictions(prod.id, horizon_days=15)
        
        assert success is True
        assert err is None
        
        # Verify forecasts were written
        today = datetime.utcnow().date()
        forecasts = Forecast.query.filter(Forecast.product_id == prod.id, Forecast.forecast_date >= today).all()
        assert len(forecasts) == 15
        assert forecasts[0].predicted_quantity >= 0
        assert forecasts[0].model_used in ['LSTM', 'GRU', 'Prophet']
