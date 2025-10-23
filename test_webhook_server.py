#!/usr/bin/env python3
"""
Test Webhook Authentication Server
Simplified server to demonstrate webhook authentication system
"""

import os
import sys
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from webhook_auth_routes import register_webhook_auth_routes
from config import Config

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Initialize rate limiter
limiter = Limiter(
    app,
    default_limits=["200 per day", "50 per hour"]
)

# Register webhook auth routes
register_webhook_auth_routes(app)

@app.route('/')
def index():
    """Main page - redirect to login"""
    return redirect(url_for('webhook_auth.webhook_login'))

@app.route('/dashboard')
def dashboard():
    """Protected dashboard"""
    if 'user' not in session:
        return redirect(url_for('webhook_auth.webhook_login'))
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - {Config.APP_NAME}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h3><i class="fas fa-shield-alt"></i> Secure Dashboard</h3>
                        </div>
                        <div class="card-body">
                            <h4>Welcome, {session['user']['email']}!</h4>
                            <p class="text-muted">You have successfully authenticated using webhook-based authentication.</p>
                            
                            <div class="alert alert-success">
                                <h5><i class="fas fa-check-circle"></i> Authentication Successful</h5>
                                <ul class="mb-0">
                                    <li><strong>Login Method:</strong> {session['user'].get('login_method', 'webhook')}</li>
                                    <li><strong>Login Time:</strong> {session['user'].get('login_time', 'Unknown')}</li>
                                    <li><strong>IP Address:</strong> {session['user'].get('ip_address', 'Unknown')}</li>
                                    <li><strong>MFA Verified:</strong> {session['user'].get('mfa_verified', False)}</li>
                                </ul>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="card">
                                        <div class="card-body">
                                            <h5><i class="fas fa-webhook"></i> Webhook Authentication</h5>
                                            <p>Your login was secured using webhook.site for code generation and verification.</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="card">
                                        <div class="card-body">
                                            <h5><i class="fas fa-shield-alt"></i> Security Features</h5>
                                            <ul class="mb-0">
                                                <li>End-to-end encryption</li>
                                                <li>Rate limiting protection</li>
                                                <li>IP address validation</li>
                                                <li>Session security</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mt-4">
                                <a href="/webhook-auth/webhook-dashboard" class="btn btn-info">
                                    <i class="fas fa-chart-line"></i> View Webhook Dashboard
                                </a>
                                <a href="/logout" class="btn btn-danger">
                                    <i class="fas fa-sign-out-alt"></i> Logout
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    return redirect(url_for('webhook_auth.webhook_login'))

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'webhook-auth-test',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🔐 WEBHOOK AUTHENTICATION SYSTEM - TEST SERVER")
    print("="*70)
    print("🌐 Web Interface: http://localhost:5000")
    print("🔗 Login Page: http://localhost:5000/login")
    print("📊 Webhook Dashboard: http://localhost:5000/webhook-auth/webhook-dashboard")
    print("🏠 Dashboard: http://localhost:5000/dashboard (after login)")
    print("="*70)
    print("Press Ctrl+C to stop the server")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)