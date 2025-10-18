#!/usr/bin/env python3
"""
Web App Enhancements - Integration module for all new features
This module contains all the integration code for the new security and operational features
"""

import os
import sys
import json
import uuid
import time
import secrets
import logging
import logging.handlers
from datetime import datetime
from functools import wraps
from flask import request, jsonify, g, make_response, send_file, session

# Import our new modules
from config import Config
from auth_utils import (
    api_key_manager, api_key_required, api_key_or_login_required,
    track_failed_login, is_login_locked, get_lockout_time_remaining,
    clear_failed_login_attempts
)
from metrics import metrics_collector
from backup_utils import BackupManager

# ============================================================================
# Enhanced Logging Setup
# ============================================================================
def setup_enhanced_logging(app):
    """Configure enhanced logging with rotation and remote support"""
    
    # Set log level
    log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        Config.LOG_FORMAT,
        datefmt=Config.LOG_DATE_FORMAT
    )
    
    # File handler with rotation
    if Config.ENABLE_FILE_LOGGING:
        try:
            Config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                Config.LOG_FILE,
                maxBytes=Config.LOG_MAX_BYTES,
                backupCount=Config.LOG_BACKUP_COUNT
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(log_level)
            
            app.logger.addHandler(file_handler)
            logging.getLogger().addHandler(file_handler)
            
            app.logger.info(f"File logging enabled: {Config.LOG_FILE}")
        except Exception as e:
            app.logger.error(f"Failed to setup file logging: {e}")
    
    # Syslog handler
    if Config.ENABLE_SYSLOG:
        try:
            syslog_handler = logging.handlers.SysLogHandler(
                address=(Config.SYSLOG_HOST, Config.SYSLOG_PORT)
            )
            syslog_handler.setFormatter(formatter)
            syslog_handler.setLevel(log_level)
            
            app.logger.addHandler(syslog_handler)
            logging.getLogger().addHandler(syslog_handler)
            
            app.logger.info(f"Syslog enabled: {Config.SYSLOG_HOST}:{Config.SYSLOG_PORT}")
        except Exception as e:
            app.logger.error(f"Failed to setup syslog: {e}")
    
    app.logger.setLevel(log_level)
    app.logger.info(f"Enhanced logging initialized at {log_level} level")

# ============================================================================
# Request ID Tracking Middleware
# ============================================================================
def add_request_id():
    """Add unique request ID to each request for tracking"""
    if not hasattr(g, 'request_id'):
        g.request_id = str(uuid.uuid4())
    return g.request_id

def log_request():
    """Log incoming request with request ID"""
    request_id = add_request_id()
    logging.info(f"[{request_id}] {request.method} {request.path} from {request.remote_addr}")

def log_response(response):
    """Log response with request ID"""
    request_id = getattr(g, 'request_id', 'unknown')
    duration = getattr(g, 'request_start_time', 0)
    if duration:
        duration = (time.time() - duration) * 1000  # Convert to milliseconds
        metrics_collector.record_duration('response_time', duration / 1000)
    
    logging.info(f"[{request_id}] Response: {response.status_code} ({duration:.2f}ms)")
    return response

# ============================================================================
# Content Security Policy Middleware
# ============================================================================
def add_csp_headers(response):
    """Add Content Security Policy headers to all responses"""
    if Config.CSP_ENABLED and response.mimetype == 'text/html':
        # Generate nonce for inline scripts
        nonce = secrets.token_urlsafe(16)
        g.csp_nonce = nonce
        
        # Get CSP policy
        csp_policy = Config.get_csp_policy(nonce)
        
        # Add header
        if Config.CSP_REPORT_ONLY:
            response.headers['Content-Security-Policy-Report-Only'] = csp_policy
        else:
            response.headers['Content-Security-Policy'] = csp_policy
    
    # Add other security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    if Config.ENABLE_HTTPS:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response

# ============================================================================
# New API Endpoints
# ============================================================================

def register_config_endpoint(app):
    """Register /api/config endpoint"""
    @app.route('/api/config')
    @api_key_or_login_required
    def api_config():
        """Get public configuration for frontend"""
        metrics_collector.increment_counter('api_requests')
        return jsonify(Config.get_public_config())

def register_api_key_endpoints(app):
    """Register API key management endpoints"""
    
    @app.route('/api/keys', methods=['GET'])
    @api_key_required
    def list_api_keys():
        """List all API keys"""
        metrics_collector.increment_counter('api_requests')
        keys = api_key_manager.list_api_keys()
        return jsonify({'keys': keys})
    
    @app.route('/api/keys', methods=['POST'])
    @api_key_required
    def create_api_key():
        """Create a new API key"""
        metrics_collector.increment_counter('api_requests')
        
        data = request.get_json()
        name = data.get('name', 'Unnamed Key')
        description = data.get('description', '')
        
        if not name:
            return jsonify({'error': 'Key name is required'}), 400
        
        api_key = api_key_manager.generate_api_key(name, description)
        
        return jsonify({
            'message': 'API key created successfully',
            'api_key': api_key,
            'warning': 'Save this key securely. It cannot be retrieved again.'
        })
    
    @app.route('/api/keys/<key_id>', methods=['DELETE'])
    @api_key_required
    def revoke_api_key(key_id):
        """Revoke an API key"""
        metrics_collector.increment_counter('api_requests')
        
        if api_key_manager.revoke_api_key(key_id):
            return jsonify({'message': 'API key revoked successfully'})
        else:
            return jsonify({'error': 'API key not found'}), 404

def register_backup_endpoints(app):
    """Register backup and restore endpoints"""
    
    @app.route('/api/backup', methods=['GET'])
    @api_key_or_login_required
    def create_backup():
        """Create and download backup"""
        metrics_collector.increment_counter('api_requests')
        
        try:
            backup_path, filename, metadata = BackupManager.create_backup()
            
            # Log backup creation
            app.logger.info(f"Backup created: {filename} with {len(metadata['files'])} files")
            
            return send_file(
                backup_path,
                mimetype='application/zip',
                as_attachment=True,
                download_name=filename
            )
        except Exception as e:
            app.logger.error(f"Backup creation failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/restore', methods=['POST'])
    @api_key_required  # More restrictive - only API key auth for restore
    def restore_backup():
        """Restore from backup"""
        metrics_collector.increment_counter('api_requests')
        
        if 'backup' not in request.files:
            return jsonify({'error': 'No backup file provided'}), 400
        
        backup_file = request.files['backup']
        
        # Save uploaded file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            backup_file.save(tmp_file.name)
            tmp_path = tmp_file.name
        
        try:
            # Validate and restore
            success, result = BackupManager.restore_backup(tmp_path)
            
            if success:
                app.logger.info(f"Backup restored successfully: {result['restored_files']}")
                
                # Reload configuration
                Config.reload()
                
                return jsonify(result)
            else:
                return jsonify({'error': result}), 400
                
        except Exception as e:
            app.logger.error(f"Restore failed: {e}")
            return jsonify({'error': str(e)}), 500
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    @app.route('/api/backups', methods=['GET'])
    @api_key_or_login_required
    def list_backups():
        """List available backups"""
        metrics_collector.increment_counter('api_requests')
        backups = BackupManager.list_backups()
        return jsonify({'backups': backups})

def register_metrics_endpoint(app):
    """Register metrics endpoint"""
    
    @app.route('/metrics')
    def metrics():
        """Prometheus-compatible metrics endpoint"""
        if Config.METRICS_AUTH_REQUIRED:
            # Check authentication
            if Config.ENABLE_API_KEYS:
                api_key = request.headers.get(Config.API_KEY_HEADER)
                if not api_key or not api_key_manager.validate_api_key(api_key):
                    if 'user' not in session:
                        return jsonify({'error': 'Authentication required'}), 401
            elif 'user' not in session:
                return jsonify({'error': 'Authentication required'}), 401
        
        # Generate metrics
        prometheus_metrics = metrics_collector.generate_prometheus_metrics()
        
        response = make_response(prometheus_metrics)
        response.mimetype = 'text/plain; version=0.0.4'
        return response
    
    @app.route('/api/metrics')
    @api_key_or_login_required
    def api_metrics():
        """JSON metrics endpoint"""
        metrics_collector.increment_counter('api_requests')
        return jsonify(metrics_collector.get_json_metrics())

def register_config_reload_endpoint(app):
    """Register configuration reload endpoint"""
    
    @app.route('/api/config/reload', methods=['POST'])
    @api_key_required
    def reload_config():
        """Reload configuration from environment variables"""
        metrics_collector.increment_counter('api_requests')
        
        try:
            new_config = Config.reload()
            app.logger.info("Configuration reloaded successfully")
            
            return jsonify({
                'message': 'Configuration reloaded successfully',
                'config': Config.get_public_config()
            })
        except Exception as e:
            app.logger.error(f"Configuration reload failed: {e}")
            return jsonify({'error': str(e)}), 500

# ============================================================================
# Enhanced Connection Management
# ============================================================================

class ConnectionManager:
    """Enhanced connection management with pooling and heartbeat"""
    
    def __init__(self):
        self.connection_pool = {}
        self.last_heartbeat = {}
        self.connection_latency = {}
    
    def update_heartbeat(self, conn_id):
        """Update heartbeat timestamp for a connection"""
        self.last_heartbeat[conn_id] = time.time()
    
    def get_connection_status(self, conn_id):
        """Get enhanced connection status"""
        if conn_id not in self.last_heartbeat:
            return 'offline'
        
        time_since_heartbeat = time.time() - self.last_heartbeat[conn_id]
        
        if time_since_heartbeat < Config.HEARTBEAT_INTERVAL_SECONDS:
            return 'online'
        elif time_since_heartbeat < Config.CONNECTION_TIMEOUT_SECONDS:
            return 'idle'
        else:
            return 'stale'
    
    def cleanup_stale_connections(self):
        """Remove stale connections"""
        current_time = time.time()
        stale_threshold = Config.STALE_CONNECTION_THRESHOLD
        
        stale_connections = []
        for conn_id, last_seen in self.last_heartbeat.items():
            if current_time - last_seen > stale_threshold:
                stale_connections.append(conn_id)
        
        for conn_id in stale_connections:
            self.remove_connection(conn_id)
            logging.info(f"Removed stale connection: {conn_id}")
    
    def remove_connection(self, conn_id):
        """Remove a connection from tracking"""
        self.last_heartbeat.pop(conn_id, None)
        self.connection_latency.pop(conn_id, None)
        if conn_id in self.connection_pool:
            del self.connection_pool[conn_id]
    
    def get_connection_info(self, conn_id):
        """Get detailed connection information"""
        return {
            'status': self.get_connection_status(conn_id),
            'last_heartbeat': self.last_heartbeat.get(conn_id),
            'latency': self.connection_latency.get(conn_id, 0),
            'time_since_heartbeat': time.time() - self.last_heartbeat.get(conn_id, 0)
        }

# Global connection manager instance
connection_manager = ConnectionManager()

# ============================================================================
# Integration Function
# ============================================================================

def integrate_enhancements(app, socketio, limiter):
    """Integrate all enhancements into the Flask app"""
    
    # Setup enhanced logging
    setup_enhanced_logging(app)
    
    # Update Flask configuration with Config values
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config['SESSION_COOKIE_HTTPONLY'] = Config.SESSION_COOKIE_HTTPONLY
    app.config['SESSION_COOKIE_SAMESITE'] = Config.SESSION_COOKIE_SAMESITE
    app.config['SESSION_COOKIE_SECURE'] = Config.SESSION_COOKIE_SECURE
    app.config['PERMANENT_SESSION_LIFETIME'] = Config.PERMANENT_SESSION_LIFETIME
    app.config['WTF_CSRF_TIME_LIMIT'] = None
    app.config['WTF_CSRF_SSL_STRICT'] = Config.WTF_CSRF_SSL_STRICT
    
    # Update rate limiter with configurable values
    limiter._default_limits = [
        f"{Config.DEFAULT_RATE_LIMIT_DAY} per day",
        f"{Config.DEFAULT_RATE_LIMIT_HOUR} per hour"
    ]
    
    # Register middleware
    @app.before_request
    def before_request():
        g.request_start_time = time.time()
        log_request()
    
    @app.after_request
    def after_request(response):
        response = add_csp_headers(response)
        response = log_response(response)
        return response
    
    # Register new endpoints
    register_config_endpoint(app)
    
    if Config.ENABLE_API_KEYS:
        register_api_key_endpoints(app)
    
    if Config.ENABLE_BACKUP_RESTORE:
        register_backup_endpoints(app)
    
    if Config.ENABLE_METRICS:
        register_metrics_endpoint(app)
    
    register_config_reload_endpoint(app)
    
    # Setup connection cleanup task
    def cleanup_connections():
        while True:
            time.sleep(60)  # Run every minute
            connection_manager.cleanup_stale_connections()
            metrics_collector.set_gauge('active_connections', len(connection_manager.last_heartbeat))
    
    import threading
    cleanup_thread = threading.Thread(target=cleanup_connections, daemon=True)
    cleanup_thread.start()
    
    app.logger.info("All enhancements integrated successfully")
    
    return app, socketio, limiter

# ============================================================================
# Export Functions
# ============================================================================

__all__ = [
    'integrate_enhancements',
    'connection_manager',
    'metrics_collector',
    'Config'
]