from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, send_from_directory, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.models.auth import User
from app.models.business import Product, Sale, Inventory
from app.models.forecast import Forecast
from app.models.system import Alert, AuditLog
from app.database import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Renders the landing page for guests or redirects users to dashboard."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('landing.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Renders the central analytics and operational dashboard with computed business metrics."""
    # 1. Gather Card Metrics
    total_products = Product.query.count()
    total_sales_records = Sale.query.count()
    
    # Calculate Total Revenue
    revenue_query = db.session.query(db.func.sum(Sale.revenue)).scalar()
    total_revenue = float(revenue_query) if revenue_query else 0.0
    
    # Low Stock Items Count
    low_stock_count = Inventory.query.filter(
        Inventory.stock_status.in_(['Low Stock', 'Critical Low', 'Out of Stock'])
    ).count()
    
    # Unread Alerts Count
    unread_alerts_count = Alert.query.filter_by(is_read=False).count()
    
    # Calculated Monthly Revenue (last 30 days)
    today = datetime.utcnow().date()
    thirty_days_ago = today - timedelta(days=30)
    monthly_rev_query = db.session.query(db.func.sum(Sale.revenue))\
        .filter(Sale.date >= thirty_days_ago).scalar()
    monthly_revenue = float(monthly_rev_query) if monthly_rev_query else 0.0
    
    # Predicted Future Demand (Next 30 Days)
    predicted_demand_query = db.session.query(db.func.sum(Forecast.predicted_quantity))\
        .filter(Forecast.forecast_date >= today, Forecast.forecast_date <= today + timedelta(days=30)).scalar()
    predicted_demand_qty = float(predicted_demand_query) if predicted_demand_query else 0.0
    
    # 2. Charts Data Generation
    # Chart A: Sales Trend (Daily totals for last 15 days)
    fifteen_days_ago = today - timedelta(days=15)
    sales_trend_query = db.session.query(Sale.date, db.func.sum(Sale.revenue))\
        .filter(Sale.date >= fifteen_days_ago)\
        .group_by(Sale.date)\
        .order_by(Sale.date).all()
    sales_trend = [{'date': item[0].strftime('%Y-%m-%d'), 'val': round(float(item[1]), 2)} for item in sales_trend_query]
    
    # Chart B: Category Wise Sales
    category_sales_query = db.session.query(Product.category, db.func.sum(Sale.revenue))\
        .join(Sale, Product.id == Sale.product_id)\
        .group_by(Product.category).all()
    category_sales = [{'category': item[0], 'revenue': round(float(item[1]), 2)} for item in category_sales_query]
    
    # Chart C: Top 5 Products by Revenue
    top_products_query = db.session.query(Product.name, db.func.sum(Sale.revenue))\
        .join(Sale, Product.id == Sale.product_id)\
        .group_by(Product.name)\
        .order_by(db.func.sum(Sale.revenue).desc())\
        .limit(5).all()
    top_products = [{'name': item[0], 'revenue': round(float(item[1]), 2)} for item in top_products_query]
    
    # Chart D: Forecast vs Actual comparison for a sample product (e.g. Wireless Headset if exists)
    sample_prod = Product.query.first()
    forecast_comparison = []
    if sample_prod:
        forecast_comp_query = Forecast.query.filter(
            Forecast.product_id == sample_prod.id,
            Forecast.forecast_date >= today
        ).order_by(Forecast.forecast_date).limit(7).all()
        forecast_comparison = [{'date': f.forecast_date.strftime('%Y-%m-%d'), 'qty': f.predicted_quantity} for f in forecast_comp_query]

    # Render Dashboard
    return render_template(
        'dashboard.html',
        total_products=total_products,
        total_sales_records=total_sales_records,
        total_revenue=total_revenue,
        monthly_revenue=monthly_revenue,
        low_stock_count=low_stock_count,
        unread_alerts_count=unread_alerts_count,
        predicted_demand_qty=predicted_demand_qty,
        sales_trend=sales_trend,
        category_sales=category_sales,
        top_products=top_products,
        forecast_comparison=forecast_comparison,
        sample_product_name=sample_prod.name if sample_prod else 'N/A'
    )

@main_bp.route('/users', methods=['GET', 'POST'])
@login_required
def users_panel():
    """Enables administrators to view user roles and delete accounts."""
    if current_user.role != 'Admin':
        abort(403)
        
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role', 'Staff')
            
            user, err = AuthService.register_user(username, email, password, role)
            if user:
                # Admin-created users are automatically marked as email-verified
                user.is_verified = True
                db.session.commit()
                flash(f"User '{username}' created successfully.", 'success')
            else:
                flash(err, 'danger')
        else:
            user_id = request.form.get('user_id')
            target_user = User.query.get(user_id)
            if not target_user:
                flash('Target user not found.', 'danger')
            elif target_user.id == current_user.id:
                flash('You cannot perform actions on your own account.', 'warning')
            else:
                if action == 'delete':
                    db.session.delete(target_user)
                    db.session.commit()
                    flash(f"User '{target_user.username}' deleted successfully.", 'success')
                elif action == 'edit':
                    username = request.form.get('username')
                    email = request.form.get('email')
                    role = request.form.get('role', 'Staff')
                    
                    dup_u = User.query.filter(User.username == username, User.id != target_user.id).first()
                    dup_e = User.query.filter(User.email == email, User.id != target_user.id).first()
                    
                    if dup_u:
                        flash('Username already registered.', 'danger')
                    elif dup_e:
                        flash('Email address already registered.', 'danger')
                    else:
                        target_user.username = username
                        target_user.email = email
                        target_user.role = role
                        db.session.commit()
                        flash(f"User '{username}' updated successfully.", 'success')
                elif action == 'promote':
                    new_role = request.form.get('role', 'Staff')
                    target_user.role = new_role
                    db.session.commit()
                    flash(f"User '{target_user.username}' role updated to '{new_role}'.", 'success')
                
    users = User.query.all()
    return render_template('users.html', users=users)

@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings_panel():
    """Renders user preferences and displays recent activity audit logs."""
    logs = AuditLog.query.filter_by(user_id=current_user.id).order_by(AuditLog.created_at.desc()).limit(15).all()
    return render_template('settings.html', logs=logs)

@main_bp.route('/manifest.json')
def serve_manifest():
    """Serves the PWA manifest.json from static assets."""
    return send_from_directory(current_app.static_folder, 'manifest.json')

@main_bp.route('/sw.js')
def serve_sw():
    """Serves the service worker sw.js from static assets with disabled browser cache."""
    response = send_from_directory(current_app.static_folder, 'sw.js')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response
