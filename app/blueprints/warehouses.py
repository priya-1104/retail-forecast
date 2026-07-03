from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app.database import db
from app.models.business import Product, Warehouse, StockTransfer
from app.services.auth_service import AuthService

warehouses_bp = Blueprint('warehouses', __name__)

@warehouses_bp.route('/')
@login_required
def list_warehouses():
    """Lists all warehouses and stock transfer history."""
    if current_user.role not in ['Admin', 'Manager']:
        abort(403)
        
    warehouses = Warehouse.query.all()
    transfers = StockTransfer.query.order_by(StockTransfer.transfer_date.desc()).limit(50).all()
    products = Product.query.all()
    
    return render_template('inventory.html', warehouses=warehouses, transfers=transfers, products=products)

@warehouses_bp.route('/add', methods=['POST'])
@login_required
def add_warehouse():
    """Creates a new warehouse."""
    if current_user.role not in ['Admin', 'Manager']:
        abort(403)
        
    name = request.form.get('name').strip()
    location = request.form.get('location')
    capacity = request.form.get('capacity_sqft', 0, type=int)
    
    if not name:
        flash('Warehouse name is required.', 'warning')
        return redirect(url_for('warehouses.list_warehouses'))
        
    existing = Warehouse.query.filter_by(name=name).first()
    if existing:
        flash(f"Warehouse '{name}' already exists.", 'danger')
        return redirect(url_for('warehouses.list_warehouses'))
        
    try:
        wh = Warehouse(name=name, location=location, capacity_sqft=capacity)
        db.session.add(wh)
        db.session.commit()
        
        AuthService.log_action(current_user.id, 'Add Warehouse', f"Created warehouse '{name}'")
        flash(f"Warehouse '{name}' created successfully!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating warehouse: {str(e)}", 'danger')
        
    return redirect(url_for('warehouses.list_warehouses'))

@warehouses_bp.route('/edit', methods=['POST'])
@login_required
def edit_warehouse():
    """Updates warehouse configurations."""
    if current_user.role not in ['Admin', 'Manager']:
        abort(403)
        
    wh_id = request.form.get('id')
    warehouse = Warehouse.query.get(wh_id)
    if not warehouse:
        flash('Warehouse not found.', 'danger')
        return redirect(url_for('warehouses.list_warehouses'))
        
    name = request.form.get('name').strip()
    existing = Warehouse.query.filter(Warehouse.name == name, Warehouse.id != warehouse.id).first()
    if existing:
        flash(f"Warehouse name '{name}' already in use.", 'danger')
        return redirect(url_for('warehouses.list_warehouses'))
        
    try:
        warehouse.name = name
        warehouse.location = request.form.get('location')
        warehouse.capacity_sqft = request.form.get('capacity_sqft', 0, type=int)
        
        db.session.commit()
        AuthService.log_action(current_user.id, 'Edit Warehouse', f"Modified warehouse '{name}' configurations")
        flash(f"Warehouse '{name}' updated successfully.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating warehouse: {str(e)}", 'danger')
        
    return redirect(url_for('warehouses.list_warehouses'))

@warehouses_bp.route('/delete', methods=['POST'])
@login_required
def delete_warehouse():
    """Deletes a warehouse."""
    if current_user.role != 'Admin':
        abort(403)
        
    wh_id = request.form.get('id')
    warehouse = Warehouse.query.get(wh_id)
    if not warehouse:
        flash('Warehouse not found.', 'danger')
        return redirect(url_for('warehouses.list_warehouses'))
        
    try:
        name = warehouse.name
        db.session.delete(warehouse)
        db.session.commit()
        
        AuthService.log_action(current_user.id, 'Delete Warehouse', f"Deleted warehouse '{name}'")
        flash(f"Warehouse '{name}' deleted successfully.", 'info')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting warehouse: {str(e)}", 'danger')
        
    return redirect(url_for('warehouses.list_warehouses'))

@warehouses_bp.route('/transfer', methods=['POST'])
@login_required
def transfer_stock():
    """Executes a stock transfer between warehouses."""
    if current_user.role not in ['Admin', 'Manager']:
        abort(403)
        
    product_id = request.form.get('product_id', type=int)
    source_id = request.form.get('source_warehouse_id', type=int)
    dest_id = request.form.get('dest_warehouse_id', type=int)
    qty = request.form.get('quantity', type=int)
    
    if source_id == dest_id:
        flash('Source and destination warehouses must be different.', 'warning')
        return redirect(url_for('warehouses.list_warehouses'))
        
    product = Product.query.get(product_id)
    source_wh = Warehouse.query.get(source_id)
    dest_wh = Warehouse.query.get(dest_id)
    
    if not product or not source_wh or not dest_wh:
        flash('Invalid product or warehouse selection.', 'danger')
        return redirect(url_for('warehouses.list_warehouses'))
        
    # Check if product is in source warehouse and has enough quantity
    if product.warehouse_id != source_id:
        flash(f"Product '{product.name}' is not currently stored in the source warehouse '{source_wh.name}'.", 'danger')
        return redirect(url_for('warehouses.list_warehouses'))
        
    if product.quantity < qty:
        flash(f"Insufficient stock in source warehouse. Available: {product.quantity}, Requested: {qty}.", 'danger')
        return redirect(url_for('warehouses.list_warehouses'))
        
    try:
        # Deduct from source and move product assignment to destination warehouse
        # (For simple single-location mapping, update product's warehouse link.
        # In multi-location stock trackers, we would deduct from source inventory and add to dest).
        product.warehouse_id = dest_id
        
        # Log stock transfer
        transfer = StockTransfer(
            product_id=product_id,
            source_warehouse_id=source_id,
            dest_warehouse_id=dest_id,
            quantity=qty,
            status='Completed',
            transfer_date=datetime.utcnow().date()
        )
        db.session.add(transfer)
        db.session.commit()
        
        AuthService.log_action(current_user.id, 'Stock Transfer', f"Transferred {qty} units of '{product.name}' from '{source_wh.name}' to '{dest_wh.name}'")
        flash(f"Successfully transferred {qty} units of '{product.name}' to '{dest_wh.name}'!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Stock transfer transaction failed: {str(e)}", 'danger')
        
    return redirect(url_for('warehouses.list_warehouses'))
