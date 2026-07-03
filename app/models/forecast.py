from datetime import datetime
from app.database import db

class Forecast(db.Model):
    __tablename__ = 'forecasts'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    forecast_date = db.Column(db.Date, nullable=False, index=True)
    predicted_quantity = db.Column(db.Float, nullable=False)
    model_used = db.Column(db.String(32), nullable=False)  # LSTM, GRU, Prophet
    horizon_days = db.Column(db.Integer, nullable=False)  # 7, 30, 90, 180
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'forecast_date': self.forecast_date.isoformat(),
            'predicted_quantity': self.predicted_quantity,
            'model_used': self.model_used,
            'horizon_days': self.horizon_days,
            'created_at': self.created_at.isoformat()
        }

class ModelMetadata(db.Model):
    __tablename__ = 'model_metadata'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    model_type = db.Column(db.String(32), nullable=False)  # LSTM, GRU, Prophet
    mae = db.Column(db.Float, nullable=True)
    rmse = db.Column(db.Float, nullable=True)
    mape = db.Column(db.Float, nullable=True)
    r2_score = db.Column(db.Float, nullable=True)
    is_best_model = db.Column(db.Boolean, default=False)
    trained_at = db.Column(db.DateTime, default=datetime.utcnow)
    model_path = db.Column(db.String(256), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'model_type': self.model_type,
            'mae': self.mae,
            'rmse': self.rmse,
            'mape': self.mape,
            'r2_score': self.r2_score,
            'is_best_model': self.is_best_model,
            'trained_at': self.trained_at.isoformat(),
            'model_path': self.model_path
        }
