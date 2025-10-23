#!/usr/bin/env python3
"""
Authentication Routes for Oranolio RAT - Elite C2 Framework
Handles login, logout, registration, and MFA
"""

import os
import sys
import logging
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, g
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import authentication utilities
from auth_utils import (
    auth_manager, session_manager, mfa_manager, 
    login_required, track_failed_login, is_login_locked, 
    get_lockout_time_remaining, clear_failed_login_attempts
)
from validation_schemas import validate_input
from error_handler import error_handler, ErrorSeverity, ErrorCategory, ErrorContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'GET':
        return render_template('login.html')
    
    try:
        # Validate input
        data = request.get_json() if request.is_json else request.form
        validation_result = validate_input('login', data)
        
        if not validation_result.is_valid:
            if request.is_json:
                return jsonify({'error': 'Validation failed', 'details': validation_result.errors}), 400
            flash('Invalid input data', 'error')
            return render_template('login.html')
        
        email = validation_result.sanitized_value['email']
        password = validation_result.sanitized_value['password']
        remember_me = validation_result.sanitized_value.get('remember_me', 'false') == 'true'
        
        # Get client information
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        
        # Check if account is locked
        if is_login_locked(email):
            remaining_time = get_lockout_time_remaining(email)
            error_msg = f"Account locked due to too many failed attempts. Try again in {remaining_time} seconds."
            
            if request.is_json:
                return jsonify({'error': error_msg}), 423
            flash(error_msg, 'error')
            return render_template('login.html')
        
        # Authenticate user
        user = auth_manager.authenticate_user(email, password, ip_address, user_agent)
        
        if not user:
            error_msg = "Invalid email or password"
            
            if request.is_json:
                return jsonify({'error': error_msg}), 401
            flash(error_msg, 'error')
            return render_template('login.html')
        
        # Check if user is active
        if not user.is_active:
            error_msg = "Account is deactivated"
            
            if request.is_json:
                return jsonify({'error': error_msg}), 403
            flash(error_msg, 'error')
            return render_template('login.html')
        
        # Regenerate session to prevent session fixation attacks
        # Save Flask internal session data
        old_session_data = {k: v for k, v in session.items() if k.startswith('_')}
        session.clear()
        session.update(old_session_data)
        
        # Create new session with user data
        session_token = session_manager.create_session_token(user)
        session.permanent = True if remember_me else False
        session['user_id'] = user.id
        session['email'] = user.email
        session['session_token'] = session_token
        session['login_time'] = datetime.utcnow().isoformat()
        session['ip_address'] = ip_address
        session['user_agent'] = user_agent[:200] if user_agent else ''
        
        # Log successful login
        logger.info(f"User logged in: {email} from {ip_address}")
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'is_verified': user.is_verified
                }
            })
        
        # Redirect to dashboard
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('index'))
        
    except Exception as e:
        context = ErrorContext(
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.HIGH, ErrorCategory.AUTHENTICATION)
        
        error_msg = "An error occurred during login"
        
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        flash(error_msg, 'error')
        return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    try:
        email = session.get('email', 'unknown')
        
        # Clear session
        session.clear()
        
        logger.info(f"User logged out: {email}")
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Logout successful'})
        
        flash('You have been logged out', 'info')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        context = ErrorContext(
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.AUTHENTICATION)
        
        if request.is_json:
            return jsonify({'error': 'Logout failed'}), 500
        
        return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if request.method == 'GET':
        return render_template('register.html')
    
    try:
        # Validate input
        data = request.get_json() if request.is_json else request.form
        validation_result = validate_input('register', data)
        
        if not validation_result.is_valid:
            if request.is_json:
                return jsonify({'error': 'Validation failed', 'details': validation_result.errors}), 400
            flash('Invalid input data', 'error')
            return render_template('register.html')
        
        email = validation_result.sanitized_value['email']
        password = validation_result.sanitized_value['password']
        confirm_password = validation_result.sanitized_value['confirm_password']
        full_name = validation_result.sanitized_value.get('full_name', '')
        
        # Check password confirmation
        if password != confirm_password:
            error_msg = "Passwords do not match"
            
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('register.html')
        
        # Create user
        success = auth_manager.create_user(email, password, full_name)
        
        if not success:
            error_msg = "Email already exists or registration failed"
            
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('register.html')
        
        logger.info(f"User registered: {email}")
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Registration successful. Please log in.'
            })
        
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        context = ErrorContext(
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.HIGH, ErrorCategory.AUTHENTICATION)
        
        error_msg = "An error occurred during registration"
        
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        flash(error_msg, 'error')
        return render_template('register.html')

@auth_bp.route('/mfa/setup', methods=['GET', 'POST'])
@login_required
def setup_mfa():
    """Setup MFA for the current user"""
    try:
        user_id = session['user_id']
        
        if request.method == 'GET':
            # Generate TOTP setup
            secret, qr_code = mfa_manager.setup_totp(user_id)
            
            if not secret:
                if request.is_json:
                    return jsonify({'error': 'Failed to setup MFA'}), 500
                flash('Failed to setup MFA', 'error')
                return redirect(url_for('dashboard'))
            
            if request.is_json:
                return jsonify({
                    'secret': secret,
                    'qr_code': qr_code
                })
            
            return render_template('mfa_setup.html', secret=secret, qr_code=qr_code)
        
        # POST - Verify and enable MFA
        data = request.get_json() if request.is_json else request.form
        token = data.get('token')
        
        if not token:
            if request.is_json:
                return jsonify({'error': 'Token required'}), 400
            flash('Token required', 'error')
            return redirect(url_for('auth.setup_mfa'))
        
        # Verify token
        if not mfa_manager.verify_totp(user_id, token):
            if request.is_json:
                return jsonify({'error': 'Invalid token'}), 400
            flash('Invalid token', 'error')
            return redirect(url_for('auth.setup_mfa'))
        
        # Enable MFA
        success = mfa_manager.enable_mfa(user_id, 'totp')
        
        if not success:
            if request.is_json:
                return jsonify({'error': 'Failed to enable MFA'}), 500
            flash('Failed to enable MFA', 'error')
            return redirect(url_for('auth.setup_mfa'))
        
        logger.info(f"MFA enabled for user {user_id}")
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'MFA enabled successfully'})
        
        flash('MFA enabled successfully', 'success')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        context = ErrorContext(
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.HIGH, ErrorCategory.AUTHENTICATION)
        
        if request.is_json:
            return jsonify({'error': 'MFA setup failed'}), 500
        flash('MFA setup failed', 'error')
        return redirect(url_for('dashboard'))

@auth_bp.route('/mfa/verify', methods=['POST'])
def verify_mfa():
    """Verify MFA token"""
    try:
        data = request.get_json() if request.is_json else request.form
        token = data.get('token')
        user_id = session.get('user_id')
        
        if not token or not user_id:
            if request.is_json:
                return jsonify({'error': 'Token and user ID required'}), 400
            return jsonify({'error': 'Token and user ID required'}), 400
        
        # Verify token
        if not mfa_manager.verify_totp(user_id, token):
            if request.is_json:
                return jsonify({'error': 'Invalid token'}), 400
            return jsonify({'error': 'Invalid token'}), 400
        
        # Mark MFA as verified in session
        session['mfa_verified'] = True
        
        logger.info(f"MFA verified for user {user_id}")
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'MFA verified successfully'})
        
        return jsonify({'success': True, 'message': 'MFA verified successfully'})
        
    except Exception as e:
        context = ErrorContext(
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.HIGH, ErrorCategory.AUTHENTICATION)
        
        if request.is_json:
            return jsonify({'error': 'MFA verification failed'}), 500
        return jsonify({'error': 'MFA verification failed'}), 500

@auth_bp.route('/api-keys', methods=['GET', 'POST', 'DELETE'])
@login_required
def manage_api_keys():
    """Manage API keys for the current user"""
    try:
        user_id = session['user_id']
        
        if request.method == 'GET':
            # List API keys
            from auth_utils import api_key_manager
            keys = api_key_manager.list_keys(user_id)
            
            if request.is_json:
                return jsonify({'api_keys': keys})
            
            return render_template('api_keys.html', api_keys=keys)
        
        elif request.method == 'POST':
            # Create new API key
            data = request.get_json() if request.is_json else request.form
            name = data.get('name')
            permissions = data.get('permissions', ['read'])
            
            if not name:
                if request.is_json:
                    return jsonify({'error': 'Name required'}), 400
                flash('Name required', 'error')
                return redirect(url_for('auth.manage_api_keys'))
            
            from auth_utils import api_key_manager
            api_key = api_key_manager.create_key(user_id, name, permissions)
            
            if not api_key:
                if request.is_json:
                    return jsonify({'error': 'Failed to create API key'}), 500
                flash('Failed to create API key', 'error')
                return redirect(url_for('auth.manage_api_keys'))
            
            logger.info(f"API key created for user {user_id}: {name}")
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'api_key': api_key,
                    'message': 'API key created successfully'
                })
            
            flash('API key created successfully', 'success')
            return redirect(url_for('auth.manage_api_keys'))
        
        elif request.method == 'DELETE':
            # Revoke API key
            data = request.get_json() if request.is_json else request.form
            key_id = data.get('key_id')
            
            if not key_id:
                if request.is_json:
                    return jsonify({'error': 'Key ID required'}), 400
                return jsonify({'error': 'Key ID required'}), 400
            
            from auth_utils import api_key_manager
            success = api_key_manager.revoke_key(key_id)
            
            if not success:
                if request.is_json:
                    return jsonify({'error': 'Failed to revoke API key'}), 500
                flash('Failed to revoke API key', 'error')
                return redirect(url_for('auth.manage_api_keys'))
            
            logger.info(f"API key revoked: {key_id}")
            
            if request.is_json:
                return jsonify({'success': True, 'message': 'API key revoked successfully'})
            
            flash('API key revoked successfully', 'success')
            return redirect(url_for('auth.manage_api_keys'))
        
    except Exception as e:
        context = ErrorContext(
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.HIGH, ErrorCategory.AUTHENTICATION)
        
        if request.is_json:
            return jsonify({'error': 'API key management failed'}), 500
        flash('API key management failed', 'error')
        return redirect(url_for('auth.manage_api_keys'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    try:
        user_id = session['user_id']
        user = auth_manager.get_user_by_id(user_id)
        
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('auth.login'))
        
        if request.is_json:
            return jsonify({
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'is_active': user.is_active,
                    'is_verified': user.is_verified,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None
                }
            })
        
        return render_template('profile.html', user=user)
        
    except Exception as e:
        context = ErrorContext(
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.AUTHENTICATION)
        
        if request.is_json:
            return jsonify({'error': 'Profile retrieval failed'}), 500
        flash('Profile retrieval failed', 'error')
        return redirect(url_for('dashboard'))

# Example usage and testing
if __name__ == "__main__":
    print("Authentication Routes")
    print("=" * 30)
    print("Routes registered:")
    print("  GET  /auth/login - Login page")
    print("  POST /auth/login - Process login")
    print("  GET  /auth/logout - Logout")
    print("  GET  /auth/register - Registration page")
    print("  POST /auth/register - Process registration")
    print("  GET  /auth/mfa/setup - MFA setup page")
    print("  POST /auth/mfa/setup - Process MFA setup")
    print("  POST /auth/mfa/verify - Verify MFA token")
    print("  GET  /auth/api-keys - API keys management")
    print("  POST /auth/api-keys - Create API key")
    print("  DELETE /auth/api-keys - Revoke API key")
    print("  GET  /auth/profile - User profile")
    print("Authentication routes ready!")