from datetime import datetime
from app.database import db

class Brand(db.Model):
    __tablename__ = 'brands'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    manufacturer = db.Column(db.String(128), nullable=True)
    description = db.Column(db.Text, nullable=True)
    
    # Relationships
    products = db.relationship('Product', backref='brand', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'manufacturer': self.manufacturer,
            'description': self.description
        }

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(32), nullable=True)
    address = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Float, default=5.0)
    
    # Relationships
    products = db.relationship('Product', backref='supplier', lazy='dynamic')
    purchase_orders = db.relationship('PurchaseOrder', backref='supplier', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'rating': self.rating
        }

class Warehouse(db.Model):
    __tablename__ = 'warehouses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    location = db.Column(db.String(256), nullable=True)
    capacity_sqft = db.Column(db.Integer, default=0)
    
    # Relationships
    products = db.relationship('Product', backref='warehouse', lazy='dynamic')
    purchase_orders = db.relationship('PurchaseOrder', backref='warehouse', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'capacity_sqft': self.capacity_sqft
        }

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(32), nullable=True)
    address = db.Column(db.Text, nullable=True)
    membership_tier = db.Column(db.String(32), default='Regular')  # Regular, Silver, Gold, Platinum
    loyalty_points = db.Column(db.Integer, default=0)
    
    # Relationships
    sales = db.relationship('Sale', backref='customer', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'membership_tier': self.membership_tier,
            'loyalty_points': self.loyalty_points
        }

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    sku = db.Column(db.String(64), unique=True, nullable=False, index=True)
    category = db.Column(db.String(64), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Enterprise Additions
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id', ondelete='SET NULL'), nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id', ondelete='SET NULL'), nullable=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id', ondelete='SET NULL'), nullable=True)
    barcode = db.Column(db.String(64), nullable=True, index=True)
    qr_code = db.Column(db.String(256), nullable=True)
    batch_number = db.Column(db.String(64), nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)
    warranty_months = db.Column(db.Integer, default=0)
    gst_rate = db.Column(db.Float, default=0.0)
    unit = db.Column(db.String(32), default='pcs')
    
    # Relationships
    sales = db.relationship('Sale', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    inventory = db.relationship('Inventory', backref='product', uselist=False, cascade='all, delete-orphan')
    forecasts = db.relationship('Forecast', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    model_metadata = db.relationship('ModelMetadata', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    stock_transfers = db.relationship('StockTransfer', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    purchase_orders = db.relationship('PurchaseOrder', backref='product', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sku': self.sku,
            'category': self.category,
            'price': self.price,
            'quantity': self.quantity,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'brand_id': self.brand_id,
            'supplier_id': self.supplier_id,
            'warehouse_id': self.warehouse_id,
            'barcode': self.barcode,
            'qr_code': self.qr_code,
            'batch_number': self.batch_number,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'warranty_months': self.warranty_months,
            'gst_rate': self.gst_rate,
            'unit': self.unit
        }

class Sale(db.Model):
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity_sold = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    revenue = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Customer Relationship
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', ondelete='SET NULL'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'quantity_sold': self.quantity_sold,
            'price': self.price,
            'revenue': self.revenue,
            'created_at': self.created_at.isoformat(),
            'customer_id': self.customer_id
        }

class Inventory(db.Model):
    __tablename__ = 'inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, unique=True)
    safety_stock = db.Column(db.Float, default=0.0)
    reorder_point = db.Column(db.Float, default=0.0)
    eoq = db.Column(db.Float, default=0.0)
    stock_status = db.Column(db.String(32), default='In Stock')  # In Stock, Low Stock, Out of Stock, Overstock
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'sku': self.product.sku if self.product else None,
            'current_stock': self.product.quantity if self.product else 0,
            'safety_stock': self.safety_stock,
            'reorder_point': self.reorder_point,
            'eoq': self.eoq,
            'stock_status': self.stock_status,
            'updated_at': self.updated_at.isoformat()
        }

class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id', ondelete='CASCADE'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id', ondelete='CASCADE'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    order_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    delivery_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(32), default='Pending')  # Pending, Delivered, Canceled
    total_amount = db.Column(db.Float, default=0.0)
    payment_status = db.Column(db.String(32), default='Unpaid')  # Paid, Unpaid, Partial

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'supplier_id': self.supplier_id,
            'warehouse_id': self.warehouse_id,
            'quantity': self.quantity,
            'order_date': self.order_date.isoformat(),
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None,
            'status': self.status,
            'total_amount': self.total_amount,
            'payment_status': self.payment_status
        }

class StockTransfer(db.Model):
    __tablename__ = 'stock_transfers'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    source_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id', ondelete='CASCADE'), nullable=False)
    dest_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id', ondelete='CASCADE'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    transfer_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    status = db.Column(db.String(32), default='Pending')  # Pending, Completed

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'source_warehouse_id': self.source_warehouse_id,
            'dest_warehouse_id': self.dest_warehouse_id,
            'quantity': self.quantity,
            'transfer_date': self.transfer_date.isoformat(),
            'status': self.status
        }
