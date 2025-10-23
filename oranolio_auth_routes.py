#!/usr/bin/env python3
"""
Oranolio RATX Authentication Routes
Modern login system with email-based authentication
"""

import os
import json
import time
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from email_auth import send_verification_email, verify_code, check_rate_limit, create_email_user, log_email_auth_event
from auth_utils import track_failed_email_login, is_login_locked, clear_failed_login_attempts, validate_email
from config import Config

# Create blueprint for Oranolio auth routes
oranolio_auth_bp = Blueprint('oranolio_auth', __name__, url_prefix='/oranolio')

@oranolio_auth_bp.route('/login', methods=['GET', 'POST'])
def oranolio_login():
    """Oranolio RATX login page"""
    if request.method == 'GET':
        return render_template('oranolio_login.html')
    
    # Handle POST request - send verification code
    data = request.get_json() or request.form
    email = data.get('email', '').strip().lower()
    ip_address = request.remote_addr
    
    # Validate input
    if not email or not validate_email(email):
        return jsonify({
            'success': False,
            'message': 'Please enter a valid email address'
        }), 400
    
    # Check if IP is locked
    if is_login_locked(ip_address):
        return jsonify({
            'success': False,
            'message': 'Too many failed attempts. Please try again later.'
        }), 429
    
    # Check if email is authorized
    if not Config.is_email_authorized(email):
        track_failed_email_login(email, ip_address)
        return jsonify({
            'success': False,
            'message': 'Email address not authorized for access'
        }), 403
    
    try:
        # Check rate limit
        if not check_rate_limit(email):
            return jsonify({
                'success': False,
                'message': 'Too many verification requests. Please wait before requesting another code.'
            }), 429
        
        # Create email user if doesn't exist
        create_email_user(email)
        
        # Send verification email
        success, code, expires_at = send_verification_email(email, ip_address)
        
        if success:
            # Store session info for verification
            session['oranolio_auth_session'] = {
                'email': email,
                'created_at': datetime.now().isoformat(),
                'expires_at': expires_at.isoformat() if expires_at else None
            }
            
            return jsonify({
                'success': True,
                'message': 'Verification code sent to your email',
                'email': email,
                'expires_at': expires_at.isoformat() if expires_at else None
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send verification email. Please try again.'
            }), 500
            
    except Exception as e:
        print(f"Error sending verification email: {e}")
        log_email_auth_event(email, 'send_failed', ip_address, success=False, details={'error': str(e)})
        return jsonify({
            'success': False,
            'message': 'Failed to send verification email'
        }), 500

@oranolio_auth_bp.route('/verify', methods=['POST'])
def oranolio_verify():
    """Verify the email verification code"""
    data = request.get_json() or request.form
    code = data.get('code', '').strip()
    ip_address = request.remote_addr
    
    # Get session info
    auth_session = session.get('oranolio_auth_session')
    if not auth_session:
        return jsonify({
            'success': False,
            'message': 'No active authentication session'
        }), 400
    
    email = auth_session['email']
    
    # Validate code format
    if not code or len(code) != 6 or not code.isdigit():
        return jsonify({
            'success': False,
            'message': 'Please enter a valid 6-digit code'
        }), 400
    
    try:
        # Verify the code
        is_valid = verify_code(email, code)
        
        if is_valid:
            # Clear failed login attempts
            clear_failed_login_attempts(ip_address)
            
            # Set up user session
            session['user'] = {
                'email': email,
                'login_method': 'email',
                'login_time': datetime.now().isoformat(),
                'ip_address': ip_address
            }
            
            # Log successful authentication
            log_email_auth_event(email, 'login_success', ip_address, success=True)
            
            # Clear auth session
            session.pop('oranolio_auth_session', None)
            
            return jsonify({
                'success': True,
                'message': 'Authentication successful',
                'redirect_url': '/dashboard'
            })
        else:
            # Track failed attempt
            track_failed_email_login(email, ip_address)
            
            # Log failed authentication
            log_email_auth_event(email, 'login_failed', ip_address, success=False, details={'code_entered': code})
            
            return jsonify({
                'success': False,
                'message': 'Invalid verification code. Please try again.'
            }), 400
            
    except Exception as e:
        print(f"Error verifying code: {e}")
        log_email_auth_event(email, 'verify_error', ip_address, success=False, details={'error': str(e)})
        return jsonify({
            'success': False,
            'message': 'Verification failed'
        }), 500

@oranolio_auth_bp.route('/resend', methods=['POST'])
def oranolio_resend():
    """Resend verification code"""
    auth_session = session.get('oranolio_auth_session')
    if not auth_session:
        return jsonify({
            'success': False,
            'message': 'No active session'
        }), 400
    
    email = auth_session['email']
    ip_address = request.remote_addr
    
    try:
        # Check rate limit
        if not check_rate_limit(email):
            return jsonify({
                'success': False,
                'message': 'Too many verification requests. Please wait before requesting another code.'
            }), 429
        
        # Send new verification email
        success, code, expires_at = send_verification_email(email, ip_address)
        
        if success:
            # Update session
            session['oranolio_auth_session']['created_at'] = datetime.now().isoformat()
            session['oranolio_auth_session']['expires_at'] = expires_at.isoformat() if expires_at else None
            
            return jsonify({
                'success': True,
                'message': 'New verification code sent',
                'expires_at': expires_at.isoformat() if expires_at else None
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to resend verification code'
            }), 500
            
    except Exception as e:
        print(f"Error resending code: {e}")
        log_email_auth_event(email, 'resend_failed', ip_address, success=False, details={'error': str(e)})
        return jsonify({
            'success': False,
            'message': 'Failed to resend code'
        }), 500

@oranolio_auth_bp.route('/status')
def oranolio_status():
    """Check authentication session status"""
    auth_session = session.get('oranolio_auth_session')
    if not auth_session:
        return jsonify({
            'active': False,
            'message': 'No active session'
        })
    
    # Check if session is expired
    expires_at = auth_session.get('expires_at')
    if expires_at:
        try:
            expires_dt = datetime.fromisoformat(expires_at)
            if datetime.now() > expires_dt:
                session.pop('oranolio_auth_session', None)
                return jsonify({
                    'active': False,
                    'message': 'Session expired'
                })
        except:
            pass
    
    return jsonify({
        'active': True,
        'email': auth_session['email'],
        'created_at': auth_session['created_at'],
        'expires_at': auth_session.get('expires_at')
    })

@oranolio_auth_bp.route('/logout', methods=['POST'])
def oranolio_logout():
    """Logout user"""
    # Clear all session data
    session.clear()
    
    return jsonify({
        'success': True,
        'message': 'Logged out successfully',
        'redirect_url': '/oranolio/login'
    })

# Register the blueprint
def register_oranolio_auth_routes(app):
    """Register Oranolio authentication routes with Flask app"""
    app.register_blueprint(oranolio_auth_bp)