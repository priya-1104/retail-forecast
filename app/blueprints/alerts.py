from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.database import db
from app.models.system import Alert

alerts_bp = Blueprint('alerts', __name__)

@alerts_bp.route('/')
@login_required
def alerts_panel():
    """Lists system alerts categorized by read/unread status."""
    unread_alerts = Alert.query.filter_by(is_read=False).order_by(Alert.created_at.desc()).all()
    read_alerts = Alert.query.filter_by(is_read=True).order_by(Alert.created_at.desc()).limit(30).all()
    return render_template('alerts.html', unread=unread_alerts, read=read_alerts)

@alerts_bp.route('/read/<int:alert_id>', methods=['POST'])
@login_required
def mark_read(alert_id):
    """Marks an individual alert notification as read."""
    alert = Alert.query.get_or_404(alert_id)
    alert.is_read = True
    db.session.commit()
    return redirect(url_for('alerts.alerts_panel'))

@alerts_bp.route('/read-all', methods=['POST'])
@login_required
def mark_all_read():
    """Marks all currently unread notifications as read in bulk."""
    Alert.query.filter_by(is_read=False).update({Alert.is_read: True})
    db.session.commit()
    flash("All active alerts marked as read.", "success")
    return redirect(url_for('alerts.alerts_panel'))

@alerts_bp.route('/delete/<int:alert_id>', methods=['POST'])
@login_required
def delete_alert(alert_id):
    """Deletes an alert completely from the database logs."""
    if current_user.role not in ['Admin', 'Manager']:
        abort(403)
        
    alert = Alert.query.get_or_404(alert_id)
    db.session.delete(alert)
    db.session.commit()
    flash("Alert deleted successfully.", "info")
    return redirect(url_for('alerts.alerts_panel'))
