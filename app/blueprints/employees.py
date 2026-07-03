from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app.database import db
from app.models.hr import Employee, Attendance
from app.services.auth_service import AuthService

employees_bp = Blueprint('employees', __name__)

@employees_bp.route('/')
@login_required
def list_employees():
    """Lists all registered employees."""
    if current_user.role not in ['Admin', 'Manager']:
        abort(403)
    employees = Employee.query.all()
    # Fetch today's attendance logs
    today = datetime.utcnow().date()
    attendance_today = Attendance.query.filter_by(date=today).all()
    attendance_map = {a.employee_id: a for a in attendance_today}
    
    return render_template('users.html', employees=employees, attendance_map=attendance_map)

@employees_bp.route('/add', methods=['POST'])
@login_required
def add_employee():
    """Registers a new employee."""
    if current_user.role not in ['Admin', 'Manager']:
        abort(403)
        
    employee_id = request.form.get('employee_id').strip()
    name = request.form.get('name')
    department = request.form.get('department')
    designation = request.form.get('designation')
    salary = request.form.get('salary', 0.0, type=float)
    shift = request.form.get('shift', 'Day')
    
    if not employee_id or not name or not department or not designation:
        flash('Please fill in all required fields.', 'warning')
        return redirect(url_for('employees.list_employees'))
        
    existing = Employee.query.filter_by(employee_id=employee_id).first()
    if existing:
        flash(f"Employee ID '{employee_id}' already registered.", 'danger')
        return redirect(url_for('employees.list_employees'))
        
    try:
        emp = Employee(
            employee_id=employee_id,
            name=name,
            department=department,
            designation=designation,
            salary=salary,
            shift=shift,
            status='Active'
        )
        db.session.add(emp)
        db.session.commit()
        
        AuthService.log_action(current_user.id, 'Add Employee', f"Registered employee '{name}' (ID: {employee_id})")
        flash(f"Employee '{name}' registered successfully!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error registering employee: {str(e)}", 'danger')
        
    return redirect(url_for('employees.list_employees'))

@employees_bp.route('/edit', methods=['POST'])
@login_required
def edit_employee():
    """Modifies employee details."""
    if current_user.role not in ['Admin', 'Manager']:
        abort(403)
        
    emp_id = request.form.get('id')
    employee = Employee.query.get(emp_id)
    if not employee:
        flash('Employee not found.', 'danger')
        return redirect(url_for('employees.list_employees'))
        
    employee_id = request.form.get('employee_id').strip()
    # Check duplicate ID excluding self
    existing = Employee.query.filter(Employee.employee_id == employee_id, Employee.id != employee.id).first()
    if existing:
        flash(f"Employee ID '{employee_id}' already in use.", 'danger')
        return redirect(url_for('employees.list_employees'))
        
    try:
        employee.employee_id = employee_id
        employee.name = request.form.get('name')
        employee.department = request.form.get('department')
        employee.designation = request.form.get('designation')
        employee.salary = request.form.get('salary', 0.0, type=float)
        employee.shift = request.form.get('shift', 'Day')
        employee.status = request.form.get('status', 'Active')
        
        db.session.commit()
        AuthService.log_action(current_user.id, 'Edit Employee', f"Modified details of employee '{employee.name}' (ID: {employee_id})")
        flash(f"Employee '{employee.name}' details updated successfully.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating employee: {str(e)}", 'danger')
        
    return redirect(url_for('employees.list_employees'))

@employees_bp.route('/delete', methods=['POST'])
@login_required
def delete_employee():
    """Deletes an employee record."""
    if current_user.role != 'Admin':
        abort(403)
        
    emp_id = request.form.get('id')
    employee = Employee.query.get(emp_id)
    if not employee:
        flash('Employee not found.', 'danger')
        return redirect(url_for('employees.list_employees'))
        
    try:
        name = employee.name
        emp_code = employee.employee_id
        db.session.delete(employee)
        db.session.commit()
        
        AuthService.log_action(current_user.id, 'Delete Employee', f"Deleted employee '{name}' (ID: {emp_code})")
        flash(f"Employee '{name}' deleted successfully.", 'info')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting employee: {str(e)}", 'danger')
        
    return redirect(url_for('employees.list_employees'))

@employees_bp.route('/check-in', methods=['POST'])
@login_required
def check_in():
    """Logs the check-in time for an employee."""
    employee_id = request.form.get('employee_id')
    employee = Employee.query.filter_by(employee_id=employee_id).first()
    if not employee:
        return jsonify({'success': False, 'message': 'Employee not found.'}), 404
        
    today = datetime.utcnow().date()
    attendance = Attendance.query.filter_by(employee_id=employee.id, date=today).first()
    
    if attendance and attendance.check_in:
        return jsonify({'success': False, 'message': 'Already checked in for today.'}), 400
        
    try:
        if not attendance:
            attendance = Attendance(employee_id=employee.id, date=today)
            db.session.add(attendance)
            
        attendance.check_in = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'message': f"Checked in successfully at {attendance.check_in.strftime('%H:%M:%S')} UTC"})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@employees_bp.route('/check-out', methods=['POST'])
@login_required
def check_out():
    """Logs the check-out time and computes working hours."""
    employee_id = request.form.get('employee_id')
    employee = Employee.query.filter_by(employee_id=employee_id).first()
    if not employee:
        return jsonify({'success': False, 'message': 'Employee not found.'}), 404
        
    today = datetime.utcnow().date()
    attendance = Attendance.query.filter_by(employee_id=employee.id, date=today).first()
    
    if not attendance or not attendance.check_in:
        return jsonify({'success': False, 'message': 'Must check in before checking out.'}), 400
        
    if attendance.check_out:
        return jsonify({'success': False, 'message': 'Already checked out for today.'}), 400
        
    try:
        attendance.check_out = datetime.utcnow()
        # Calculate working hours (difference in hours)
        diff = attendance.check_out - attendance.check_in
        hours = diff.total_seconds() / 3600.0
        attendance.working_hours = round(hours, 2)
        
        # Calculate overtime (standard shift is 8 hours)
        if hours > 8.0:
            attendance.overtime_hours = round(hours - 8.0, 2)
            
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f"Checked out successfully at {attendance.check_out.strftime('%H:%M:%S')} UTC. Total hours: {attendance.working_hours}."
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
