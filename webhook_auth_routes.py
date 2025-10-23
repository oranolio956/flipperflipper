#!/usr/bin/env python3
"""
Webhook Authentication Routes
Flask routes for webhook-based authentication system
"""

import os
import json
import time
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
from webhook_auth_manager import webhook_auth_manager
from mfa_manager import mfa_manager
from webhook_mfa_integration import webhook_mfa
from auth_utils import track_failed_login, is_login_locked, clear_failed_login_attempts
from config import Config

# Create blueprint for webhook auth routes
webhook_auth_bp = Blueprint('webhook_auth', __name__, url_prefix='/webhook-auth')

@webhook_auth_bp.route('/login', methods=['GET', 'POST'])
def webhook_login():
    """Webhook-based login page"""
    if request.method == 'GET':
        return render_template('webhook_login.html')
    
    # Handle POST request
    data = request.get_json() or request.form
    user_identifier = data.get('email', '').strip().lower()
    ip_address = request.remote_addr
    
    # Validate input
    if not user_identifier or '@' not in user_identifier:
        return jsonify({
            'success': False,
            'message': 'Please enter a valid email address'
        }), 400
    
    # Check if IP is locked
    if is_login_locked(ip_address):
        lockout_time = webhook_auth_manager.get_session_status('dummy')  # Get remaining time
        return jsonify({
            'success': False,
            'message': f'Too many failed attempts. Please try again later.'
        }), 429
    
    # Check if email is authorized
    if not Config.is_email_authorized(user_identifier):
        track_failed_login(ip_address, user_identifier)
        return jsonify({
            'success': False,
            'message': 'Email address not authorized for access'
        }), 403
    
    try:
        # Generate authentication code
        session_id, display_code = webhook_auth_manager.generate_auth_code(user_identifier, ip_address)
        
        # Store session info for verification
        session['webhook_auth_session'] = {
            'session_id': session_id,
            'user_identifier': user_identifier,
            'created_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'message': f'Authentication code sent to webhook. Check your webhook dashboard.',
            'session_id': session_id,
            'display_code': display_code  # For testing - remove in production
        })
        
    except Exception as e:
        print(f"Error generating auth code: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to generate authentication code'
        }), 500

@webhook_auth_bp.route('/verify', methods=['POST'])
def verify_code():
    """Verify the authentication code"""
    data = request.get_json() or request.form
    entered_code = data.get('code', '').strip()
    ip_address = request.remote_addr
    
    # Get session info
    webhook_session = session.get('webhook_auth_session')
    if not webhook_session:
        return jsonify({
            'success': False,
            'message': 'No active authentication session'
        }), 400
    
    session_id = webhook_session['session_id']
    user_identifier = webhook_session['user_identifier']
    
    try:
        # Verify the code
        is_valid, message, session_data = webhook_auth_manager.verify_auth_code(
            session_id, entered_code, ip_address
        )
        
        if is_valid:
            # Clear failed login attempts
            clear_failed_login_attempts(ip_address)
            
            # Set up user session
            session['user'] = {
                'email': user_identifier,
                'login_method': 'webhook',
                'login_time': datetime.now().isoformat(),
                'ip_address': ip_address
            }
            
            # Send success notification
            webhook_auth_manager.send_verification_notification(
                user_identifier, True, ip_address
            )
            
            # Check if MFA is required
            mfa_status = webhook_mfa.get_mfa_status(user_identifier)
            mfa_required = mfa_status['setup_required']
            
            return jsonify({
                'success': True,
                'message': 'Authentication successful',
                'mfa_required': mfa_required,
                'mfa_status': mfa_status,
                'redirect_url': '/webhook-mfa-setup' if mfa_required else '/webhook-mfa-verify'
            })
        else:
            # Track failed attempt
            track_failed_login(ip_address, user_identifier)
            
            # Send failure notification
            webhook_auth_manager.send_verification_notification(
                user_identifier, False, ip_address
            )
            
            return jsonify({
                'success': False,
                'message': message
            }), 400
            
    except Exception as e:
        print(f"Error verifying code: {e}")
        return jsonify({
            'success': False,
            'message': 'Verification failed'
        }), 500

@webhook_auth_bp.route('/status/<session_id>')
def check_status(session_id):
    """Check authentication session status"""
    try:
        session_data = webhook_auth_manager.get_session_status(session_id)
        
        if not session_data:
            return jsonify({
                'exists': False,
                'message': 'Session not found or expired'
            })
        
        return jsonify({
            'exists': True,
            'verified': session_data.get('verified', False),
            'attempts': session_data.get('attempts', 0),
            'max_attempts': session_data.get('max_attempts', 3),
            'expires_at': session_data.get('expires_at'),
            'user_identifier': session_data.get('user_identifier')
        })
        
    except Exception as e:
        print(f"Error checking status: {e}")
        return jsonify({
            'exists': False,
            'message': 'Error checking session status'
        }), 500

@webhook_auth_bp.route('/resend', methods=['POST'])
def resend_code():
    """Resend authentication code"""
    webhook_session = session.get('webhook_auth_session')
    if not webhook_session:
        return jsonify({
            'success': False,
            'message': 'No active session'
        }), 400
    
    user_identifier = webhook_session['user_identifier']
    ip_address = request.remote_addr
    
    try:
        # Generate new code
        session_id, display_code = webhook_auth_manager.generate_auth_code(user_identifier, ip_address)
        
        # Update session
        session['webhook_auth_session']['session_id'] = session_id
        
        return jsonify({
            'success': True,
            'message': 'New authentication code sent',
            'session_id': session_id,
            'display_code': display_code  # For testing
        })
        
    except Exception as e:
        print(f"Error resending code: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to resend code'
        }), 500

@webhook_auth_bp.route('/webhook-dashboard')
def webhook_dashboard():
    """Display webhook requests for monitoring"""
    try:
        requests_data = webhook_auth_manager.get_webhook_requests()
        return render_template('webhook_dashboard.html', requests=requests_data)
    except Exception as e:
        print(f"Error loading webhook dashboard: {e}")
        return render_template('webhook_dashboard.html', requests=[], error=str(e))

@webhook_auth_bp.route('/mfa-setup', methods=['GET', 'POST'])
def mfa_setup():
    """MFA setup page for webhook-authenticated users"""
    if 'user' not in session:
        return redirect(url_for('webhook_auth.webhook_login'))
    
    user_identifier = session['user']['email']
    
    if request.method == 'GET':
        # Check if MFA is already set up
        mfa_status = webhook_mfa.get_mfa_status(user_identifier)
        if not mfa_status['setup_required']:
            return redirect(url_for('webhook_auth.mfa_verify'))
        
        # Start MFA setup
        setup_result = webhook_mfa.setup_mfa(user_identifier)
        if setup_result['success']:
            # Store setup data in session
            session['mfa_setup'] = {
                'secret': setup_result['secret'],
                'backup_codes': setup_result['backup_codes']
            }
            return render_template('webhook_mfa_setup.html', 
                                 qr_code=setup_result['qr_code'],
                                 backup_codes=setup_result['backup_codes'])
        else:
            flash(setup_result['message'], 'error')
            return redirect(url_for('webhook_auth.webhook_login'))
    
    # Handle POST - verify setup
    data = request.get_json() or request.form
    token = data.get('token', '').strip()
    
    if not token:
        return jsonify({
            'success': False,
            'message': 'Verification code is required'
        }), 400
    
    verify_result = webhook_mfa.verify_mfa_setup(user_identifier, token)
    
    if verify_result['success']:
        # Clear setup data from session
        session.pop('mfa_setup', None)
        return jsonify({
            'success': True,
            'message': 'MFA setup completed successfully!',
            'redirect_url': '/dashboard'
        })
    else:
        return jsonify({
            'success': False,
            'message': verify_result['message']
        }), 400

@webhook_auth_bp.route('/mfa-verify', methods=['GET', 'POST'])
def mfa_verify():
    """MFA verification page for webhook-authenticated users"""
    if 'user' not in session:
        return redirect(url_for('webhook_auth.webhook_login'))
    
    user_identifier = session['user']['email']
    mfa_status = webhook_mfa.get_mfa_status(user_identifier)
    
    if mfa_status['setup_required']:
        return redirect(url_for('webhook_auth.mfa_setup'))
    
    if request.method == 'GET':
        return render_template('webhook_mfa_verify.html', 
                             user_identifier=user_identifier)
    
    # Handle POST - verify MFA
    data = request.get_json() or request.form
    token = data.get('token', '').strip()
    use_backup = data.get('use_backup', 'false').lower() == 'true'
    
    if not token:
        return jsonify({
            'success': False,
            'message': 'Verification code is required'
        }), 400
    
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    
    if use_backup:
        verify_result = webhook_mfa.verify_backup_code(user_identifier, token, ip_address, user_agent)
    else:
        verify_result = webhook_mfa.verify_mfa_login(user_identifier, token, ip_address, user_agent)
    
    if verify_result['success']:
        # Mark MFA as verified in session
        session['user']['mfa_verified'] = True
        session['user']['mfa_verified_at'] = datetime.now().isoformat()
        
        return jsonify({
            'success': True,
            'message': 'MFA verification successful!',
            'redirect_url': '/dashboard'
        })
    else:
        return jsonify({
            'success': False,
            'message': verify_result['message']
        }), 400

def _check_mfa_required(user_identifier):
    """Check if MFA setup is required for user"""
    mfa_status = webhook_mfa.get_mfa_status(user_identifier)
    return mfa_status['setup_required']

# Register the blueprint
def register_webhook_auth_routes(app):
    """Register webhook authentication routes with Flask app"""
    app.register_blueprint(webhook_auth_bp)