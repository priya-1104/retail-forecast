from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.database import db
from app.models.business import Product, Sale
from app.models.forecast import Forecast, ModelMetadata
from app.services.ai_engine import AIEngine
from app.services.auth_service import AuthService

forecasting_bp = Blueprint('forecasting', __name__)

@forecasting_bp.route('/')
@login_required
def forecast_panel():
    """Renders the AI forecasting overview, listing trained models and metrics."""
    products = Product.query.all()
    # Find products that have at least one trained model
    trained_skus = [m.product_id for m in ModelMetadata.query.filter_by(is_best_model=True).all()]
    return render_template('forecasting.html', products=products, trained_skus=trained_skus)

@forecasting_bp.route('/train/<int:product_id>', methods=['POST'])
@login_required
def train_models(product_id):
    """Triggers LSTM/GRU/Prophet training, calculates metrics, and updates best model."""
    if current_user.role not in ['Admin', 'Manager']:
        abort(403)
        
    product = Product.query.get_or_404(product_id)
    
    # Train
    best_model, err = AIEngine.train_and_evaluate_models(product_id)
    
    if err:
        flash(f"Training failed for '{product.name}': {err}", 'danger')
    else:
        # Pre-generate standard 30-day forecast with the new best model
        AIEngine.generate_predictions(product_id, horizon_days=30)
        AuthService.log_action(current_user.id, 'Train AI', f"Trained forecasting models for '{product.name}'. Selected: {best_model}")
        flash(f"Successfully trained models for '{product.name}'! Best model selected: {best_model}.", 'success')
        
    return redirect(url_for('forecasting.forecast_panel'))

@forecasting_bp.route('/view/<int:product_id>')
@login_required
def view_forecast(product_id):
    """Renders detailed predictions charts and metrics for a specific product."""
    product = Product.query.get_or_404(product_id)
    horizon = request.args.get('horizon', 30, type=int)
    
    # Generate predictions if none exist
    today = datetime.utcnow().date()
    forecasts = Forecast.query.filter(Forecast.product_id == product_id, Forecast.forecast_date >= today).all()
    
    if not forecasts:
        success, err = AIEngine.generate_predictions(product_id, horizon_days=horizon)
        if not success:
            flash(f"Could not generate forecast: {err}", 'warning')
            return redirect(url_for('forecasting.forecast_panel'))
        forecasts = Forecast.query.filter(Forecast.product_id == product_id, Forecast.forecast_date >= today).all()
        
    # Query model metrics
    models_meta = ModelMetadata.query.filter_by(product_id=product_id).all()
    best_model = next((m for m in models_meta if m.is_best_model), None)
    
    # Fetch historical sales (last 60 days) to display on chart
    cutoff_date = today - timedelta(days=60)
    sales = Sale.query.filter(Sale.product_id == product_id, Sale.date >= cutoff_date).order_by(Sale.date).all()
    
    # Format data for chart
    chart_history = [{'x': s.date.strftime('%Y-%m-%d'), 'y': s.quantity_sold} for s in sales]
    chart_forecast = [{'x': f.forecast_date.strftime('%Y-%m-%d'), 'y': f.predicted_quantity} for f in forecasts[:horizon]]
    
    return render_template(
        'view_forecast.html',
        product=product,
        models_meta=models_meta,
        best_model=best_model,
        chart_history=chart_history,
        chart_forecast=chart_forecast,
        horizon=horizon
    )

@forecasting_bp.route('/generate/<int:product_id>', methods=['POST'])
@login_required
def generate_forecast(product_id):
    """API endpoint to re-generate predictions for a dynamic horizon."""
    if current_user.role not in ['Admin', 'Manager']:
        abort(403)
        
    horizon = request.form.get('horizon', 30, type=int)
    success, err = AIEngine.generate_predictions(product_id, horizon_days=horizon)
    
    if success:
        flash(f"Regenerated {horizon}-day forecast successfully.", 'success')
    else:
        flash(f"Failed to generate forecast: {err}", 'danger')
        
    return redirect(url_for('forecasting.view_forecast', product_id=product_id, horizon=horizon))
