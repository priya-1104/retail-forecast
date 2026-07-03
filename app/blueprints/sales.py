import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models.business import Sale
from app.services.sales_service import SalesService

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/')
@login_required
def sales_dashboard():
    """Lists recent sales records and shows the import panel."""
    # Query recent 100 sales logs
    recent_sales = Sale.query.order_by(Sale.date.desc()).limit(100).all()
    return render_template('sales.html', sales=recent_sales)

@sales_bp.route('/upload', methods=['POST'])
@login_required
def upload_sales():
    """Handles CSV/Excel uploads, runs import parsing, and cleans up temp files."""
    if current_user.role not in ['Admin', 'Manager']:
        abort(403)
        
    if 'sales_file' not in request.files:
        flash('No file part in the upload request.', 'warning')
        return redirect(url_for('sales.sales_dashboard'))
        
    file = request.files['sales_file']
    if file.filename == '':
        flash('No file selected.', 'warning')
        return redirect(url_for('sales.sales_dashboard'))
        
    if file and SalesService.allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Create temp path in static upload folder
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        # Execute import
        success, message = SalesService.import_sales_from_file(temp_path, current_user.id)
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
    else:
        flash('Invalid file format. Please upload a valid CSV or Excel (.xlsx/.xls) spreadsheet.', 'danger')
        
    return redirect(url_for('sales.sales_dashboard'))
