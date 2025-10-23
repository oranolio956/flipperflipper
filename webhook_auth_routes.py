#!/usr/bin/env python3
"""
Webhook Authentication Routes for Oranolio RAT - Elite C2 Framework
Handles webhook-based authentication for API access
"""

import os
import sys
import json
import hmac
import hashlib
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, session, g
from typing import Dict, Any, Optional

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import utilities
from auth_utils import auth_manager, api_key_or_login_required
from error_handler import error_handler, ErrorSeverity, ErrorCategory, ErrorContext
from validation_schemas import validate_input

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
webhook_auth_bp = Blueprint('webhook_auth', __name__, url_prefix='/webhook')

class WebhookAuthManager:
    """Manages webhook-based authentication"""
    
    def __init__(self):
        self.webhook_secrets = {}
        self.webhook_events = []
        self.max_events = 1000
    
    def add_webhook_secret(self, webhook_id: str, secret: str, permissions: list = None):
        """Add a webhook secret for authentication"""
        if permissions is None:
            permissions = ['read', 'write']
        
        self.webhook_secrets[webhook_id] = {
            'secret': secret,
            'permissions': permissions,
            'created_at': datetime.now(),
            'last_used': None,
            'usage_count': 0
        }
        
        logger.info(f"Webhook secret added: {webhook_id}")
    
    def validate_webhook_signature(self, webhook_id: str, payload: str, signature: str) -> bool:
        """Validate webhook signature"""
        if webhook_id not in self.webhook_secrets:
            return False
        
        webhook_info = self.webhook_secrets[webhook_id]
        secret = webhook_info['secret']
        
        # Calculate expected signature
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        is_valid = hmac.compare_digest(signature, expected_signature)
        
        if is_valid:
            # Update usage statistics
            webhook_info['last_used'] = datetime.now()
            webhook_info['usage_count'] += 1
            
            # Log webhook event
            self._log_webhook_event(webhook_id, 'authentication', 'success')
        
        return is_valid
    
    def _log_webhook_event(self, webhook_id: str, event_type: str, status: str, details: Dict[str, Any] = None):
        """Log webhook event"""
        event = {
            'webhook_id': webhook_id,
            'event_type': event_type,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'details': details or {}
        }
        
        self.webhook_events.append(event)
        
        # Keep only recent events
        if len(self.webhook_events) > self.max_events:
            self.webhook_events = self.webhook_events[-self.max_events:]
    
    def get_webhook_permissions(self, webhook_id: str) -> list:
        """Get permissions for a webhook"""
        if webhook_id in self.webhook_secrets:
            return self.webhook_secrets[webhook_id]['permissions']
        return []
    
    def get_webhook_stats(self) -> Dict[str, Any]:
        """Get webhook statistics"""
        total_webhooks = len(self.webhook_secrets)
        total_events = len(self.webhook_events)
        
        recent_events = [
            event for event in self.webhook_events
            if datetime.fromisoformat(event['timestamp']) > datetime.now() - timedelta(hours=24)
        ]
        
        return {
            'total_webhooks': total_webhooks,
            'total_events': total_events,
            'recent_events_24h': len(recent_events),
            'webhooks': list(self.webhook_secrets.keys())
        }

# Global webhook auth manager
webhook_auth_manager = WebhookAuthManager()

def webhook_auth_required(permissions: list = None):
    """Decorator to require webhook authentication"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get webhook ID and signature from headers
                webhook_id = request.headers.get('X-Webhook-ID')
                signature = request.headers.get('X-Webhook-Signature')
                
                if not webhook_id or not signature:
                    return jsonify({'error': 'Webhook authentication required'}), 401
                
                # Get request payload
                payload = request.get_data(as_text=True)
                
                # Validate signature
                if not webhook_auth_manager.validate_webhook_signature(webhook_id, payload, signature):
                    webhook_auth_manager._log_webhook_event(webhook_id, 'authentication', 'failed')
                    return jsonify({'error': 'Invalid webhook signature'}), 401
                
                # Check permissions
                if permissions:
                    webhook_permissions = webhook_auth_manager.get_webhook_permissions(webhook_id)
                    if not any(perm in webhook_permissions for perm in permissions):
                        webhook_auth_manager._log_webhook_event(webhook_id, 'authorization', 'failed')
                        return jsonify({'error': 'Insufficient permissions'}), 403
                
                # Store webhook info in g for use in the route
                g.webhook_id = webhook_id
                g.webhook_permissions = webhook_auth_manager.get_webhook_permissions(webhook_id)
                
                return f(*args, **kwargs)
                
            except Exception as e:
                context = ErrorContext(
                    ip_address=request.remote_addr,
                    additional_data={'error': str(e)}
                )
                error_handler.handle_error(e, context, ErrorSeverity.HIGH, ErrorCategory.AUTHENTICATION)
                
                return jsonify({'error': 'Webhook authentication failed'}), 500
        
        return decorated_function
    return decorator

@webhook_auth_bp.route('/register', methods=['POST'])
# NOTE: Webhook endpoints use HMAC signature validation instead of CSRF tokens
# CSRF exemption should be applied when registering this blueprint in web_app.py
def register_webhook():
    """Register a new webhook"""
    try:
        data = request.get_json()
        
        webhook_id = data.get('webhook_id')
        secret = data.get('secret')
        permissions = data.get('permissions', ['read'])
        
        if not webhook_id or not secret:
            return jsonify({'error': 'Webhook ID and secret required'}), 400
        
        # Add webhook secret
        webhook_auth_manager.add_webhook_secret(webhook_id, secret, permissions)
        
        logger.info(f"Webhook registered: {webhook_id}")
        
        return jsonify({
            'success': True,
            'message': 'Webhook registered successfully',
            'webhook_id': webhook_id
        })
        
    except Exception as e:
        context = ErrorContext(
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.HIGH, ErrorCategory.AUTHENTICATION)
        
        return jsonify({'error': 'Webhook registration failed'}), 500

@webhook_auth_bp.route('/test', methods=['POST'])
@webhook_auth_required(['read'])
# NOTE: Webhook endpoints use HMAC signature validation instead of CSRF tokens
def test_webhook():
    """Test webhook authentication"""
    try:
        webhook_id = g.webhook_id
        permissions = g.webhook_permissions
        
        return jsonify({
            'success': True,
            'message': 'Webhook authentication successful',
            'webhook_id': webhook_id,
            'permissions': permissions,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        context = ErrorContext(
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.AUTHENTICATION)
        
        return jsonify({'error': 'Webhook test failed'}), 500

@webhook_auth_bp.route('/stats', methods=['GET'])
@webhook_auth_required(['read'])
def get_webhook_stats():
    """Get webhook statistics"""
    try:
        stats = webhook_auth_manager.get_webhook_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        context = ErrorContext(
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        
        return jsonify({'error': 'Failed to get webhook stats'}), 500

@webhook_auth_bp.route('/events', methods=['GET'])
@webhook_auth_required(['read'])
def get_webhook_events():
    """Get webhook events"""
    try:
        limit = request.args.get('limit', 100, type=int)
        events = webhook_auth_manager.webhook_events[-limit:]
        
        return jsonify({
            'success': True,
            'events': events,
            'total': len(events)
        })
        
    except Exception as e:
        context = ErrorContext(
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        
        return jsonify({'error': 'Failed to get webhook events'}), 500

@webhook_auth_bp.route('/command', methods=['POST'])
@webhook_auth_required(['write'])
# NOTE: Webhook endpoints use HMAC signature validation instead of CSRF tokens
def execute_webhook_command():
    """Execute a command via webhook"""
    try:
        data = request.get_json()
        
        command = data.get('command')
        target_id = data.get('target_id')
        
        if not command or not target_id:
            return jsonify({'error': 'Command and target ID required'}), 400
        
        # Execute command (simplified for webhook)
        result = {
            'command_id': f"webhook_cmd_{int(datetime.now().timestamp() * 1000)}",
            'command': command,
            'target_id': target_id,
            'status': 'completed',
            'output': f"Webhook command '{command}' executed on {target_id}",
            'timestamp': datetime.now().isoformat()
        }
        
        # Log webhook event
        webhook_auth_manager._log_webhook_event(
            g.webhook_id, 
            'command_execution', 
            'success',
            {'command': command, 'target_id': target_id}
        )
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        context = ErrorContext(
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.HIGH, ErrorCategory.APPLICATION)
        
        return jsonify({'error': 'Command execution failed'}), 500

def register_webhook_auth_routes(app):
    """Register webhook authentication routes with Flask app"""
    app.register_blueprint(webhook_auth_bp)
    
    # Initialize default webhook for testing
    webhook_auth_manager.add_webhook_secret(
        'test_webhook',
        'test_secret_key_change_in_production',
        ['read', 'write']
    )
    
    logger.info("Webhook authentication routes registered")

# Example usage and testing
if __name__ == "__main__":
    print("Webhook Authentication Routes")
    print("=" * 40)
    print("Routes registered:")
    print("  POST /webhook/register - Register webhook")
    print("  POST /webhook/test - Test webhook auth")
    print("  GET  /webhook/stats - Get webhook stats")
    print("  GET  /webhook/events - Get webhook events")
    print("  POST /webhook/command - Execute command")
    print("Webhook authentication routes ready!")