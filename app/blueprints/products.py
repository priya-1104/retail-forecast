from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.database import db
from app.models.business import Product, Inventory
from app.services.auth_service import AuthService

products_bp = Blueprint('products', __name__)

@products_bp.route('/')
@login_required
def list_products():
    """Lists all products for browsing."""
    products = Product.query.all()
    return render_template('products.html', products=products)

@products_bp.route('/add', methods=['POST'])
@login_required
def add_product():
    """Adds a new product to the database and initializes its inventory parameters."""
    if current_user.role not in ['Admin', 'Manager']:
        abort(403)
        
    name = request.form.get('name')
    sku = request.form.get('sku').strip()
    category = request.form.get('category')
    price = request.form.get('price')
    quantity = request.form.get('quantity')
    description = request.form.get('description')
    
    # Validation
    if not name or not sku or not category or not price or not quantity:
        flash('Please fill in all required fields.', 'warning')
        return redirect(url_for('products.list_products'))
        
    # Check duplicate SKU
    existing = Product.query.filter_by(sku=sku).first()
    if existing:
        flash(f"Product SKU '{sku}' already exists in system.", 'danger')
        return redirect(url_for('products.list_products'))
        
    try:
        prod = Product(
            name=name,
            sku=sku,
            category=category,
            price=float(price),
            quantity=int(quantity),
            description=description
        )
        db.session.add(prod)
        db.session.commit()
        
        # Initialize Inventory optimization stats
        inv = Inventory(
            product_id=prod.id,
            safety_stock=10.0,  # Default starting values
            reorder_point=25.0,
            eoq=50.0,
            stock_status="In Stock"
        )
        db.session.add(inv)
        db.session.commit()
        
        AuthService.log_action(current_user.id, 'Add Product', f"Added product '{name}' (SKU: {sku})")
        flash(f"Product '{name}' added successfully!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding product: {str(e)}", 'danger')
        
    return redirect(url_for('products.list_products'))

@products_bp.route('/edit', methods=['POST'])
@login_required
def edit_product():
    """Modifies an existing product's fields."""
    if current_user.role not in ['Admin', 'Manager']:
        abort(403)
        
    product_id = request.form.get('product_id')
    name = request.form.get('name')
    sku = request.form.get('sku').strip()
    category = request.form.get('category')
    price = request.form.get('price')
    quantity = request.form.get('quantity')
    description = request.form.get('description')
    
    product = Product.query.get(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('products.list_products'))
        
    # Check duplicate SKU (excluding self)
    existing = Product.query.filter(Product.sku == sku, Product.id != product_id).first()
    if existing:
        flash(f"Product SKU '{sku}' already exists.", 'danger')
        return redirect(url_for('products.list_products'))
        
    try:
        product.name = name
        product.sku = sku
        product.category = category
        product.price = float(price)
        product.quantity = int(quantity)
        product.description = description
        
        db.session.commit()
        
        AuthService.log_action(current_user.id, 'Edit Product', f"Edited product '{name}' (SKU: {sku})")
        flash(f"Product '{name}' updated successfully!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating product: {str(e)}", 'danger')
        
    return redirect(url_for('products.list_products'))

@products_bp.route('/delete', methods=['POST'])
@login_required
def delete_product():
    """Deletes a product from the database."""
    if current_user.role not in ['Admin', 'Manager']:
        abort(403)
        
    product_id = request.form.get('product_id')
    product = Product.query.get(product_id)
    
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('products.list_products'))
        
    try:
        name = product.name
        sku = product.sku
        db.session.delete(product)
        db.session.commit()
        
        AuthService.log_action(current_user.id, 'Delete Product', f"Deleted product '{name}' (SKU: {sku})")
        flash(f"Product '{name}' deleted successfully.", 'info')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting product: {str(e)}", 'danger')
        
    return redirect(url_for('products.list_products'))
