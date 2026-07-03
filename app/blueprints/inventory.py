from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models.business import Product, Inventory
from app.services.inventory_ops import InventoryOps
from app.services.auth_service import AuthService

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/')
@login_required
def inventory_panel():
    """Renders the inventory status list with safety stock and EOQ recommendations."""
    inventories = Inventory.query.all()
    
    # Calculate simple aggregate indicators
    stats = {
        'total': len(inventories),
        'low': sum(1 for i in inventories if i.stock_status in ['Low Stock', 'Critical Low']),
        'overstock': sum(1 for i in inventories if i.stock_status == 'Overstock'),
        'out': sum(1 for i in inventories if i.stock_status == 'Out of Stock'),
        'healthy': sum(1 for i in inventories if i.stock_status == 'In Stock')
    }
    
    return render_template('inventory.html', inventories=inventories, stats=stats)

@inventory_bp.route('/recalculate', methods=['POST'])
@login_required
def recalculate_metrics():
    """Triggers mathematical inventory recalculations for all catalog products."""
    if current_user.role not in ['Admin', 'Manager']:
        abort(403)
        
    products = Product.query.all()
    recalculated_count = 0
    
    for p in products:
        inv = InventoryOps.calculate_optimization_metrics(p.id)
        if inv:
            recalculated_count += 1
            
    AuthService.log_action(current_user.id, 'Optimize Inventory', f"Recalculated inventory optimization parameters for {recalculated_count} products")
    flash(f"Successfully recalculated optimization parameters for {recalculated_count} products!", "success")
    return redirect(url_for('inventory.inventory_panel'))
