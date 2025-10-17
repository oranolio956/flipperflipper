# Terminal CLI to Web Interface - Complete Command Mapping

## Overview

This document provides a comprehensive mapping between Stitch CLI terminal commands and their Web Interface equivalents. The web interface achieves **100% feature parity** with the CLI while adding enhanced safety, usability, and monitoring features.

---

## Core Architecture Mapping

| CLI Component | Web Equivalent | Enhancement |
|---------------|----------------|-------------|
| `python main.py` | `python web_app_real.py` | Includes CLI + Web server |
| Terminal prompt | Web dashboard | Visual interface with real-time updates |
| Command input | 8 categorized command sections | Organized by function with tooltips |
| Direct execution | Confirmation dialogs | Safety for 25+ dangerous commands |
| Manual connection switching | Click-to-select connections | Visual connection cards with status |
| Text-based output | Formatted output with timestamps | Copy-to-clipboard, export options |

---

## Command Categories Mapping

### 1. System Information Commands

| CLI Command | Web Interface | Location | Notes |
|-------------|---------------|----------|-------|
| `sysinfo` | **System Info** button | Commands → System Info | Same output, formatted display |
| `environment` | **Environment** button | Commands → System Info | Shows environment variables |
| `ps` | **Processes** button | Commands → System Info | Process list |
| `lsmod` | **List Modules** button | Commands → System Info | Drivers/kernel modules |
| `drives` | **Drives** button | Commands → System Info | Windows drive information |
| `location` | **Location** button | Commands → System Info | IP geolocation |
| `vmscan` | **VM Scan** button | Commands → System Info | Virtual machine detection |
| `pwd` | **Working Dir** button | Commands → System Info | Current directory |
| `ls` / `dir` | **List Files** / **Dir (Win)** | Commands → System Info | Directory contents |

### 2. File Operations

| CLI Command | Web Interface | Location | Enhancement |
|-------------|---------------|----------|-------------|
| `upload <file>` | **Drag & Drop Upload** | Files tab | Visual progress bar, 100MB limit |
| `download <file>` | **Download** button | Commands → Files | Parameter prompt |
| `cat <file>` | **View File (cat)** button | Commands → Files | Parameter prompt |
| `cd <path>` | **Change Dir** button | Commands → Files | Parameter prompt |
| `rm <file>` | Shell command via custom input | Commands → Custom | No dedicated button |
| `mkdir <dir>` | Shell command via custom input | Commands → Custom | No dedicated button |
| `hide <path>` | **Hide** button | Commands → Files | Parameter prompt + confirmation |
| `unhide <path>` | **Unhide** button | Commands → Files | Parameter prompt + confirmation |

### 3. Network Operations

| CLI Command | Web Interface | Location | Enhancement |
|-------------|---------------|----------|-------------|
| `ipconfig` | **IP Config** button | Commands → Network | Direct execution |
| `ifconfig` | **ifconfig** button | Commands → Admin | Linux equivalent |
| `netstat` | **Netstat** button | Commands → Admin | Parameter prompt |
| `firewall status` | **Firewall Status** button | Commands → Network | Direct execution |
| `firewall open` | **Firewall Open** button | Commands → Network | Interactive parameter form |
| `firewall close` | **Firewall Close** button | Commands → Network | Interactive parameter form + confirmation |
| `hostsfile show` | **Show Hosts** button | Commands → Network | Direct execution |
| `hostsfile update` | **Update Hosts** button | Commands → Network | Interactive form + confirmation |
| `hostsfile remove` | **Remove Hosts** button | Commands → Network | Interactive form + confirmation |
| `ssh` | **SSH** button | Commands → Network | Interactive prompts |

### 4. Security & Credential Operations

| CLI Command | Web Interface | Location | Safety Enhancement |
|-------------|---------------|----------|-------------------|
| `hashdump` | **Hash Dump** button | Commands → Control & Exploit | ⚠️ Dangerous - requires confirmation |
| `keylogger start` | **Keylog Start** button | Commands → Control & Exploit | ⚠️ Dangerous - requires confirmation |
| `keylogger stop` | **Keylog Stop** button | Commands → Control & Exploit | Direct execution |
| `keylogger dump` | **Keylog Dump** button | Commands → Control & Exploit | Direct execution |
| `keylogger status` | **Keylog Status** button | Commands → Control & Exploit | Direct execution |
| `screenshot` | **Screenshot** button | Commands → Control & Exploit | Direct execution |
| `webcamlist` | **Webcam List** button | Commands → Control & Exploit | Direct execution |
| `webcamsnap` | **Webcam Snap** button | Commands → Control & Exploit | Parameter prompt |
| `wifikeys` | **WiFi Keys** button | Commands → Control & Exploit | ⚠️ Dangerous - requires confirmation |
| `chromedump` | **Chrome Dump** button | Commands → Windows | ⚠️ Dangerous - requires confirmation |

### 5. Windows-Specific Commands

| CLI Command | Web Interface | Location | Safety Enhancement |
|-------------|---------------|----------|-------------------|
| `clearev` | **Clear Events** button | Commands → Windows | ⚠️ Dangerous - requires confirmation |
| `avkill` | **AV Kill** button | Commands → Control & Exploit | ⚠️ Dangerous - requires confirmation |
| `avscan` | **AV Scan** button | Commands → Control & Exploit | Direct execution |
| `disableRDP` | **Disable RDP** button | Commands → Windows | ⚠️ Dangerous - requires confirmation |
| `enableRDP` | **Enable RDP** button | Commands → Windows | Direct execution |
| `disableUAC` | **Disable UAC** button | Commands → Windows | ⚠️ Dangerous - requires confirmation |
| `enableUAC` | **Enable UAC** button | Commands → Windows | Direct execution |
| `disableWindef` | **Disable Defender** button | Commands → Windows | ⚠️ Dangerous - requires confirmation |
| `enableWindef` | **Enable Defender** button | Commands → Windows | Direct execution |
| `scanreg` | **Scan Registry** button | Commands → Windows | Direct execution |

### 6. System Control Commands

| CLI Command | Web Interface | Location | Safety Enhancement |
|-------------|---------------|----------|-------------------|
| `freeze start` | **Freeze Start** button | Commands → Control & Exploit | ⚠️ Dangerous - requires confirmation |
| `freeze stop` | **Freeze Stop** button | Commands → Control & Exploit | Direct execution |
| `freeze status` | **Freeze Status** button | Commands → Control & Exploit | Direct execution |
| `lockscreen` | **Lock Screen** button | Commands → Control & Exploit | ⚠️ Dangerous - requires confirmation |
| `displayoff` | **Display Off** button | Commands → Control & Exploit | ⚠️ Dangerous - requires confirmation |
| `displayon` | **Display On** button | Commands → Control & Exploit | Direct execution |
| `popup` | **Popup** button | Commands → Control & Exploit | Interactive form + confirmation |

### 7. macOS/Linux Specific Commands

| CLI Command | Web Interface | Location | Enhancement |
|-------------|---------------|----------|-------------|
| `askpassword` | **Ask Password** button | Commands → macOS/Linux | ⚠️ Requires confirmation |
| `crackpassword` | **Crack Password** button | Commands → macOS/Linux | Direct execution |
| `logintext` | **Login Text** button | Commands → Control & Exploit | Interactive form + confirmation |
| `sudo <cmd>` | **Sudo** button | Commands → Admin | Parameter prompt |
| `ssh` | **SSH** button | Commands → Network | Interactive prompts |

### 8. Administrative Commands

| CLI Command | Web Interface | Location | Enhancement |
|-------------|---------------|----------|-------------|
| `sessions` | **Sessions** button | Commands → Admin | Server-only command |
| `history` | **History** button | Commands → Admin | Server-only command |
| `showkey` | **Show Key** button | Commands → Admin | Server-only command |
| `addkey` | **Add Key** button | Commands → Admin | Parameter prompt |
| `clear` / `cls` | **Clear Screen** button | Commands → Admin | UI-specific message |
| `home` | **Home** button | Commands → Admin | Shows banner |
| `connect` | **Connect** button | Commands → Admin | Parameter prompt |
| `listen` | **Listen** button | Commands → Admin | Parameter prompt |
| `pyexec` | **Python Exec** button | Commands → Admin | Parameter prompt |

### 9. Custom Commands

| CLI Feature | Web Interface | Location | Enhancement |
|-------------|---------------|----------|-------------|
| Any command input | **Custom Command Input** | Commands → Custom | 500 char limit, validation |
| Command history | **Arrow key navigation** | Commands → Custom | 50-command history |
| Tab completion | Not applicable | N/A | Web uses buttons instead |

---

## Connection Management Mapping

| CLI Feature | Web Interface | Enhancement |
|-------------|---------------|-------------|
| `sessions` | **Connections Dashboard** | Visual cards with status indicators |
| `shell <ip>` | **Click connection card** | Visual selection with quick actions |
| Manual IP switching | **Connection selection** | Persistent selection across tabs |
| Text-based status | **Real-time status updates** | Online/offline indicators, last seen |
| No connection filtering | **Search & Filter** | Search by IP/OS/hostname, status filters |

---

## File Management Mapping

| CLI Feature | Web Interface | Enhancement |
|-------------|---------------|-------------|
| `upload <file>` | **Drag & Drop Upload Zone** | Visual progress, 100MB limit validation |
| Manual file paths | **File Browser** | Click to download, file metadata |
| No download management | **Downloaded Files Grid** | Search, pagination, size/date info |
| Command-based transfers | **Progress Indicators** | Real-time upload progress bars |

---

## Monitoring & Logging Mapping

| CLI Feature | Web Interface | Enhancement |
|-------------|---------------|-------------|
| Terminal output only | **Real-time Debug Logs** | WebSocket streaming, 1000-entry buffer |
| No persistent logs | **Export Logs (JSON/CSV)** | Download logs and command history |
| No command history export | **Export Commands (JSON/CSV)** | Full audit trail with timestamps |
| Basic command output | **Formatted Output with Timestamps** | Copy to clipboard, clear functions |
| No metrics | **Connection Health Monitoring** | Last seen timestamps, connection duration |

---

## Security Enhancements Mapping

| CLI Security | Web Interface Security | Enhancement |
|--------------|----------------------|-------------|
| No authentication | **Login System** | Environment-based credentials |
| No session management | **Secure Sessions** | HttpOnly cookies, CSRF tokens |
| No rate limiting | **Rate Limiting** | 30 commands/min, 5 login attempts/15min |
| No input validation | **Input Validation** | Length limits, control character blocking |
| No confirmation dialogs | **Dangerous Command Confirmations** | 25+ commands require explicit confirmation |
| No audit trail | **Comprehensive Logging** | 34 audit points, user tracking |
| HTTP only | **HTTPS Support** | Auto-generated certificates, HSTS headers |

---

## API Endpoints Mapping

| CLI Function | Web API Endpoint | Method | Purpose |
|--------------|------------------|--------|---------|
| Server status | `/api/server/status` | GET | Server listening status |
| Connection list | `/api/connections` | GET | Active and historical connections |
| Command execution | `/api/execute` | POST | Execute commands on targets |
| File upload | `/api/upload` | POST | Upload files to targets |
| File download | `/api/files/download/<path>` | GET | Download files from server |
| Export logs | `/api/export/logs` | GET | Export debug logs (JSON/CSV) |
| Export commands | `/api/export/commands` | GET | Export command history (JSON/CSV) |
| Health check | `/health` | GET | Service health status |
| Command definitions | `/api/command_definitions` | GET | Interactive command metadata |
| Manual cleanup | `/api/cleanup/connections` | POST | Clean stale connection contexts |

---

## WebSocket Events Mapping

| CLI Feature | WebSocket Event | Purpose |
|-------------|-----------------|---------|
| Manual refresh | `connection_update` | Real-time connection count updates |
| No real-time logs | `debug_log` | Live log streaming to UI |
| Manual status check | `ping/pong` | Connection health monitoring |

---

## Usage Pattern Mapping

### CLI Workflow
```bash
python main.py
> listen 4040
> sessions
> shell 192.168.1.100
> sysinfo
> upload /path/to/file
> download /remote/file
> exit
```

### Web Interface Workflow
1. **Start**: `python web_app_real.py`
2. **Login**: Navigate to `http://localhost:5000/login`
3. **Monitor**: View connections in dashboard (auto-refreshing)
4. **Select**: Click connection card to select target
5. **Execute**: Click command buttons or use custom input
6. **Upload**: Drag & drop files in Files tab
7. **Download**: Click download links in Files tab
8. **Export**: Export logs/commands for audit

---

## Parity Verification

### ✅ Complete Parity Achieved
- **All 75+ commands accessible** via buttons or custom input
- **Same underlying execution engine** (`stitch_lib.py`)
- **Same AES encryption** and handshake process
- **Same port 4040** for target connections
- **Same command syntax** in custom input field

### 🏆 Enhanced Beyond CLI
- **Visual connection management** with real-time status
- **Safety confirmations** for dangerous operations
- **File upload progress** and drag-and-drop
- **Audit logging** with user tracking
- **Export capabilities** for logs and commands
- **Search and filtering** for connections and files
- **Rate limiting** and security headers
- **Session management** and authentication

### 🔄 Behavioral Differences
- **Web requires browser** (CLI works in pure terminal)
- **Web has confirmation dialogs** (CLI executes immediately)
- **Web validates input** (CLI passes through directly)
- **Web tracks users** (CLI has no user concept)

---

## Migration Guide

### From CLI to Web
1. **Same server**: Web interface includes CLI functionality
2. **Same commands**: All CLI commands work in web custom input
3. **Same targets**: Existing connections work with both interfaces
4. **Same files**: Downloads/uploads use same directory structure
5. **Enhanced safety**: Web adds confirmations and validation

### Running Both Simultaneously
- **Recommended approach**: Start web interface (`python web_app_real.py`)
- **CLI access**: Web interface includes all CLI functionality
- **Shared state**: Both use same server instance and connections
- **No conflicts**: Web and CLI can operate simultaneously

---

## Command Reference Quick Guide

| Need to... | CLI Command | Web Interface |
|------------|-------------|---------------|
| See connections | `sessions` | Connections tab |
| Select target | `shell <ip>` | Click connection card |
| Get system info | `sysinfo` | Commands → System Info → System Info |
| Take screenshot | `screenshot` | Commands → Control & Exploit → Screenshot |
| Upload file | `upload <file>` | Files tab → Drag & drop |
| Download file | `download <file>` | Commands → Files → Download (with prompt) |
| View logs | Terminal output | Logs tab |
| Export data | Not available | Logs tab → Export buttons |
| Clear event logs | `clearev` | Commands → Windows → Clear Events (with confirmation) |
| Dump passwords | `hashdump` | Commands → Control & Exploit → Hash Dump (with confirmation) |
| Start keylogger | `keylogger start` | Commands → Control & Exploit → Keylog Start (with confirmation) |
| Custom command | Type directly | Commands → Custom → Text input |

---

## Conclusion

The web interface provides **100% feature parity** with the CLI while adding significant enhancements for safety, usability, and monitoring. Users can:

1. **Use familiar commands** - All CLI commands work in web custom input
2. **Benefit from safety features** - Confirmations prevent accidental damage
3. **Enjoy better UX** - Visual interface with real-time updates
4. **Maintain security** - Authentication, rate limiting, audit trails
5. **Access enhanced features** - Export, search, progress tracking

The mapping is complete and comprehensive, ensuring no functionality is lost while providing substantial improvements for production use.

---

*Last Updated: October 17, 2025*  
*Version: 1.0*