#!/usr/bin/env python3
"""
Admin Setup Routes
One-time admin account creation with token validation
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from admin_setup import AdminSetupManager
import logging

logger = logging.getLogger(__name__)

admin_setup_bp = Blueprint('admin_setup', __name__, url_prefix='/admin')

# Initialize manager
setup_manager = AdminSetupManager()

@admin_setup_bp.route('/setup', methods=['GET'])
def setup_page():
    """Display admin setup page if token is valid"""
    token = request.args.get('token')
    
    if not token:
        return render_template('admin_setup_error.html', 
                             error="No setup token provided"), 400
    
    # Validate token
    valid, message = setup_manager.validate_token(token)
    
    if not valid:
        return render_template('admin_setup_error.html', 
                             error=message), 403
    
    # Check if admin already exists
    if setup_manager.admin_exists():
        return render_template('admin_setup_error.html',
                             error="Admin account already exists"), 403
    
    # Show setup form
    return render_template('admin_setup.html', token=token)

@admin_setup_bp.route('/setup', methods=['POST'])
def create_admin():
    """Create admin account"""
    token = request.form.get('token')
    username = request.form.get('username')
    password = request.form.get('password')
    password_confirm = request.form.get('password_confirm')
    
    # Validation
    if not all([token, username, password, password_confirm]):
        return jsonify({'error': 'All fields required'}), 400
    
    if password != password_confirm:
        return jsonify({'error': 'Passwords do not match'}), 400
    
    if len(password) < 12:
        return jsonify({'error': 'Password must be at least 12 characters'}), 400
    
    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400
    
    # Create admin account
    success, message = setup_manager.create_admin_account(token, username, password)
    
    if not success:
        return jsonify({'error': message}), 400
    
    # Mark token as used
    setup_manager.mark_token_used(token, request.remote_addr)
    
    logger.info(f"Admin account created: {username}")
    
    # Set session
    session['admin_username'] = username
    session['is_admin'] = True
    session['authenticated'] = True
    
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
