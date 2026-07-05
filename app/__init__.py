from flask import Flask, jsonify
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from app.config import Config
from app.database import db

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'

jwt = JWTManager()
csrf = CSRFProtect()
migrate = Migrate()

@login_manager.user_loader
def load_user(user_id):
    from app.models.auth import User
    return User.query.get(int(user_id))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    config_class.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    jwt.init_app(app)
    csrf.init_app(app)
    
    # Register blueprints (imported inside to avoid circular dependencies)
    from app.models import User, Product, Sale, Inventory, Forecast, ModelMetadata, Alert, Report, AuditLog, Brand, Supplier, Warehouse, Customer, PurchaseOrder, StockTransfer, Employee, Attendance
    from app.blueprints.auth import auth_bp
    from app.blueprints.main import main_bp
    from app.blueprints.products import products_bp
    from app.blueprints.sales import sales_bp
    from app.blueprints.forecasting import forecasting_bp
    from app.blueprints.inventory import inventory_bp
    from app.blueprints.alerts import alerts_bp
    from app.blueprints.reports import reports_bp
    from app.blueprints.employees import employees_bp
    from app.blueprints.warehouses import warehouses_bp
    from app.blueprints.customers import customers_bp
    from app.blueprints.db_management import db_management_bp
    from app.blueprints.api import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(sales_bp, url_prefix='/sales')
    app.register_blueprint(forecasting_bp, url_prefix='/forecasting')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(alerts_bp, url_prefix='/alerts')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(employees_bp, url_prefix='/employees')
    app.register_blueprint(warehouses_bp, url_prefix='/warehouses')
    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(db_management_bp, url_prefix='/db')
    
    # Exempt API from CSRF and register it
    csrf.exempt(api_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Global error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        from flask import render_template
        return render_template('404.html'), 404
        
    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template('403.html'), 403

    @app.errorhandler(500)
    def internal_error(e):
        from flask import render_template
        return render_template('500.html'), 500

    # JWT Error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'message': 'The token has expired.', 'error': 'token_expired'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'message': 'Signature verification failed.', 'error': 'invalid_token'}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'message': 'Request does not contain an access token.', 'error': 'authorization_required'}), 401

    if app.config.get('TESTING'):
        with app.app_context():
            db.create_all()
            
    return app
