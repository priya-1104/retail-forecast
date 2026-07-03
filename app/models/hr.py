from datetime import datetime
from app.database import db

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(32), unique=True, nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)
    department = db.Column(db.String(64), nullable=False, index=True)
    designation = db.Column(db.String(64), nullable=False)
    salary = db.Column(db.Float, nullable=False, default=0.0)
    joining_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    shift = db.Column(db.String(32), nullable=False, default='Day')  # Day, Night
    status = db.Column(db.String(32), nullable=False, default='Active')  # Active, Inactive
    performance_rating = db.Column(db.Float, nullable=True)
    
    # Credentials reference
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # Relationships
    attendance = db.relationship('Attendance', backref='employee', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'name': self.name,
            'department': self.department,
            'designation': self.designation,
            'salary': self.salary,
            'joining_date': self.joining_date.isoformat() if self.joining_date else None,
            'shift': self.shift,
            'status': self.status,
            'performance_rating': self.performance_rating,
            'user_id': self.user_id
        }

class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    check_in = db.Column(db.DateTime, nullable=True)
    check_out = db.Column(db.DateTime, nullable=True)
    break_start = db.Column(db.DateTime, nullable=True)
    break_end = db.Column(db.DateTime, nullable=True)
    working_hours = db.Column(db.Float, default=0.0)
    overtime_hours = db.Column(db.Float, default=0.0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'date': self.date.isoformat(),
            'check_in': self.check_in.isoformat() if self.check_in else None,
            'check_out': self.check_out.isoformat() if self.check_out else None,
            'break_start': self.break_start.isoformat() if self.break_start else None,
            'break_end': self.break_end.isoformat() if self.break_end else None,
            'working_hours': self.working_hours,
            'overtime_hours': self.overtime_hours
        }
