#!/usr/bin/env python3
"""
Complete Dashboard Routes for Oranolio C2 - Use this to replace dashboard_routes.py
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, session, send_file
from werkzeug.utils import secure_filename

sys.path.insert(0, os.path.dirname(__file__))
from auth_utils import login_required

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'py', 'exe', 'zip', 'rar', 'dll', 'bat', 'ps1'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Pages
@dashboard_bp.route('/')
@dashboard_bp.route('/overview')
@login_required
def overview():
    return render_template('dashboard/overview.html')

@dashboard_bp.route('/targets')
@login_required
def targets():
    return render_template('dashboard/targets.html')

@dashboard_bp.route('/commands')
@login_required
def commands():
    return render_template('dashboard/commands.html')

@dashboard_bp.route('/files')
@login_required
def files():
    return render_template('dashboard/files.html')

@dashboard_bp.route('/credentials')
@login_required
def credentials():
    return render_template('dashboard/credentials.html')

@dashboard_bp.route('/keylogs')
@login_required
def keylogs():
    return render_template('dashboard/keylogs.html')

@dashboard_bp.route('/logs')
@login_required
def logs():
    return render_template('dashboard/logs.html')

@dashboard_bp.route('/settings')
@login_required
def settings():
    return render_template('dashboard/settings.html')

@dashboard_bp.route('/help')
@login_required
def help():
    return render_template('dashboard/help.html')

# API Endpoints (Mock data - integrate with your backend)
@dashboard_bp.route('/api/dashboard/overview')
@login_required
def api_overview():
    return jsonify({
        'stats': {'active_targets': 2, 'commands_today': 15, 'total_credentials': 8, 'success_rate': 95},
        'recent_activity': [],
        'active_targets': []
    })

@dashboard_bp.route('/api/targets')
@login_required
def api_targets():
    return jsonify({'targets': []})

@dashboard_bp.route('/api/commands')
@login_required
def api_commands():
    return jsonify({'system': [], 'file': [], 'network': [], 'security': []})

@dashboard_bp.route('/api/files')
@login_required
def api_files():
    return jsonify({'uploaded': [], 'downloaded': []})

@dashboard_bp.route('/api/credentials')
@login_required
def api_credentials():
    return jsonify({'credentials': []})

@dashboard_bp.route('/api/keylogs')
@login_required
def api_keylogs():
    return jsonify({'keylogs': []})

@dashboard_bp.route('/api/logs')
@login_required
def api_logs():
    return jsonify({'logs': []})

__all__ = ['dashboard_bp']
