from flask import Blueprint, jsonify, request, send_file, current_app, abort
from flask_login import login_required, current_user
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename

from app.database import db
from app.models.auth import User
from app.models.business import Product, Sale, Inventory
from app.models.forecast import Forecast, ModelMetadata
from app.models.system import Alert, Report, AuditLog
from app.services.auth_service import AuthService
from app.services.ai_engine import AIEngine
from app.services.inventory_ops import InventoryOps
from app.services.sales_service import SalesService
from app.services.report_service import ReportService

api_bp = Blueprint('api', __name__)

# ==========================================
# AUTHENTICATION API
# ==========================================

@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """REST API login endpoint returning JWT tokens for remote integrations."""
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'message': 'Missing email or password.'}), 400
        
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'message': 'Invalid email or password.'}), 401
        
    # Generate token
    token = create_access_token(identity=str(user.id))
    AuthService.log_action(user.id, 'API Login', f"User '{user.username}' authenticated via JWT")
    
    return jsonify({
        'access_token': token,
        'user': user.to_dict()
    })

@api_bp.route('/auth/profile', methods=['GET'])
@jwt_required()
def api_profile():
    """REST API endpoint returning user profile details using JWT bearer auth."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({'message': 'User not found.'}), 404
    return jsonify(user.to_dict())

# ==========================================
# DASHBOARD API
# ==========================================

@api_bp.route('/dashboard/summary', methods=['GET'])
@jwt_required()
def api_dashboard_summary():
    """Returns business summary indicators and trends in JSON format."""
    total_products = Product.query.count()
    
    revenue_query = db.session.query(db.func.sum(Sale.revenue)).scalar()
    total_revenue = float(revenue_query) if revenue_query else 0.0
    
    low_stock_count = Inventory.query.filter(
        Inventory.stock_status.in_(['Low Stock', 'Critical Low', 'Out of Stock'])
    ).count()
    
    unread_alerts = Alert.query.filter_by(is_read=False).count()
    
    # Trends for last 7 days
    today = datetime.utcnow().date()
    seven_days_ago = today - timedelta(days=7)
    sales_trend_query = db.session.query(Sale.date, db.func.sum(Sale.revenue))\
        .filter(Sale.date >= seven_days_ago)\
        .group_by(Sale.date)\
        .order_by(Sale.date).all()
    
    trend = [{'date': item[0].strftime('%Y-%m-%d'), 'revenue': float(item[1])} for item in sales_trend_query]
    
    return jsonify({
        'total_products': total_products,
        'total_revenue': total_revenue,
        'low_stock_count': low_stock_count,
        'unread_alerts_count': unread_alerts,
        'recent_sales_trend': trend
    })

# ==========================================
# PRODUCT API
# ==========================================

@api_bp.route('/products', methods=['GET'])
@jwt_required()
def api_list_products():
    """Lists all products."""
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products])

@api_bp.route('/products/<int:product_id>', methods=['GET'])
@jwt_required()
def api_get_product(product_id):
    """Retrieves a single product."""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'message': 'Product not found.'}), 404
    return jsonify(product.to_dict())

@api_bp.route('/products', methods=['POST'])
@jwt_required()
def api_create_product():
    """Adds a new product (Admin/Manager only)."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user or user.role not in ['Admin', 'Manager']:
        return jsonify({'message': 'Unauthorized role permission.'}), 403
        
    data = request.get_json() or {}
    name = data.get('name')
    sku = data.get('sku', '').strip()
    category = data.get('category')
    price = data.get('price')
    quantity = data.get('quantity')
    description = data.get('description')
    
    if not name or not sku or not category or price is None or quantity is None:
        return jsonify({'message': 'Missing required fields.'}), 400
        
    # Check duplicate SKU
    if Product.query.filter_by(sku=sku).first():
        return jsonify({'message': f"Product SKU '{sku}' already exists."}), 409
        
    try:
        product = Product(
            name=name,
            sku=sku,
            category=category,
            price=float(price),
            quantity=int(quantity),
            description=description
        )
        db.session.add(product)
        db.session.commit()
        
        # Seed default inventory
        inv = Inventory(
            product_id=product.id,
            safety_stock=10.0,
            reorder_point=25.0,
            eoq=50.0,
            stock_status="In Stock"
        )
        db.session.add(inv)
        db.session.commit()
        
        AuthService.log_action(user.id, 'API Add Product', f"Added product '{name}' (SKU: {sku})")
        return jsonify(product.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f"Error: {str(e)}"}), 500

@api_bp.route('/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def api_update_product(product_id):
    """Updates product values (Admin/Manager only)."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user or user.role not in ['Admin', 'Manager']:
        return jsonify({'message': 'Unauthorized role.'}), 403
        
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'message': 'Product not found.'}), 404
        
    data = request.get_json() or {}
    sku = data.get('sku', '').strip()
    
    if sku and sku != product.sku:
        if Product.query.filter(Product.sku == sku, Product.id != product_id).first():
            return jsonify({'message': f"SKU '{sku}' already in use."}), 409
            
    try:
        if 'name' in data: product.name = data['name']
        if 'sku' in data: product.sku = sku
        if 'category' in data: product.category = data['category']
        if 'price' in data: product.price = float(data['price'])
        if 'quantity' in data: product.quantity = int(data['quantity'])
        if 'description' in data: product.description = data['description']
        
        db.session.commit()
        AuthService.log_action(user.id, 'API Edit Product', f"Updated product '{product.name}' (SKU: {product.sku})")
        return jsonify(product.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f"Error: {str(e)}"}), 500

@api_bp.route('/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def api_delete_product(product_id):
    """Removes a product (Admin/Manager only)."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user or user.role not in ['Admin', 'Manager']:
        return jsonify({'message': 'Unauthorized.'}), 403
        
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'message': 'Product not found.'}), 404
        
    try:
        name = product.name
        sku = product.sku
        db.session.delete(product)
        db.session.commit()
        AuthService.log_action(user.id, 'API Delete Product', f"Deleted product '{name}' (SKU: {sku})")
        return jsonify({'message': f"Product '{name}' successfully deleted."})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f"Error: {str(e)}"}), 500

# ==========================================
# SALES API
# ==========================================

@api_bp.route('/sales', methods=['GET'])
@jwt_required()
def api_list_sales():
    """Lists recent sales records."""
    sales = Sale.query.order_by(Sale.date.desc()).limit(100).all()
    return jsonify([s.to_dict() for s in sales])

@api_bp.route('/sales', methods=['POST'])
@jwt_required()
def api_create_sale():
    """Logs an individual sales transaction."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user or user.role not in ['Admin', 'Manager', 'Staff']:
        return jsonify({'message': 'Unauthorized.'}), 403
        
    data = request.get_json() or {}
    product_id = data.get('product_id')
    qty = data.get('quantity_sold')
    price = data.get('price')
    date_str = data.get('date')
    
    if not product_id or not qty or not price:
        return jsonify({'message': 'Missing fields.'}), 400
        
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'message': 'Product not found.'}), 404
        
    try:
        parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()
    except ValueError:
        return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD.'}), 400
        
    try:
        sale = Sale(
            date=parsed_date,
            product_id=product.id,
            quantity_sold=int(qty),
            price=float(price),
            revenue=round(int(qty) * float(price), 2)
        )
        db.session.add(sale)
        
        # Deduct quantity from product stock
        product.quantity = max(0, product.quantity - int(qty))
        
        db.session.commit()
        
        # Check stockout triggers
        InventoryOps.calculate_optimization_metrics(product.id)
        
        AuthService.log_action(user.id, 'API Add Sale', f"Logged sale of {qty} units for product '{product.name}'")
        return jsonify(sale.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f"Error: {str(e)}"}), 500

@api_bp.route('/sales/upload', methods=['POST'])
@jwt_required()
def api_upload_sales():
    """Endpoint for uploading CSV/Excel sales sheets in bulk."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user or user.role not in ['Admin', 'Manager']:
        return jsonify({'message': 'Unauthorized.'}), 403
        
    if 'sales_file' not in request.files:
        return jsonify({'message': 'No file uploaded.'}), 400
        
    file = request.files['sales_file']
    if file.filename == '':
        return jsonify({'message': 'No file selected.'}), 400
        
    if file and SalesService.allowed_file(file.filename):
        filename = secure_filename(file.filename)
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        success, msg = SalesService.import_sales_from_file(temp_path, user.id)
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        if success:
            return jsonify({'message': msg})
        else:
            return jsonify({'message': msg}), 422
            
    return jsonify({'message': 'Invalid file extension.'}), 400

# ==========================================
# FORECAST API
# ==========================================

@api_bp.route('/forecast/<int:product_id>', methods=['GET'])
@jwt_required()
def api_get_forecast(product_id):
    """Retrieves forecast prediction values for a product."""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'message': 'Product not found.'}), 404
        
    forecasts = Forecast.query.filter(Forecast.product_id == product_id).order_by(Forecast.forecast_date).all()
    models_meta = ModelMetadata.query.filter_by(product_id=product_id).all()
    
    return jsonify({
        'product': product.to_dict(),
        'models_evaluation': [m.to_dict() for m in models_meta],
        'predictions': [f.to_dict() for f in forecasts]
    })

@api_bp.route('/forecast/train/<int:product_id>', methods=['POST'])
@jwt_required()
def api_train_forecast(product_id):
    """Triggers deep learning model training for a product."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user or user.role not in ['Admin', 'Manager']:
        return jsonify({'message': 'Unauthorized.'}), 403
        
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'message': 'Product not found.'}), 404
        
    best_model, err = AIEngine.train_and_evaluate_models(product_id)
    if err:
        return jsonify({'message': f"Training failed: {err}"}), 422
        
    # Generate default predictions
    AIEngine.generate_predictions(product_id, horizon_days=30)
    AuthService.log_action(user.id, 'API Train AI', f"Trained forecasting models for '{product.name}'. Selected: {best_model}")
    
    return jsonify({
        'message': f"Training completed. Selected best model: {best_model}",
        'selected_model': best_model
    })

# ==========================================
# INVENTORY OPTIMIZATION API
# ==========================================

@api_bp.route('/inventory', methods=['GET'])
@jwt_required()
def api_list_inventory():
    """Lists all product inventory metrics (safety stock, ROP, EOQ)."""
    inventories = Inventory.query.all()
    return jsonify([inv.to_dict() for inv in inventories])

@api_bp.route('/inventory/recalculate', methods=['POST'])
@jwt_required()
def api_recalculate_inventory():
    """Triggers inventory re-calculations for all items."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user or user.role not in ['Admin', 'Manager']:
        return jsonify({'message': 'Unauthorized.'}), 403
        
    products = Product.query.all()
    count = 0
    for p in products:
        if InventoryOps.calculate_optimization_metrics(p.id):
            count += 1
            
    AuthService.log_action(user.id, 'API Optimize Inventory', f"Recalculated safety stock metrics for {count} products")
    return jsonify({'message': f"Recalculated parameters for {count} products successfully."})

# ==========================================
# REPORTS API
# ==========================================

@api_bp.route('/reports', methods=['GET'])
@jwt_required()
def api_list_reports():
    """Lists all compiled download reports logs."""
    reports = Report.query.order_by(Report.created_at.desc()).all()
    return jsonify([r.to_dict() for r in reports])

# ==========================================
# ALERTS API
# ==========================================

@api_bp.route('/alerts/unread-count', methods=['GET'])
@login_required
def unread_count():
    """Returns number of active, unread notifications (Cookie-based session for base layout)."""
    count = Alert.query.filter_by(is_read=False).count()
    return jsonify({'unread_count': count})
