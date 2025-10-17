#!/usr/bin/env python3
"""
Virtual Meeting Platform - Server Component
Professional video conferencing solution with collaboration tools
"""

import os
import sys
from flask import Flask, render_template, jsonify

# Add application path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'application'))

app = Flask(__name__)

# Import meeting platform components
try:
    from conference_manager import *
    MEETING_CORE_AVAILABLE = True
except ImportError:
    MEETING_CORE_AVAILABLE = False

@app.route('/')
def home():
    """Meeting platform homepage"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Virtual Meeting Platform</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }
            .header { background: #2d8cff; color: white; padding: 40px 20px; text-align: center; }
            .content { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
            .feature { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .btn { background: #2d8cff; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎥 Virtual Meeting Platform</h1>
            <p>Professional Video Conferencing Solution</p>
        </div>
        <div class="content">
            <div class="feature">
                <h3>📹 HD Video Conferencing</h3>
                <p>Crystal clear video calls with advanced collaboration features.</p>
            </div>
            <div class="feature">
                <h3>🖥️ Screen Sharing</h3>
                <p>Share presentations and collaborate in real-time with team members.</p>
            </div>
            <div class="feature">
                <h3>🔒 Enterprise Security</h3>
                <p>End-to-end encryption and enterprise-grade security features.</p>
            </div>
            <div style="text-align: center; margin-top: 40px;">
                <button class="btn" onclick="alert('Meeting platform is ready for deployment!')">Start Meeting</button>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/api/status')
def status():
    """API endpoint for platform status"""
    return jsonify({
        "status": "online",
        "platform": "Virtual Meeting Platform",
        "version": "1.0.0",
        "features": ["video_conferencing", "screen_sharing", "collaboration"],
        "core_available": MEETING_CORE_AVAILABLE
    })

@app.route('/admin')
def admin_panel():
    """Administrative panel for meeting management"""
    if MEETING_CORE_AVAILABLE:
        return '''
        <h1>🎥 Meeting Platform Administration</h1>
        <p>Core meeting services are running.</p>
        <ul>
            <li><a href="/api/status">Platform Status</a></li>
            <li><a href="/">Main Interface</a></li>
        </ul>
        '''
    else:
        return '<h1>Meeting Platform</h1><p>Core services loading...</p>'

def start_meeting_core():
    """Start the core meeting platform services"""
    if MEETING_CORE_AVAILABLE:
        try:
            # Start the conference management system in background
            import threading
            core_thread = threading.Thread(target=conference_main)
            core_thread.daemon = True
            core_thread.start()
            print("✅ Meeting platform core services started")
        except Exception as e:
            print(f"⚠️  Core services startup warning: {e}")

if __name__ == "__main__":
    # Start meeting platform core
    start_meeting_core()
    
    # Start web interface
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Virtual Meeting Platform starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
