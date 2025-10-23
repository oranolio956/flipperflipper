"""
Enterprise Health Check System
Provides comprehensive health monitoring for production deployments
"""

from flask import Blueprint, jsonify
import psutil
import time
import os
from datetime import datetime

health_bp = Blueprint('health', __name__)

# Track application start time
START_TIME = time.time()

def get_system_health():
    """Get comprehensive system health metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'status': 'healthy',
            'cpu': {
                'usage_percent': cpu_percent,
                'status': 'healthy' if cpu_percent < 80 else 'warning'
            },
            'memory': {
                'total_mb': round(memory.total / (1024 * 1024), 2),
                'available_mb': round(memory.available / (1024 * 1024), 2),
                'usage_percent': memory.percent,
                'status': 'healthy' if memory.percent < 85 else 'warning'
            },
            'disk': {
                'total_gb': round(disk.total / (1024 * 1024 * 1024), 2),
                'free_gb': round(disk.free / (1024 * 1024 * 1024), 2),
                'usage_percent': disk.percent,
                'status': 'healthy' if disk.percent < 90 else 'warning'
            }
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def get_database_health():
    """Check database connectivity"""
    try:
        import sqlite3
        # Quick check of main databases
        databases = [
            'Application/admin_setup.db',
            'data/email_auth.db',
            'data/mfa_auth.db'
        ]
        
        db_status = {}
        for db_path in databases:
            if os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute('SELECT 1')
                    conn.close()
                    db_status[db_path] = 'healthy'
                except Exception as e:
                    db_status[db_path] = f'error: {str(e)}'
            else:
                db_status[db_path] = 'not_found'
        
        return {
            'status': 'healthy' if all(v == 'healthy' for v in db_status.values()) else 'degraded',
            'databases': db_status
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Basic health check endpoint
    Returns 200 if service is running
    """
    uptime_seconds = time.time() - START_TIME
    
    return jsonify({
        'status': 'healthy',
        'service': 'Oranolio RAT - Elite C2 Framework',
        'timestamp': datetime.utcnow().isoformat(),
        'uptime_seconds': round(uptime_seconds, 2),
        'version': '1.0.0'
    }), 200

@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """
    Detailed health check with system metrics
    For monitoring systems and dashboards
    """
    uptime_seconds = time.time() - START_TIME
    system_health = get_system_health()
    db_health = get_database_health()
    
    # Determine overall status
    statuses = [system_health['status'], db_health['status']]
    if 'error' in statuses:
        overall_status = 'unhealthy'
        status_code = 503
    elif 'warning' in statuses or 'degraded' in statuses:
        overall_status = 'degraded'
        status_code = 200
    else:
        overall_status = 'healthy'
        status_code = 200
    
    return jsonify({
        'status': overall_status,
        'service': 'Oranolio RAT - Elite C2 Framework',
        'timestamp': datetime.utcnow().isoformat(),
        'uptime_seconds': round(uptime_seconds, 2),
        'version': '1.0.0',
        'system': system_health,
        'database': db_health,
        'checks': {
            'system': system_health['status'],
            'database': db_health['status']
        }
    }), status_code

@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """
    Kubernetes-style readiness probe
    Returns 200 when service is ready to accept traffic
    """
    db_health = get_database_health()
    
    if db_health['status'] == 'healthy':
        return jsonify({
            'status': 'ready',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    else:
        return jsonify({
            'status': 'not_ready',
            'reason': 'database_unavailable',
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """
    Kubernetes-style liveness probe
    Returns 200 if service is alive (even if not ready)
    """
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@health_bp.route('/metrics', methods=['GET'])
def prometheus_metrics():
    """
    Prometheus-compatible metrics endpoint
    """
    uptime_seconds = time.time() - START_TIME
    system_health = get_system_health()
    
    metrics = []
    
    # Uptime metric
    metrics.append(f'# HELP app_uptime_seconds Application uptime in seconds')
    metrics.append(f'# TYPE app_uptime_seconds gauge')
    metrics.append(f'app_uptime_seconds {uptime_seconds}')
    
    # CPU metric
    if 'cpu' in system_health:
        metrics.append(f'# HELP system_cpu_usage_percent CPU usage percentage')
        metrics.append(f'# TYPE system_cpu_usage_percent gauge')
        metrics.append(f'system_cpu_usage_percent {system_health["cpu"]["usage_percent"]}')
    
    # Memory metrics
    if 'memory' in system_health:
        metrics.append(f'# HELP system_memory_usage_percent Memory usage percentage')
        metrics.append(f'# TYPE system_memory_usage_percent gauge')
        metrics.append(f'system_memory_usage_percent {system_health["memory"]["usage_percent"]}')
    
    # Disk metrics
    if 'disk' in system_health:
        metrics.append(f'# HELP system_disk_usage_percent Disk usage percentage')
        metrics.append(f'# TYPE system_disk_usage_percent gauge')
        metrics.append(f'system_disk_usage_percent {system_health["disk"]["usage_percent"]}')
    
    return '\n'.join(metrics), 200, {'Content-Type': 'text/plain; charset=utf-8'}
