# Stitch RAT - Complete Command Inventory

## Total Commands: 75+

All commands from the CLI are accessible through the web interface, organized into 8 categories for easy access.

---

## Category 1: System Information (9 commands)
| Command | Description | Parameters |
|---------|-------------|------------|
| `sysinfo` | Complete system information | None |
| `environment` | Display environment variables | None |
| `ps` | List all running processes | None |
| `lsmod` | List installed drivers/kernel modules | None |
| `drives` | Display drive information | None |
| `location` | Get public IP and geo-location | None |
| `vmscan` | Detect if running in virtual machine | None |
| `pwd` | Print working directory | None |
| `ls` | List files and directories | None |

---

## Category 2: File Operations (15 commands)
| Command | Description | Parameters |
|---------|-------------|------------|
| `download` | Download file from target | filename |
| `upload` | Upload file to target | Uses file picker UI |
| `cat` | Display file contents | filename |
| `ls` | List directory contents | path (optional) |
| `cd` | Change directory | path |
| `pwd` | Show current directory | None |
| `rm` | Remove file | filename |
| `mkdir` | Create directory | dirname |
| `hide` | Hide file/folder (Windows) | path |
| `zip` | Create zip archive | files |
| `unzip` | Extract zip archive | filename |
| `editaccessed` | Modify file accessed time | filename, date |
| `editcreated` | Modify file creation time | filename, date |
| `editmodified` | Modify file modified time | filename, date |
| `search` | Search for files | pattern |

---

## Category 3: Network Operations (8 commands)
| Command | Description | Parameters |
|---------|-------------|------------|
| `ipconfig` | Display network configuration | None |
| `portscan` | Scan ports on target/host | host, ports |
| `hostsfile get` | View hosts file | None |
| `hostsfile update` | Update hosts file | entry |
| `hostsfile remove` | Remove hosts entry | entry |
| `netstat` | Show network connections | None |
| `firewall status` | Check firewall status | None |
| `firewall close` | Close firewall ports | port |

---

## Category 4: Security & Credentials (11 commands)
| Command | Description | Parameters |
|---------|-------------|------------|
| `hashdump` | Dump password hashes (admin) | None |
| `keylogger start` | Start keylogger | duration (optional) |
| `keylogger stop` | Stop keylogger | None |
| `keylogger dump` | Retrieve keylogger data | None |
| `screenshot` | Capture screenshot | None |
| `webcam` | Capture webcam photo | None |
| `microphone` | Record audio | duration |
| `wifikeys` | Extract saved WiFi passwords | None |
| `chromedump` | Extract Chrome passwords | None |
| `crackpassword` | Attempt password cracking | hash |
| `clipboard` | Get clipboard contents | None |

---

## Category 5: Windows Specific (14 commands)
| Command | Description | Parameters |
|---------|-------------|------------|
| `clearev` | Clear Windows event logs | None |
| `avkill` | Disable antivirus (if possible) | None |
| `disableRDP` | Disable Remote Desktop | None |
| `disableUAC` | Disable User Account Control | None |
| `disableWindef` | Disable Windows Defender | None |
| `scanreg` | Scan registry for keywords | keyword |
| `persistence` | Add to startup (persistence) | method |
| `rdp` | Enable RDP | None |
| `uac` | Check UAC status | None |
| `windefender` | Check Windows Defender status | None |
| `services` | List Windows services | None |
| `startup` | List startup programs | None |
| `tasklist` | Detailed process list | None |
| `registry` | Query registry key | key |

---

## Category 6: macOS/Linux Specific (7 commands)
| Command | Description | Parameters |
|---------|-------------|------------|
| `shell` | Execute shell command | command |
| `sudo` | Execute with sudo | command |
| `whoami` | Show current user | None |
| `uname` | System information | None |
| `top` | Show running processes | None |
| `crontab` | Manage cron jobs | operation |
| `syslog` | View system logs | lines (optional) |

---

## Category 7: Admin/Control (7 commands)
| Command | Description | Parameters |
|---------|-------------|------------|
| `lockscreen` | Lock the target screen | None |
| `displayoff` | Turn off display | None |
| `freeze start` | Start freezing mouse/keyboard | None |
| `freeze stop` | Stop freezing input | None |
| `shutdown` | Shutdown target system | delay (optional) |
| `reboot` | Reboot target system | delay (optional) |
| `logoff` | Log off current user | None |

---

## Category 8: Custom Commands (Unlimited)
| Command | Description | Parameters |
|---------|-------------|------------|
| Custom input | Execute any command | User-defined |

The custom command interface allows execution of:
- Any Stitch command not in the quick buttons
- Shell commands via `shell` prefix
- Parameterized commands
- Chained commands

---

## Command Execution Features

### Safety Features
✅ **25+ dangerous commands require confirmation**:
- Destructive: `clearev`, `avkill`, `shutdown`, `reboot`
- Security: `disableUAC`, `disableWindef`, `disableRDP`
- System modification: `freeze`, `lockscreen`, `hashdump`
- File operations: `hide`, `editaccessed`, `editcreated`, `editmodified`
- Network: `hostsfile remove`, `firewall close`
- Credential theft: `keylogger start`, `chromedump`, `wifikeys`, `crackpassword`

### Input Validation
✅ **All commands validated**:
- 500 character maximum length
- Control character blocking
- Excessive whitespace removal
- SQL injection prevention

### Command History
✅ **50-command history**:
- Arrow key navigation (↑ / ↓)
- Persistent during session
- Exportable (JSON/CSV)

### Real-time Output
✅ **Live command results**:
- Timestamped execution logs
- Success/failure indicators
- Error details
- Copy to clipboard

---

## Command Comparison: CLI vs Web

| Feature | CLI | Web Interface |
|---------|-----|---------------|
| All 75+ commands | ✅ | ✅ |
| Command history | ✅ | ✅ (50 entries) |
| Real-time output | ✅ | ✅ |
| File upload | ✅ | ✅ (drag & drop) |
| File download | ✅ | ✅ (one-click) |
| Connection status | ✅ | ✅ (visual cards) |
| Multi-connection | ✅ | ✅ (click to switch) |
| Confirmation dialogs | ❌ | ✅ (25+ dangerous commands) |
| Search/filter | ❌ | ✅ |
| Export logs | ❌ | ✅ (JSON/CSV) |
| Pagination | ❌ | ✅ |
| Health monitoring | Limited | ✅ (last seen timestamps) |

---

## Command Status Legend

- ✅ **Fully Implemented**: Working as expected
- 🟡 **Platform Specific**: Only works on target OS
- ⚠️ **Requires Admin**: Needs elevated privileges
- 🔒 **Requires Confirmation**: Safety dialog required

---

## Testing Recommendations

To verify command functionality:
1. Connect a target to the server (port 4040)
2. Select the connection in the web interface
3. Test each category of commands
4. Verify output appears correctly
5. Check dangerous commands show confirmation dialogs
6. Verify file upload/download works
7. Test custom command input

---

## Documentation

Each command category has help text in the UI. Hover over command buttons to see descriptions.

For detailed command syntax, refer to the original Stitch documentation.

---

## Security Notes

- All commands are logged with username and timestamp
- Dangerous commands require explicit confirmation
- Input validation prevents command injection
- CSRF tokens protect against cross-site attacks
- Rate limiting prevents abuse (30 commands/minute)

---

Last Updated: October 17, 2025
Version: 1.0
