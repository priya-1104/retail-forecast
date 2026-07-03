from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, abort
from flask_login import login_required, current_user
from datetime import datetime
import io

from app.database import db
from app.models.business import Product, Sale, Inventory
from app.models.forecast import Forecast
from app.models.system import Report
from app.services.report_service import ReportService
from app.services.auth_service import AuthService

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
def reports_panel():
    """Renders the reports page listing historical downloads."""
    recent_reports = Report.query.order_by(Report.created_at.desc()).limit(15).all()
    return render_template('reports.html', reports=recent_reports)

@reports_bp.route('/generate', methods=['POST'])
@login_required
def generate_report():
    """Generates the requested data export (Sales, Inventory, or Forecasts) in CSV, Excel, or PDF format."""
    report_type = request.form.get('report_type')
    report_format = request.form.get('format')
    
    if not report_type or not report_format:
        flash("Invalid report generation parameters.", "warning")
        return redirect(url_for('reports.reports_panel'))
        
    headers = []
    rows = []
    title = ""
    
    # 1. Query Data
    if report_type == 'Sales':
        title = "Historical Sales Report"
        headers = ["Date", "SKU", "Product Name", "Quantity Sold", "Price ($)", "Revenue ($)"]
        sales = Sale.query.order_by(Sale.date.desc()).all()
        rows = [
            [
                s.date.strftime('%Y-%m-%d'),
                s.product.sku if s.product else 'N/A',
                s.product.name if s.product else 'N/A',
                s.quantity_sold,
                s.price,
                s.revenue
            ]
            for s in sales
        ]
        
    elif report_type == 'Inventory':
        title = "Inventory Optimization Parameters Report"
        headers = ["SKU", "Product Name", "Current Stock", "Safety Stock", "Reorder Point (ROP)", "Economic Order (EOQ)", "Status"]
        inventories = Inventory.query.all()
        rows = [
            [
                inv.product.sku if inv.product else 'N/A',
                inv.product.name if inv.product else 'N/A',
                inv.product.quantity if inv.product else 0,
                inv.safety_stock,
                inv.reorder_point,
                inv.eoq,
                inv.stock_status
            ]
            for inv in inventories
        ]
        
    elif report_type == 'Forecast':
        title = "AI Demand Predictions Report"
        headers = ["Forecast Date", "SKU", "Product Name", "Predicted Demand", "Model Used", "Generation Date"]
        forecasts = Forecast.query.order_by(Forecast.forecast_date).all()
        rows = [
            [
                f.forecast_date.strftime('%Y-%m-%d'),
                f.product.sku if f.product else 'N/A',
                f.product.name if f.product else 'N/A',
                f.predicted_quantity,
                f.model_used,
                f.created_at.strftime('%Y-%m-%d')
            ]
            for f in forecasts
        ]
    else:
        flash(f"Unknown report type: {report_type}", "danger")
        return redirect(url_for('reports.reports_panel'))
        
    # Check if empty
    if not rows:
        flash("No data records available to generate this report.", "warning")
        return redirect(url_for('reports.reports_panel'))
        
    # 2. Build Exporter File
    filename = f"{report_type.lower()}_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    if report_format == 'CSV':
        mimetype = "text/csv"
        filename += ".csv"
        buffer = ReportService.generate_csv_report(headers, rows)
    elif report_format == 'Excel':
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename += ".xlsx"
        buffer = ReportService.generate_excel_report(headers, rows, sheet_name=report_type)
    elif report_format == 'PDF':
        mimetype = "application/pdf"
        filename += ".pdf"
        buffer = ReportService.generate_pdf_report(title, headers, rows)
    else:
        flash("Unsupported file format.", "danger")
        return redirect(url_for('reports.reports_panel'))
        
    # 3. Save report metadata to db log
    rep = Report(
        name=filename,
        type=report_type,
        format=report_format,
        file_path=f"static/reports/{filename}" # Mock path, we stream directly from memory
    )
    db.session.add(rep)
    db.session.commit()
    
    # Audit log
    AuthService.log_action(current_user.id, 'Generate Report', f"Generated {report_format} report for '{report_type}'")
    
    # Stream back as attachment
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype
    )
