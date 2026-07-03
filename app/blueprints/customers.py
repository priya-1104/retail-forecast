from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app.database import db
from app.models.business import Customer, Sale
from app.services.auth_service import AuthService

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/')
@login_required
def list_customers():
    """Lists all customer accounts."""
    if current_user.role not in ['Admin', 'Manager']:
        abort(403)
    customers = Customer.query.all()
    return render_template('users.html', customers=customers)

@customers_bp.route('/add', methods=['POST'])
@login_required
def add_customer():
    """Registers a new customer account."""
    if current_user.role not in ['Admin', 'Manager', 'Staff']:
        abort(403)
        
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    address = request.form.get('address')
    membership = request.form.get('membership_tier', 'Regular')
    
    if not name:
        flash('Customer name is required.', 'warning')
        return redirect(url_for('customers.list_customers'))
        
    try:
        cust = Customer(
            name=name,
            email=email,
            phone=phone,
            address=address,
            membership_tier=membership,
            loyalty_points=0
        )
        db.session.add(cust)
        db.session.commit()
        
        AuthService.log_action(current_user.id, 'Add Customer', f"Registered customer '{name}'")
        flash(f"Customer '{name}' registered successfully!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error registering customer: {str(e)}", 'danger')
        
    return redirect(url_for('customers.list_customers'))

@customers_bp.route('/edit', methods=['POST'])
@login_required
def edit_customer():
    """Modifies customer details."""
    if current_user.role not in ['Admin', 'Manager']:
        abort(403)
        
    cust_id = request.form.get('id')
    customer = Customer.query.get(cust_id)
    if not customer:
        flash('Customer not found.', 'danger')
        return redirect(url_for('customers.list_customers'))
        
    try:
        customer.name = request.form.get('name')
        customer.email = request.form.get('email')
        customer.phone = request.form.get('phone')
        customer.address = request.form.get('address')
        customer.membership_tier = request.form.get('membership_tier', 'Regular')
        customer.loyalty_points = request.form.get('loyalty_points', 0, type=int)
        
        db.session.commit()
        AuthService.log_action(current_user.id, 'Edit Customer', f"Modified customer details for '{customer.name}'")
        flash(f"Customer '{customer.name}' details updated successfully.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating customer: {str(e)}", 'danger')
        
    return redirect(url_for('customers.list_customers'))

@customers_bp.route('/delete', methods=['POST'])
@login_required
def delete_customer():
    """Deletes a customer account."""
    if current_user.role != 'Admin':
        abort(403)
        
    cust_id = request.form.get('id')
    customer = Customer.query.get(cust_id)
    if not customer:
        flash('Customer not found.', 'danger')
        return redirect(url_for('customers.list_customers'))
        
    try:
        name = customer.name
        db.session.delete(customer)
        db.session.commit()
        
        AuthService.log_action(current_user.id, 'Delete Customer', f"Deleted customer '{name}'")
        flash(f"Customer '{name}' deleted successfully.", 'info')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting customer: {str(e)}", 'danger')
        
    return redirect(url_for('customers.list_customers'))

@customers_bp.route('/history/<int:customer_id>', methods=['GET'])
@login_required
def purchase_history(customer_id):
    """API endpoint to fetch purchase logs of a customer."""
    customer = Customer.query.get_or_404(customer_id)
    sales = Sale.query.filter_by(customer_id=customer_id).order_by(Sale.date.desc()).all()
    return jsonify({
        'customer_name': customer.name,
        'loyalty_points': customer.loyalty_points,
        'sales': [s.to_dict() for s in sales]
    })
