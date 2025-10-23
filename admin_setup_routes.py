#!/usr/bin/env python3
"""
Admin Setup Routes
One-time admin account creation with token validation
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, g, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from admin_setup import AdminSetupManager
import logging
import secrets
import bleach

logger = logging.getLogger(__name__)

admin_setup_bp = Blueprint('admin_setup', __name__, url_prefix='/admin')

# Mark this blueprint to skip CSRF
admin_setup_bp._got_registered_once = False

# Initialize manager
setup_manager = AdminSetupManager()

# Rate limiter for this blueprint
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

def sanitize_input(text):
    """Sanitize user input to prevent XSS"""
    if not text:
        return text
    return bleach.clean(str(text), tags=[], strip=True)

@admin_setup_bp.route('/setup', methods=['GET'])
@limiter.limit("10 per minute")  # Rate limit page access
def setup_page():
    """Display admin setup page if token is valid"""
    token = sanitize_input(request.args.get('token'))
    
    if not token:
        logger.warning(f"Setup page accessed without token from {request.remote_addr}")
        return render_template('admin_setup_error.html', 
                             error="No setup token provided"), 400
    
    # Validate token
    valid, message = setup_manager.validate_token(token)
    
    if not valid:
        logger.warning(f"Invalid token attempt from {request.remote_addr}: {message}")
        return render_template('admin_setup_error.html', 
                             error=message), 403
    
    # Check if admin already exists
    if setup_manager.admin_exists():
        logger.warning(f"Setup attempted but admin exists from {request.remote_addr}")
        return render_template('admin_setup_error.html',
                             error="Admin account already exists"), 403
    
    # Generate CSRF token for form
    csrf_token = secrets.token_urlsafe(32)
    session['setup_csrf_token'] = csrf_token
    
    # Show setup form with CSRF token
    return render_template('admin_setup.html', token=token, csrf_token=csrf_token)

@admin_setup_bp.route('/setup', methods=['POST'])
@limiter.limit("5 per minute")  # Rate limit: 5 attempts per minute
def create_admin():
    """Create admin account with security hardening"""
    # Get and sanitize inputs
    token = sanitize_input(request.form.get('token'))
    username = sanitize_input(request.form.get('username'))
    password = request.form.get('password')  # Don't sanitize password
    password_confirm = request.form.get('password_confirm')
    csrf_token = request.form.get('csrf_token')
    
    # CSRF validation
    if not csrf_token or csrf_token != session.get('setup_csrf_token'):
        logger.warning(f"CSRF validation failed from {request.remote_addr}")
        return jsonify({'error': 'Invalid security token'}), 403
    
    # Clear CSRF token after use
    session.pop('setup_csrf_token', None)
    
    # Validation
    if not all([token, username, password, password_confirm]):
        return jsonify({'error': 'All fields required'}), 400
    
    if password != password_confirm:
        return jsonify({'error': 'Passwords do not match'}), 400
    
    # Create admin account (includes strong validation)
    success, message = setup_manager.create_admin_account(token, username, password)
    
    if not success:
        logger.warning(f"Admin account creation failed: {message} from {request.remote_addr}")
        return jsonify({'error': message}), 400
    
    # Mark token as used
    setup_manager.mark_token_used(token, request.remote_addr)
    
    logger.info(f"Admin account created: {username} from {request.remote_addr}")
    
    # Set secure session with regeneration
    session.clear()  # Clear any existing session data
    session['admin_username'] = username
    session['is_admin'] = True
    session['authenticated'] = True
    session['session_id'] = secrets.token_urlsafe(32)
    session.permanent = True  # Use permanent session with timeout
    
    return jsonify({
        'success': True,
        'message': 'Admin account created successfully',
        'redirect': '/admin/dashboard'
    })

@admin_setup_bp.route('/dashboard')
def admin_dashboard():
    """Admin dashboard - requires admin session"""
    if not session.get('is_admin'):
        return redirect('/auth/login')
    
    return render_template('admin_dashboard.html',
                         username=session.get('admin_username'))

@admin_setup_bp.route('/check-setup')
def check_setup():
    """Check if admin setup is needed"""
    needs_setup = not setup_manager.admin_exists()
    
    return jsonify({
        'needs_setup': needs_setup,
        'admin_exists': setup_manager.admin_exists()
    })
