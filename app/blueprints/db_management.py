import csv
import io
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify, send_file
from flask_login import login_required, current_user
from app.database import db
from app.services.db_manager import DatabaseManager
from app.services.auth_service import AuthService
from sqlalchemy import MetaData, Table, inspect
import openpyxl

db_management_bp = Blueprint('db_management', __name__, url_prefix='/db')

def check_admin_auth():
    """Restricts access to administrators only."""
    if not current_user.is_authenticated or current_user.role != 'Admin':
        abort(403)

@db_management_bp.before_request
@login_required
def restrict_access():
    check_admin_auth()

@db_management_bp.route('/dashboard')
def dashboard():
    """Renders the database telemetry dashboard and backups list."""
    stats = DatabaseManager.get_system_telemetry()
    backups = DatabaseManager.list_backups()
    return render_template('db_dashboard.html', stats=stats, backups=backups)

@db_management_bp.route('/explorer')
def explorer():
    """Renders the table structure explorer listing schema details."""
    stats = DatabaseManager.get_system_telemetry()
    metadata = MetaData()
    metadata.reflect(bind=db.engine)
    
    tables_schema = {}
    inspector = inspect(db.engine)
    
    for t_name in stats['tables']:
        columns = inspector.get_columns(t_name)
        pk_cols = inspector.get_pk_constraint(t_name).get('constrained_columns', [])
        fks = inspector.get_foreign_keys(t_name)
        indexes = inspector.get_indexes(t_name)
        
        tables_schema[t_name] = {
            'columns': columns,
            'primary_keys': pk_cols,
            'foreign_keys': fks,
            'indexes': indexes,
            'rows_count': stats['table_records'].get(t_name, 0)
        }
        
    return render_template('db_schema.html', tables=tables_schema)

@db_management_bp.route('/console', methods=['POST'])
def query_console():
    """Executes raw SQL query on the active database."""
    query_str = request.form.get('query', '').strip()
    if not query_str:
        return jsonify({'success': False, 'message': 'Empty query string.'}), 400
        
    # Restrict destructive actions from non-admins just in case
    check_admin_auth()
    
    try:
        # Wrap query in text()
        result = db.session.execute(db.text(query_str))
        
        # Check if query yields records (like SELECT)
        if result.returns_rows:
            columns = list(result.keys())
            rows = [dict(row._mapping) for row in result.all()]
            
            # Serialize dates and datetimes
            for row in rows:
                for col in columns:
                    val = row[col]
                    if hasattr(val, 'isoformat'):
                        row[col] = val.isoformat()
                        
            return jsonify({
                'success': True,
                'type': 'select',
                'columns': columns,
                'rows': rows,
                'count': len(rows)
            })
        else:
            db.session.commit()
            return jsonify({
                'success': True,
                'type': 'command',
                'rows_affected': result.rowcount
            })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@db_management_bp.route('/table/<table_name>', methods=['GET'])
def table_records(table_name):
    """Renders tabular rows of a reflected table."""
    metadata = MetaData()
    metadata.reflect(bind=db.engine)
    table = metadata.tables.get(table_name)
    
    if table is None:
        flash(f"Table '{table_name}' does not exist.", 'danger')
        return redirect(url_for('db_management.explorer'))
        
    # Read query params
    search_col = request.args.get('search_col', '').strip()
    search_val = request.args.get('search_val', '').strip()
    sort_col = request.args.get('sort_col', '').strip()
    sort_dir = request.args.get('sort_dir', 'asc').strip()
    
    page = request.args.get('page', 1, type=int)
    per_page = 25
    offset = (page - 1) * per_page
    
    # Base query
    query = db.select(table)
    
    # Filter
    if search_col and search_val and search_col in table.columns:
        query = query.where(table.c[search_col].like(f"%{search_val}%"))
        
    # Sort
    if sort_col and sort_col in table.columns:
        if sort_dir == 'desc':
            query = query.order_by(table.c[sort_col].desc())
        else:
            query = query.order_by(table.c[sort_col].asc())
            
    # Calculate totals
    count_query = db.select(db.func.count()).select_from(table)
    if search_col and search_val and search_col in table.columns:
        count_query = count_query.where(table.c[search_col].like(f"%{search_val}%"))
    total_rows = db.session.execute(count_query).scalar()
    
    # Paginate
    query = query.offset(offset).limit(per_page)
    result = db.session.execute(query)
    
    columns = list(table.columns.keys())
    rows = [dict(r._mapping) for r in result.all()]
    
    # Get Primary Key column for edit/delete mapping
    inspector = inspect(db.engine)
    pk_cols = inspector.get_pk_constraint(table_name).get('constrained_columns', [])
    pk_name = pk_cols[0] if pk_cols else 'id'
    
    column_schemas = []
    for col in table.columns:
        t = 'text'
        if 'INTEGER' in str(col.type).upper():
            t = 'number'
        elif 'FLOAT' in str(col.type).upper() or 'DECIMAL' in str(col.type).upper():
            t = 'float'
        elif 'BOOLEAN' in str(col.type).upper():
            t = 'boolean'
        elif 'DATE' in str(col.type).upper() and 'DATETIME' not in str(col.type).upper():
            t = 'date'
        elif 'DATETIME' in str(col.type).upper():
            t = 'datetime'
            
        column_schemas.append({
            'name': col.name,
            'type': t,
            'nullable': col.nullable,
            'primary_key': col.primary_key
        })
        
    total_pages = (total_rows + per_page - 1) // per_page
    
    return render_template(
        'db_explorer.html', 
        table_name=table_name,
        columns=columns, 
        rows=rows, 
        pk_name=pk_name,
        column_schemas=column_schemas,
        page=page,
        total_pages=total_pages,
        total_rows=total_rows,
        search_col=search_col,
        search_val=search_val,
        sort_col=sort_col,
        sort_dir=sort_dir
    )

@db_management_bp.route('/table/<table_name>/add', methods=['POST'])
def add_record(table_name):
    """Inserts a new record dynamically into the reflected table."""
    metadata = MetaData()
    metadata.reflect(bind=db.engine)
    table = metadata.tables.get(table_name)
    
    if table is None:
        return jsonify({'success': False, 'message': 'Table not found.'}), 404
        
    data = {}
    for col in table.columns:
        if col.primary_key:
            continue
        val = request.form.get(col.name)
        if val == '' or val is None:
            if col.nullable:
                data[col.name] = None
            continue
            
        # Type convert
        if 'INTEGER' in str(col.type).upper():
            data[col.name] = int(val)
        elif 'FLOAT' in str(col.type).upper() or 'DECIMAL' in str(col.type).upper():
            data[col.name] = float(val)
        elif 'BOOLEAN' in str(col.type).upper():
            data[col.name] = val.lower() in ['true', '1', 'on']
        elif 'DATE' in str(col.type).upper():
            data[col.name] = datetime.strptime(val, '%Y-%m-%d').date()
        elif 'DATETIME' in str(col.type).upper():
            data[col.name] = datetime.strptime(val, '%Y-%m-%dT%H:%M')
        else:
            data[col.name] = val
            
    try:
        stmt = table.insert().values(**data)
        db.session.execute(stmt)
        db.session.commit()
        
        AuthService.log_action(current_user.id, 'DB Insert', f"Added record to '{table_name}'")
        return jsonify({'success': True, 'message': 'Record added successfully.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@db_management_bp.route('/table/<table_name>/edit', methods=['POST'])
def edit_record(table_name):
    """Updates a record dynamically in the reflected table."""
    metadata = MetaData()
    metadata.reflect(bind=db.engine)
    table = metadata.tables.get(table_name)
    
    if table is None:
        return jsonify({'success': False, 'message': 'Table not found.'}), 404
        
    inspector = inspect(db.engine)
    pk_cols = inspector.get_pk_constraint(table_name).get('constrained_columns', [])
    if not pk_cols:
        return jsonify({'success': False, 'message': 'No primary key defined.'}), 400
        
    pk_name = pk_cols[0]
    pk_value = request.form.get(pk_name)
    
    if not pk_value:
        return jsonify({'success': False, 'message': 'Primary key identifier missing.'}), 400
        
    data = {}
    for col in table.columns:
        if col.name == pk_name:
            continue
        val = request.form.get(col.name)
        if val == '' or val is None:
            if col.nullable:
                data[col.name] = None
            continue
            
        # Type convert
        if 'INTEGER' in str(col.type).upper():
            data[col.name] = int(val)
        elif 'FLOAT' in str(col.type).upper() or 'DECIMAL' in str(col.type).upper():
            data[col.name] = float(val)
        elif 'BOOLEAN' in str(col.type).upper():
            data[col.name] = val.lower() in ['true', '1', 'on']
        elif 'DATE' in str(col.type).upper():
            data[col.name] = datetime.strptime(val, '%Y-%m-%d').date()
        elif 'DATETIME' in str(col.type).upper():
            data[col.name] = datetime.strptime(val, '%Y-%m-%dT%H:%M')
        else:
            data[col.name] = val
            
    try:
        # Cast primary key value
        if 'INTEGER' in str(table.columns[pk_name].type).upper():
            pk_value = int(pk_value)
            
        stmt = table.update().where(table.c[pk_name] == pk_value).values(**data)
        db.session.execute(stmt)
        db.session.commit()
        
        AuthService.log_action(current_user.id, 'DB Update', f"Modified record ID: {pk_value} in table '{table_name}'")
        return jsonify({'success': True, 'message': 'Record updated successfully.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@db_management_bp.route('/table/<table_name>/delete', methods=['POST'])
def delete_record(table_name):
    """Deletes a record dynamically from the reflected table."""
    metadata = MetaData()
    metadata.reflect(bind=db.engine)
    table = metadata.tables.get(table_name)
    
    if table is None:
        return jsonify({'success': False, 'message': 'Table not found.'}), 404
        
    inspector = inspect(db.engine)
    pk_cols = inspector.get_pk_constraint(table_name).get('constrained_columns', [])
    if not pk_cols:
        return jsonify({'success': False, 'message': 'No primary key defined.'}), 400
        
    pk_name = pk_cols[0]
    pk_value = request.form.get(pk_name)
    
    if not pk_value:
        return jsonify({'success': False, 'message': 'Primary key identifier missing.'}), 400
        
    try:
        if 'INTEGER' in str(table.columns[pk_name].type).upper():
            pk_value = int(pk_value)
            
        stmt = table.delete().where(table.c[pk_name] == pk_value)
        db.session.execute(stmt)
        db.session.commit()
        
        AuthService.log_action(current_user.id, 'DB Delete', f"Deleted record ID: {pk_value} from table '{table_name}'")
        return jsonify({'success': True, 'message': 'Record deleted successfully.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@db_management_bp.route('/table/<table_name>/export')
def export_table(table_name):
    """Exports table records to CSV or Excel format."""
    fmt = request.args.get('format', 'csv').lower()
    
    metadata = MetaData()
    metadata.reflect(bind=db.engine)
    table = metadata.tables.get(table_name)
    
    if table is None:
        abort(404)
        
    result = db.session.execute(db.select(table))
    columns = list(table.columns.keys())
    rows = [dict(r._mapping) for r in result.all()]
    
    if fmt == 'xlsx':
        # Excel Export using openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = table_name[:30] # Excel limits tab names to 30 chars
        
        # Headers
        ws.append(columns)
        
        # Rows
        for row in rows:
            ws.append([str(row[c]) if row[c] is not None else '' for c in columns])
            
        out = io.BytesIO()
        wb.save(out)
        out.seek(0)
        
        return send_file(
            out,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"{table_name}_export.xlsx"
        )
    else:
        # Default CSV Export
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(columns)
        for row in rows:
            cw.writerow([row[c] for c in columns])
            
        output = io.BytesIO()
        output.write(si.getvalue().encode('utf-8'))
        output.seek(0)
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"{table_name}_export.csv"
        )

@db_management_bp.route('/backup/run', methods=['POST'])
def run_backup():
    """Triggers a manual database backup."""
    success, res = DatabaseManager.run_backup()
    if success:
        AuthService.log_action(current_user.id, 'DB Backup', f"Created backup file '{res}'")
        flash(f"Database backed up successfully as '{res}'!", 'success')
    else:
        flash(f"Backup failed: {res}", 'danger')
    return redirect(url_for('db_management.dashboard'))

@db_management_bp.route('/backup/download/<filename>')
def download_backup(filename):
    """Downloads a backup file from disk."""
    path = os.path.join(DatabaseManager.get_backup_dir(), filename)
    if not os.path.exists(path):
        abort(404)
    return send_file(path, as_attachment=True)

@db_management_bp.route('/backup/delete/<filename>', methods=['POST'])
def delete_backup(filename):
    """Deletes a backup file from disk."""
    success, err = DatabaseManager.delete_backup(filename)
    if success:
        AuthService.log_action(current_user.id, 'DB Backup Delete', f"Deleted backup file '{filename}'")
        flash(f"Backup '{filename}' deleted.", 'info')
    else:
        flash(f"Delete failed: {err}", 'danger')
    return redirect(url_for('db_management.dashboard'))

@db_management_bp.route('/backup/restore/<filename>', methods=['POST'])
def restore_backup(filename):
    """Restores database from backup."""
    success, err = DatabaseManager.restore_backup(filename)
    if success:
        AuthService.log_action(current_user.id, 'DB Restore', f"Restored database using backup '{filename}'")
        flash(f"Database successfully restored using backup '{filename}'!", 'success')
    else:
        flash(f"Restore failed: {err}", 'danger')
    return redirect(url_for('db_management.dashboard'))
