#!/usr/bin/env python3
"""
Production Health Check and Monitoring System
Provides comprehensive health checks and system metrics
"""

import os
import sys
import time
import psutil
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

class HealthChecker:
    """Comprehensive health check system"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.start_time = time.time()
        
    def check_databases(self) -> Dict[str, Any]:
        """Check database health"""
        results = {
            "status": "healthy",
            "databases": {},
            "issues": []
        }
        
        db_files = [
            "email_auth.db",
            "mfa_auth.db",
            "sessions.db",
            "logs.db",
            "main.db"
        ]
        
        for db_file in db_files:
            db_path = self.data_dir / db_file
            db_status = {
                "exists": db_path.exists(),
                "size_mb": 0,
                "accessible": False,
                "tables": 0
            }
            
            if db_path.exists():
                try:
                    db_status["size_mb"] = round(db_path.stat().st_size / (1024 * 1024), 2)
                    
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    db_status["tables"] = len(cursor.fetchall())
                    db_status["accessible"] = True
                    conn.close()
                except Exception as e:
                    db_status["error"] = str(e)
                    results["issues"].append(f"{db_file}: {e}")
                    results["status"] = "degraded"
            else:
                results["issues"].append(f"{db_file}: Not found")
                results["status"] = "unhealthy"
            
            results["databases"][db_file] = db_status
        
        return results
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            status = "healthy"
            issues = []
            
            # Check thresholds
            if cpu_percent > 80:
                status = "warning"
                issues.append(f"High CPU usage: {cpu_percent}%")
            
            if memory.percent > 85:
                status = "warning"
                issues.append(f"High memory usage: {memory.percent}%")
            
            if disk.percent > 90:
                status = "critical"
                issues.append(f"Low disk space: {disk.percent}% used")
            
            return {
                "status": status,
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent": disk.percent
                },
                "issues": issues
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_directories(self) -> Dict[str, Any]:
        """Check required directories"""
        required_dirs = [
            "data",
            "logs",
            "uploads",
            "downloads",
            "backups"
        ]
        
        results = {
            "status": "healthy",
            "directories": {},
            "issues": []
        }
        
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            dir_status = {
                "exists": dir_path.exists(),
                "writable": False,
                "size_mb": 0
            }
            
            if dir_path.exists():
                try:
                    # Check if writable
                    test_file = dir_path / ".write_test"
                    test_file.touch()
                    test_file.unlink()
                    dir_status["writable"] = True
                    
                    # Calculate size
                    total_size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                    dir_status["size_mb"] = round(total_size / (1024 * 1024), 2)
                except Exception as e:
                    dir_status["error"] = str(e)
                    results["issues"].append(f"{dir_name}: {e}")
                    results["status"] = "degraded"
            else:
                results["issues"].append(f"{dir_name}: Not found")
                results["status"] = "degraded"
            
            results["directories"][dir_name] = dir_status
        
        return results
    
    def check_redis(self) -> Dict[str, Any]:
        """Check Redis connection"""
        try:
            import redis
            r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
            r.ping()
            
            info = r.info()
            return {
                "status": "healthy",
                "connected": True,
                "version": info.get('redis_version', 'unknown'),
                "used_memory_mb": round(info.get('used_memory', 0) / (1024 * 1024), 2),
                "connected_clients": info.get('connected_clients', 0)
            }
        except ImportError:
            return {
                "status": "warning",
                "connected": False,
                "message": "Redis library not installed, using memory backend"
            }
        except Exception as e:
            return {
                "status": "warning",
                "connected": False,
                "error": str(e),
                "message": "Redis not available, using memory backend"
            }
    
    def get_uptime(self) -> str:
        """Get system uptime"""
        uptime_seconds = time.time() - self.start_time
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        return f"{hours}h {minutes}m {seconds}s"
    
    def get_full_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        db_health = self.check_databases()
        sys_health = self.check_system_resources()
        dir_health = self.check_directories()
        redis_health = self.check_redis()
        
        # Determine overall status
        statuses = [
            db_health["status"],
            sys_health["status"],
            dir_health["status"],
            redis_health["status"]
        ]
        
        if "unhealthy" in statuses or "critical" in statuses:
            overall_status = "unhealthy"
        elif "degraded" in statuses or "warning" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "uptime": self.get_uptime(),
            "checks": {
                "databases": db_health,
                "system_resources": sys_health,
                "directories": dir_health,
                "redis": redis_health
            }
        }

def print_health_report():
    """Print formatted health report"""
    checker = HealthChecker()
    report = checker.get_full_health_report()
    
    print("=" * 70)
    print("ORANOLIO RAT - HEALTH CHECK REPORT")
    print("=" * 70)
    print(f"Overall Status: {report['status'].upper()}")
    print(f"Timestamp: {report['timestamp']}")
    print(f"Uptime: {report['uptime']}")
    print()
    
    # Databases
    print("DATABASES:")
    db_check = report['checks']['databases']
    print(f"  Status: {db_check['status']}")
    for db_name, db_info in db_check['databases'].items():
        status_icon = "✓" if db_info['accessible'] else "✗"
        print(f"  {status_icon} {db_name}: {db_info['size_mb']} MB, {db_info['tables']} tables")
    if db_check['issues']:
        print(f"  Issues: {', '.join(db_check['issues'])}")
    print()
    
    # System Resources
    print("SYSTEM RESOURCES:")
    sys_check = report['checks']['system_resources']
    print(f"  Status: {sys_check['status']}")
    print(f"  CPU: {sys_check['cpu']['percent']}% ({sys_check['cpu']['count']} cores)")
    print(f"  Memory: {sys_check['memory']['percent']}% used "
          f"({sys_check['memory']['available_gb']}/{sys_check['memory']['total_gb']} GB available)")
    print(f"  Disk: {sys_check['disk']['percent']}% used "
          f"({sys_check['disk']['free_gb']}/{sys_check['disk']['total_gb']} GB free)")
    if sys_check.get('issues'):
        print(f"  Issues: {', '.join(sys_check['issues'])}")
    print()
    
    # Directories
    print("DIRECTORIES:")
    dir_check = report['checks']['directories']
    print(f"  Status: {dir_check['status']}")
    for dir_name, dir_info in dir_check['directories'].items():
        status_icon = "✓" if dir_info['writable'] else "✗"
        print(f"  {status_icon} {dir_name}: {dir_info['size_mb']} MB")
    if dir_check['issues']:
        print(f"  Issues: {', '.join(dir_check['issues'])}")
    print()
    
    # Redis
    print("REDIS:")
    redis_check = report['checks']['redis']
    print(f"  Status: {redis_check['status']}")
    if redis_check['connected']:
        print(f"  Version: {redis_check['version']}")
        print(f"  Memory: {redis_check['used_memory_mb']} MB")
        print(f"  Clients: {redis_check['connected_clients']}")
    else:
        print(f"  Message: {redis_check.get('message', 'Not connected')}")
    print()
    
    print("=" * 70)
    
    return 0 if report['status'] == "healthy" else 1

if __name__ == "__main__":
    sys.exit(print_health_report())
