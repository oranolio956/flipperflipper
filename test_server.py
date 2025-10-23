#!/usr/bin/env python3
"""
Simple test server for E2E testing
"""

from flask import Flask, jsonify, request, render_template_string
import json
import time

app = Flask(__name__)
app.secret_key = 'test_secret_key_for_e2e_testing'

# Mock login page
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Oranolio RAT - Access</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a1a; color: white; text-align: center; padding: 50px; }
        .container { max-width: 400px; margin: 0 auto; background: #2a2a2a; padding: 30px; border-radius: 10px; }
        input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #555; background: #333; color: white; }
        button { width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .error { color: #ff6b6b; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ Oranolio</h1>
        <p>Command & Control Platform</p>
        <div id="error" class="error" style="display: none;"></div>
        <form id="loginForm">
            <input type="text" id="accessKey" placeholder="orat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" required>
            <button type="submit">Access Dashboard</button>
        </form>
    </div>
    <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const key = document.getElementById('accessKey').value;
            const error = document.getElementById('error');
            
            try {
                const response = await fetch('/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ access_key: key })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    window.location.href = '/dashboard';
                } else {
                    error.textContent = data.error || 'Login failed';
                    error.style.display = 'block';
                }
            } catch (err) {
                error.textContent = 'Network error';
                error.style.display = 'block';
            }
        });
    </script>
</body>
</html>
"""

# Mock dashboard page
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Dashboard - FlipperFlipper</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a1a; color: white; margin: 0; }
        .header { background: #2a2a2a; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-card { background: #2a2a2a; padding: 20px; border-radius: 10px; text-align: center; }
        .stat-value { font-size: 2em; font-weight: bold; color: #007bff; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔄 FlipperFlipper Dashboard</h1>
        <a href="/auth/logout" style="color: #ff6b6b;">Logout</a>
    </div>
    <div class="content">
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value" id="activeAgents">0</div>
                <div>Active Agents</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="totalPayloads">0</div>
                <div>Total Payloads</div>
            </div>
        </div>
        <div id="agents">
            <h3>Active Agents</h3>
            <div id="agentList">No agents connected</div>
        </div>
    </div>
    <script>
        // Load dashboard data
        async function loadDashboard() {
            try {
                const [statsResponse, agentsResponse] = await Promise.all([
                    fetch('/api/dashboard/stats'),
                    fetch('/api/dashboard/agents')
                ]);
                
                const stats = await statsResponse.json();
                const agents = await agentsResponse.json();
                
                document.getElementById('activeAgents').textContent = stats.active_agents || 0;
                document.getElementById('totalPayloads').textContent = stats.total_payloads || 0;
                
                const agentList = document.getElementById('agentList');
                if (agents.length === 0) {
                    agentList.textContent = 'No agents connected';
                } else {
                    agentList.innerHTML = agents.map(agent => 
                        `<div>${agent.hostname || 'Unknown'} - ${agent.status || 'offline'}</div>`
                    ).join('');
                }
            } catch (error) {
                console.error('Failed to load dashboard:', error);
            }
        }
        
        loadDashboard();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return 'Server is running for E2E testing'

@app.route('/auth/login')
def login_page():
    return render_template_string(LOGIN_HTML)

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    access_key = data.get('access_key', '')
    
    # Simple validation for testing
    if not access_key:
        return jsonify({'success': False, 'error': 'Access key required'}), 400
    
    if not access_key.startswith('orat_'):
        return jsonify({'success': False, 'error': 'Invalid access key format'}), 401
    
    # Mock successful login
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'redirect': '/dashboard'
    })

@app.route('/dashboard')
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/dashboard/stats')
def dashboard_stats():
    return jsonify({
        'active_agents': 0,
        'total_payloads': 0,
        'commands_executed_24h': 0,
        'data_transferred_24h_mb': 0
    })

@app.route('/api/dashboard/agents')
def dashboard_agents():
    return jsonify([])

@app.route('/api/dashboard/execute', methods=['POST'])
def execute_command():
    data = request.get_json()
    return jsonify({
        'message': f"Command '{data.get('command', '')}' queued for agent {data.get('agent_id', 'unknown')}"
    })

@app.route('/auth/logout', methods=['POST', 'GET'])
def logout():
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/invalid-endpoint')
def invalid_endpoint():
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    print('🚀 Starting test server on http://localhost:5000')
    app.run(host='0.0.0.0', port=5000, debug=False)