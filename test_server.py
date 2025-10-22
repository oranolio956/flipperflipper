#!/usr/bin/env python3
"""
Simple test server to preview the login pages
"""
from flask import Flask, render_template, request, flash, redirect, url_for
import os

app = Flask(__name__)
app.secret_key = 'test-secret-key-for-preview'

@app.route('/')
def login():
    return render_template('elite_email_login.html')

@app.route('/mfa-verify')
def mfa_verify():
    return render_template('mfa_verify.html')

@app.route('/mfa-setup')
def mfa_setup():
    # Mock data for testing
    qr_code = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2ZmZiIvPgogIDx0ZXh0IHg9IjEwMCIgeT0iMTAwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LWZhbWlseT0ibW9ub3NwYWNlIiBmb250LXNpemU9IjE0cHgiPk1GQSBRUiBDb2RlPC90ZXh0Pgo8L3N2Zz4K"
    secret = "JBSWY3DPEHPK3PXP"
    return render_template('mfa_setup.html', qr_code=qr_code, secret=secret)

@app.route('/login', methods=['POST'])
def handle_login():
    email = request.form.get('email')
    if email:
        flash('Verification code sent to your email', 'success')
        return redirect('/mfa-verify')
    else:
        flash('Please enter a valid email address', 'error')
        return redirect('/')

@app.route('/verify', methods=['POST'])
def handle_verify():
    token = request.form.get('token')
    if token and len(token) == 6:
        flash('Login successful!', 'success')
        return redirect('/')
    else:
        flash('Invalid verification code', 'error')
        return redirect('/mfa-verify')

if __name__ == '__main__':
    print("Starting test server...")
    print("Visit http://localhost:5000 to see the login page")
    print("Press Ctrl+C to stop the server")
    app.run(debug=True, host='0.0.0.0', port=5000)