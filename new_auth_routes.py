#!/usr/bin/env python3
"""
New Authentication Routes - Access Key Based
Clean, simple, secure authentication system
"""

import os
import sys
import logging
import secrets
import hmac
import hashlib
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, make_response
from functools import wraps

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from access_key_manager import access_key_manager, AuthErrorCode
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
new_auth_bp = Blueprint('new_auth', __name__, url_prefix='/auth')


def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_key_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('new_auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin permissions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_key_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        permissions = session.get('permissions', [])
        if 'admin' not in permissions:
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


@new_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login with access key"""
    if request.method == 'GET':
        # Check if already logged in
        if 'access_key_id' in session:
            return redirect(url_for('dashboard.index'))
        
        return render_template('new_login.html')
    
    # POST - Process login
    try:
        data = request.get_json() if request.is_json else request.form
        access_key = data.get('access_key', '').strip()
        
        if not access_key:
            return jsonify({
                'success': False,
                'error': 'Access key is required'
            }), 400
        
        # Get client info
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        
        # Authenticate
        result = access_key_manager.authenticate(access_key, ip_address, user_agent)
        
        if result.success:
            # Create session
            session.clear()
            session['access_key_id'] = result.key_id
            session['permissions'] = result.permissions
            session['authenticated_at'] = datetime.utcnow().isoformat()
            session['ip_address'] = ip_address
            session.permanent = True
            
            logger.info(f"Successful login from {ip_address} with key {result.key_id}")
            
            return jsonify({
                'success': True,
                'message': 'Authentication successful',
                'redirect': url_for('dashboard.index')
            })
        else:
            # Authentication failed
            logger.warning(f"Failed login from {ip_address}: {result.error_code.value}")
            
            return jsonify({
                'success': False,
                'error': result.error_message,
                'code': result.error_code.value
            }), 401
    
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'An error occurred during authentication'
        }), 500


@new_auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Handle logout"""
    key_id = session.get('access_key_id')
    if key_id:
        logger.info(f"User logged out: {key_id}")
    
    session.clear()
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    
    return redirect(url_for('new_auth.login'))


@new_auth_bp.route('/link', methods=['GET'])
def access_link():
    """Handle access link authentication"""
    token = request.args.get('token')
    
    if not token:
        return redirect(url_for('new_auth.login', error='Invalid access link'))
    
    try:
        # Verify and decode token
        result = verify_access_link_token(token)
        
        if result['valid']:
            # Create session
            session.clear()
            session['access_key_id'] = result['key_id']
            session['permissions'] = result['permissions']
            session['authenticated_at'] = datetime.utcnow().isoformat()
            session['ip_address'] = request.remote_addr
            session['auth_method'] = 'access_link'
            session.permanent = True
            
            logger.info(f"Access link used from {request.remote_addr}")
            
            return redirect(url_for('dashboard.index'))
        else:
            return redirect(url_for('new_auth.login', error=result['error']))
    
    except Exception as e:
        logger.error(f"Access link error: {e}", exc_info=True)
        return redirect(url_for('new_auth.login', error='Invalid or expired access link'))


@new_auth_bp.route('/admin/keys', methods=['GET', 'POST', 'DELETE'])
@admin_required
def manage_keys():
    """Manage access keys (admin only)"""
    if request.method == 'GET':
        # List all keys
        keys = access_key_manager.list_keys()
        
        keys_data = []
        for key in keys:
            keys_data.append({
                'id': key.id,
                'name': key.name,
                'created_by': key.created_by,
                'created_at': datetime.fromtimestamp(key.created_at).isoformat(),
                'last_used_at': datetime.fromtimestamp(key.last_used_at).isoformat() if key.last_used_at else None,
                'expires_at': datetime.fromtimestamp(key.expires_at).isoformat() if key.expires_at else None,
                'is_active': key.is_active,
                'usage_count': key.usage_count,
                'max_uses': key.max_uses,
                'permissions': key.permissions
            })
        
        if request.is_json:
            return jsonify({'keys': keys_data})
        
        return render_template('admin_keys.html', keys=keys_data)
    
    elif request.method == 'POST':
        # Create new key
        try:
            data = request.get_json()
            
            name = data.get('name')
            if not name:
                return jsonify({'error': 'Name is required'}), 400
            
            expires_in_days = data.get('expires_in_days')
            max_uses = data.get('max_uses')
            ip_whitelist = data.get('ip_whitelist')
            permissions = data.get('permissions', ['read', 'write'])
            
            created_by = session.get('access_key_id', 'admin')
            
            key_id, plaintext_key = access_key_manager.generate_access_key(
                name=name,
                created_by=created_by,
                expires_in_days=expires_in_days,
                max_uses=max_uses,
                ip_whitelist=ip_whitelist,
                permissions=permissions
            )
            
            logger.info(f"Access key created: {key_id} by {created_by}")
            
            return jsonify({
                'success': True,
                'key_id': key_id,
                'access_key': plaintext_key,
                'message': 'Access key created successfully. Save this key - it won\'t be shown again.'
            })
        
        except Exception as e:
            logger.error(f"Key creation error: {e}", exc_info=True)
            return jsonify({'error': 'Failed to create access key'}), 500
    
    elif request.method == 'DELETE':
        # Revoke key
        try:
            data = request.get_json()
            key_id = data.get('key_id')
            
            if not key_id:
                return jsonify({'error': 'Key ID is required'}), 400
            
            success = access_key_manager.revoke_key(key_id)
            
            if success:
                logger.info(f"Access key revoked: {key_id}")
                return jsonify({'success': True, 'message': 'Access key revoked'})
            else:
                return jsonify({'error': 'Key not found'}), 404
        
        except Exception as e:
            logger.error(f"Key revocation error: {e}", exc_info=True)
            return jsonify({'error': 'Failed to revoke access key'}), 500


@new_auth_bp.route('/admin/links', methods=['POST'])
@admin_required
def generate_link():
    """Generate access link (admin only)"""
    try:
        data = request.get_json()
        
        access_key_id = data.get('access_key_id')
        if not access_key_id:
            return jsonify({'error': 'Access key ID is required'}), 400
        
        expires_in_hours = data.get('expires_in_hours', 24)
        max_uses = data.get('max_uses', 1)
        
        # Generate link
        link, token = generate_access_link(
            access_key_id,
            expires_in_hours,
            max_uses
        )
        
        logger.info(f"Access link generated for key {access_key_id}")
        
        return jsonify({
            'success': True,
            'link': link,
            'expires_at': (datetime.utcnow() + timedelta(hours=expires_in_hours)).isoformat(),
            'max_uses': max_uses
        })
    
    except Exception as e:
        logger.error(f"Link generation error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to generate access link'}), 500


@new_auth_bp.route('/status', methods=['GET'])
@login_required
def status():
    """Get authentication status"""
    return jsonify({
        'authenticated': True,
        'key_id': session.get('access_key_id'),
        'permissions': session.get('permissions', []),
        'authenticated_at': session.get('authenticated_at'),
        'auth_method': session.get('auth_method', 'access_key')
    })


def generate_access_link(
    access_key_id: str,
    expires_in_hours: int = 24,
    max_uses: int = 1
) -> tuple:
    """Generate a signed access link"""
    # Create payload
    payload = {
        'key_id': access_key_id,
        'exp': int((datetime.utcnow() + timedelta(hours=expires_in_hours)).timestamp()),
        'nonce': secrets.token_urlsafe(16),
        'max_uses': max_uses
    }
    
    # Sign payload
    payload_json = json.dumps(payload, sort_keys=True)
    signature = hmac.new(
        Config.SECRET_KEY.encode(),
        payload_json.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Create token
    token = f"{payload_json.encode().hex()}.{signature}"
    
    # Create URL
    base_url = request.url_root.rstrip('/')
    link = f"{base_url}/auth/link?token={token}"
    
    return link, token


def verify_access_link_token(token: str) -> dict:
    """Verify and decode access link token"""
    try:
        # Split token
        parts = token.split('.')
        if len(parts) != 2:
            return {'valid': False, 'error': 'Invalid token format'}
        
        payload_hex, signature = parts
        
        # Decode payload
        payload_json = bytes.fromhex(payload_hex).decode()
        payload = json.loads(payload_json)
        
        # Verify signature
        expected_signature = hmac.new(
            Config.SECRET_KEY.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return {'valid': False, 'error': 'Invalid signature'}
        
        # Check expiration
        if payload['exp'] < datetime.utcnow().timestamp():
            return {'valid': False, 'error': 'Link has expired'}
        
        # Get key details
        # TODO: Implement link usage tracking
        
        return {
            'valid': True,
            'key_id': payload['key_id'],
            'permissions': ['read', 'write']  # Get from key
        }
    
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return {'valid': False, 'error': 'Invalid token'}


if __name__ == "__main__":
    print("New Authentication Routes")
    print("=" * 60)
    print("Routes registered:")
    print("  GET  /auth/login - Login page")
    print("  POST /auth/login - Process login")
    print("  GET  /auth/logout - Logout")
    print("  GET  /auth/link - Access link handler")
    print("  GET  /auth/admin/keys - List keys (admin)")
    print("  POST /auth/admin/keys - Create key (admin)")
    print("  DELETE /auth/admin/keys - Revoke key (admin)")
    print("  POST /auth/admin/links - Generate link (admin)")
    print("  GET  /auth/status - Auth status")
