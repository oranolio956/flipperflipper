#!/usr/bin/env python3
"""
Simple 2FA Test Server
Tests the complete 2FA flow with authenticator apps
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
import pyotp
import qrcode
import io
import base64
import json
import time
from datetime import datetime
from simple_config import Config
from mfa_manager import mfa_manager
from mfa_database import save_user_mfa, get_user_mfa_status, get_user_mfa_config, update_user_backup_codes, log_mfa_event
from automated_email_service import automated_email_service

app = Flask(__name__)
app.secret_key = 'test-secret-key'

# Store verification codes in memory for testing
verification_codes = {}

@app.route('/')
def index():
    """Main page"""
    return """
    <h1>🔐 2FA Test System</h1>
    <p>This system tests the complete 2FA flow with authenticator apps.</p>
    <a href="/login">Login</a> | 
    <a href="/mfa/setup">Setup MFA</a> | 
    <a href="/mfa/verify">Verify MFA</a>
    """

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if email:
            # Generate verification code
            code = '123456'  # For testing
            verification_codes[email] = code
            
            # Send via automated email service
            automated_email_service.send_verification_email(email, code, '127.0.0.1')
            
            session['verify_email'] = email
            return redirect(url_for('verify_email'))
    
    return '''
    <h2>🔐 Login</h2>
    <form method="post">
        <input type="email" name="email" placeholder="Enter email" required>
        <button type="submit">Send Code</button>
    </form>
    '''

@app.route('/verify', methods=['GET', 'POST'])
def verify_email():
    """Email verification"""
    if 'verify_email' not in session:
        return redirect(url_for('login'))
    
    email = session['verify_email']
    
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        if code == verification_codes.get(email):
            # Check MFA status
            mfa_status = get_user_mfa_status(email)
            
            if not mfa_status['enabled']:
                session['mfa_setup_email'] = email
                return redirect(url_for('mfa_setup'))
            else:
                session['mfa_verify_email'] = email
                return redirect(url_for('mfa_verify'))
        else:
            flash('Invalid code')
    
    return f'''
    <h2>📧 Verify Email</h2>
    <p>Enter the code sent to {email}</p>
    <p>Test code: {verification_codes.get(email, 'N/A')}</p>
    <form method="post">
        <input type="text" name="code" placeholder="Enter code" required>
        <button type="submit">Verify</button>
    </form>
    '''

@app.route('/mfa/setup', methods=['GET', 'POST'])
def mfa_setup():
    """MFA setup page"""
    if 'mfa_setup_email' not in session:
        return redirect(url_for('login'))
    
    email = session['mfa_setup_email']
    
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        secret = session.get('mfa_setup_secret')
        
        if secret and token and mfa_manager.verify_token(secret, token):
            # Generate backup codes
            backup_codes = mfa_manager.generate_backup_codes(10)
            backup_codes_hashed = [mfa_manager.hash_backup_code(c) for c in backup_codes]
            
            # Save MFA configuration
            encrypted_secret = mfa_manager.encrypt_secret(secret)
            save_user_mfa(email, encrypted_secret, json.dumps(backup_codes_hashed))
            
            session['backup_codes'] = backup_codes
            session.pop('mfa_setup_email', None)
            session.pop('mfa_setup_secret', None)
            
            flash('MFA setup successful!')
            return redirect(url_for('mfa_backup_codes'))
        else:
            flash('Invalid verification code')
    
    # Generate new secret for setup
    if 'mfa_setup_secret' not in session:
        secret = mfa_manager.generate_secret()
        session['mfa_setup_secret'] = secret
    else:
        secret = session['mfa_setup_secret']
    
    # Generate QR code
    provisioning_uri = mfa_manager.get_provisioning_uri(email, secret)
    qr_code_data = mfa_manager.generate_qr_code(provisioning_uri)
    
    return f'''
    <h2>🔐 Setup 2FA</h2>
    <p>Scan this QR code with your authenticator app:</p>
    <img src="{qr_code_data}" alt="QR Code">
    <p>Or enter this secret manually: <code>{secret}</code></p>
    <p>Then enter the 6-digit code from your app:</p>
    <form method="post">
        <input type="text" name="token" placeholder="Enter 6-digit code" maxlength="6" required>
        <button type="submit">Verify & Setup</button>
    </form>
    '''

@app.route('/mfa/backup-codes')
def mfa_backup_codes():
    """Display backup codes"""
    backup_codes = session.get('backup_codes')
    if not backup_codes:
        return redirect(url_for('login'))
    
    # Clear from session
    session.pop('backup_codes', None)
    
    codes_html = '<br>'.join([f'{i+1}. {code}' for i, code in enumerate(backup_codes)])
    
    return f'''
    <h2>🔑 Backup Codes</h2>
    <p>Save these backup codes in a safe place. Each can only be used once:</p>
    <div style="font-family: monospace; background: #f5f5f5; padding: 10px;">
        {codes_html}
    </div>
    <p><a href="/mfa/verify">Continue to MFA Verification</a></p>
    '''

@app.route('/mfa/verify', methods=['GET', 'POST'])
def mfa_verify():
    """MFA verification page"""
    if 'mfa_verify_email' not in session:
        return redirect(url_for('login'))
    
    email = session['mfa_verify_email']
    
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        use_backup = request.form.get('use_backup') == 'on'
        
        if not token:
            flash('Verification code required')
            return redirect(url_for('mfa_verify'))
        
        # Get user's MFA configuration
        mfa_config = get_user_mfa_config(email)
        
        if not mfa_config:
            flash('MFA not configured for this account')
            return redirect(url_for('login'))
        
        if use_backup:
            # Verify backup code
            is_valid, new_backup_codes = mfa_manager.verify_backup_code(
                token, mfa_config['backup_codes']
            )
            
            if is_valid:
                update_user_backup_codes(email, new_backup_codes)
                session.pop('mfa_verify_email', None)
                flash('Login successful with backup code!')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid backup code')
        else:
            # Verify TOTP token
            encrypted_secret = mfa_config['mfa_secret']
            secret = mfa_manager.decrypt_secret(encrypted_secret)
            
            if mfa_manager.verify_token(secret, token):
                session.pop('mfa_verify_email', None)
                flash('Login successful!')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid verification code')
    
    return '''
    <h2>🔐 Verify 2FA</h2>
    <p>Enter the 6-digit code from your authenticator app:</p>
    <form method="post">
        <input type="text" name="token" placeholder="Enter 6-digit code" maxlength="6" required>
        <button type="submit">Verify</button>
    </form>
    <hr>
    <p>Lost your device? Use a backup code:</p>
    <form method="post">
        <input type="text" name="token" placeholder="Enter backup code" required>
        <input type="checkbox" name="use_backup" id="use_backup">
        <label for="use_backup">This is a backup code</label>
        <button type="submit">Verify Backup Code</button>
    </form>
    '''

@app.route('/dashboard')
def dashboard():
    """Dashboard after successful login"""
    return '''
    <h1>🎉 Dashboard</h1>
    <p>Congratulations! You have successfully completed the 2FA flow.</p>
    <h3>✅ What was tested:</h3>
    <ul>
        <li>Email verification with automated service</li>
        <li>QR code generation for authenticator apps</li>
        <li>TOTP token verification</li>
        <li>Backup codes generation and verification</li>
        <li>Complete secure login flow</li>
    </ul>
    <h3>📱 Compatible Apps:</h3>
    <ul>
        <li>Google Authenticator</li>
        <li>Microsoft Authenticator</li>
        <li>Authy</li>
        <li>1Password</li>
        <li>Bitwarden</li>
        <li>LastPass Authenticator</li>
    </ul>
    <p><a href="/">Start Over</a></p>
    '''

if __name__ == '__main__':
    print("🚀 Starting 2FA Test Server...")
    print("📱 Open: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)