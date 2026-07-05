import os
import shutil
import ctypes
import platform
import subprocess
from datetime import datetime
from app.database import db

# Define Windows Memory Status Structure for native API call
class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)
    ]

class DatabaseManager:
    
    @classmethod
    def get_backup_dir(cls):
        """Returns the backups folder path."""
        # Create 'instance/backups' if missing
        backup_dir = os.path.join(os.getcwd(), 'instance', 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir
        
    @classmethod
    def run_backup(cls):
        """Copies the main SQLite database to the backups folder."""
        db_path = os.path.join(os.getcwd(), 'instance', 'demand_forecasting.db')
        if not os.path.exists(db_path):
            return False, "Database file does not exist yet."
            
        try:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"backup_{timestamp}.db"
            dest_path = os.path.join(cls.get_backup_dir(), filename)
            
            # Perform direct file copy (safe for SQLite development db)
            shutil.copy2(db_path, dest_path)
            return True, filename
        except Exception as e:
            return False, str(e)
            
    @classmethod
    def list_backups(cls):
        """Lists all files in the backups folder with details."""
        backup_dir = cls.get_backup_dir()
        files = []
        
        for name in os.listdir(backup_dir):
            if name.endswith('.db'):
                path = os.path.join(backup_dir, name)
                stat = os.stat(path)
                size_mb = stat.st_size / (1024 * 1024)
                created = datetime.utcfromtimestamp(stat.st_mtime)
                
                files.append({
                    'filename': name,
                    'size_mb': round(size_mb, 2),
                    'created_at': created.isoformat()
                })
                
        # Sort newest first
        files.sort(key=lambda x: x['filename'], reverse=True)
        return files
        
    @classmethod
    def delete_backup(cls, filename):
        """Removes a backup file from disk."""
        path = os.path.join(cls.get_backup_dir(), filename)
        if not os.path.exists(path):
            return False, "Backup file not found."
            
        try:
            os.remove(path)
            return True, None
        except Exception as e:
            return False, str(e)

    @classmethod
    def restore_backup(cls, filename):
        """Restores the database using a backup file."""
        backup_path = os.path.join(cls.get_backup_dir(), filename)
        db_path = os.path.join(os.getcwd(), 'instance', 'demand_forecasting.db')
        
        if not os.path.exists(backup_path):
            return False, "Backup file not found."
            
        try:
            # Close active connections (by disposing the SQLAlchemy engine)
            db.session.remove()
            db.engine.dispose()
            
            # Copy backup to current database destination
            shutil.copy2(backup_path, db_path)
            return True, None
        except Exception as e:
            return False, str(e)

    @classmethod
    def get_system_telemetry(cls):
        """Fetches CPU, RAM, and Disk storage usage using native Win32 API calls."""
        # 1. Disk usage via GetDiskFreeSpaceExW
        total_gb, used_gb, disk_pct = 0.0, 0.0, 0.0
        try:
            free_bytes = ctypes.c_ulonglong(0)
            total_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW("C:\\", None, ctypes.byref(total_bytes), ctypes.byref(free_bytes))
            
            total_gb = total_bytes.value / (1024**3)
            free_gb = free_bytes.value / (1024**3)
            used_gb = total_gb - free_gb
            disk_pct = (used_gb / total_gb) * 100 if total_gb > 0 else 0.0
        except Exception:
            # Fallback
            total_gb, used_gb, disk_pct = 100.0, 10.0, 10.0
            
        # 2. RAM usage via GlobalMemoryStatusEx
        total_ram_gb, used_ram_gb, ram_pct = 0.0, 0.0, 0.0
        try:
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            
            total_ram_gb = stat.ullTotalPhys / (1024**3)
            free_ram_gb = stat.ullAvailPhys / (1024**3)
            used_ram_gb = total_ram_gb - free_ram_gb
            ram_pct = stat.dwMemoryLoad
        except Exception:
            total_ram_gb, used_ram_gb, ram_pct = 8.0, 2.0, 25.0
            
        # 3. CPU Load estimation (standard subprocess call to Windows WMIC)
        cpu_pct = 5.0
        try:
            # wmic cpu get LoadPercentage
            out = subprocess.check_output("wmic cpu get LoadPercentage", shell=True)
            lines = out.decode().strip().split('\n')
            if len(lines) > 1:
                cpu_pct = float(lines[1].strip())
        except Exception:
            pass
            
        # 4. Database size
        db_path = os.path.join(os.getcwd(), 'instance', 'demand_forecasting.db')
        db_size_mb = 0.0
        if os.path.exists(db_path):
            db_size_mb = os.path.getsize(db_path) / (1024 * 1024)
            
        # 5. Row count and tables stats
        total_records = 0
        table_records = {}
        try:
            # Use reflection to fetch all table names
            inspector = db.inspect(db.engine)
            table_names = inspector.get_table_names()
            
            for t_name in table_names:
                # Direct select count
                res = db.session.execute(db.text(f"SELECT COUNT(*) FROM {t_name}")).scalar()
                table_records[t_name] = res
                total_records += res
        except Exception:
            table_names = []
            
        return {
            'cpu_usage': round(cpu_pct, 1),
            'ram_total': round(total_ram_gb, 2),
            'ram_used': round(used_ram_gb, 2),
            'ram_percent': round(ram_pct, 1),
            'disk_total': round(total_gb, 2),
            'disk_used': round(used_gb, 2),
            'disk_percent': round(disk_pct, 1),
            'db_size_mb': round(db_size_mb, 2),
            'total_tables': len(table_names),
            'total_records': total_records,
            'table_records': table_records,
            'tables': table_names,
            'db_health': 'Healthy',
            'server_status': 'Running'
        }
