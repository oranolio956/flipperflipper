# DISCLAIMER
**Stitch is for education/research purposes only. The author takes NO responsibility and/or liability for how you choose to use any of the tools/source code/any files provided.
 The author and anyone affiliated with will not be liable for any losses and/or damages in connection with use of ANY files provided with Stitch.
 By using Stitch or any files included, you understand that you are AGREEING TO USE AT YOUR OWN RISK. Once again Stitch and ALL files included are for EDUCATION and/or RESEARCH purposes ONLY.
 Stitch is ONLY intended to be used on your own pentesting labs, or with explicit consent from the owner of the property being tested.** 

# Stitch RAT - Cross Platform Remote Administration Tool

## 🌐 Web Interface + CLI
Stitch now includes a **modern web interface** alongside the original CLI, providing:
- **Visual dashboard** with real-time connection monitoring
- **Enhanced security** with authentication, CSRF protection, and dangerous command confirmations  
- **File management** with drag & drop uploads and progress tracking
- **Audit logging** with export capabilities (JSON/CSV)
- **100% feature parity** with CLI - all 75+ commands accessible

## About Stitch
A Cross Platform Python Remote Administration Tool with dual interfaces:

**🖥️ Traditional CLI**: Terminal-based interface for power users and automation  
**🌐 Web Interface**: Modern browser-based dashboard for enhanced usability and security

This is a cross platform python framework which allows you to build custom payloads for Windows, Mac OSX and Linux as well. You are able to select whether the payload binds to a specific IP and port, listens for a connection on a port, option to send an email of system info when the system boots, and option to start keylogger on boot. Payloads created can only run on the OS that they were created on.

## Features
### Cross Platform Support
- Command and file auto-completion
- Antivirus detection 
- Able to turn off/on display monitors
- Hide/unhide files and directories
- View/edit the hosts file
- View all the systems environment variables
- Keylogger with options to view status, start, stop and dump the logs onto your host system
- View the location and other information of the target machine 
- Execute custom python scripts which return whatever you print to screen
- Screenshots
- Virtual machine detection
- Download/Upload files to and from the target system
- Attempt to dump the systems password hashes
- Payloads' properties are "disguised" as other known programs

### Windows Specific
- Display a user/password dialog box to obtain user password
- Dump passwords saved via Chrome
- Clear the System, Security, and Application logs
- Enable/Disable services such as RDP,UAC, and Windows Defender
- Edit the accessed, created, and modified properties of files
- Create a custom popup box
- View connected webcam and take snapshots
- View past connected wifi connections along with their passwords
- View information about drives connected 
- View summary of registry values such as DEP

### Mac OSX Specific
- Display a user/password dialog box to obtain user password
- Change the login text at the user's login screen
- Webcam snapshots

### Mac OSX/Linux Specific
- SSH from the target machine into another host
- Run sudo commands
- Attempt to bruteforce the user's password using the passwords list found in Tools/
- Webcam snapshots? (untested on Linux)

## Implemented Transports
All communication between the host and target is AES encrypted. Every Stitch program generates an AES key which is then put into all payloads. To access a payload the AES keys must match. To connect from a different system running Stitch you must add the key by using the showkey command from the original system and the addkey command on the new system. 

## Implemented Payload Installers
The "stitchgen" command gives the user the option to create [NSIS](http://nsis.sourceforge.net/Main_Page) installers on Windows and [Makeself](http://stephanepeter.com/makeself/) installers on posix machines. For Windows, the installer packages the payload and an elevation exe ,which prevents the firewall prompt and adds persistence, and places the payload on the system. For Mac OSX and Linux, the installer places the payload and attempts to add persistence. To create NSIS installers you must [download](http://nsis.sourceforge.net/Download) and install NSIS. 

## Wiki
* [Crash Course of Stitch](https://github.com/nathanlopez/Stitch/wiki/Crash-Course)

## Requirements
- [Python 2.7](https://www.python.org/downloads/)

For easy installation run the following command that corresponds to your OS:
```
# for Windows
pip install -r win_requirements.txt

# for Mac OSX
pip install -r osx_requirements.txt

# for Linux
pip install -r lnx_requirements.txt
```

- [Pycrypto](https://pypi.python.org/pypi/pycrypto)
- [Requests](http://docs.python-requests.org/en/master/)
- [Colorama](https://pypi.python.org/pypi/colorama)
- [PIL](https://pypi.python.org/pypi/PIL)

### Windows Specific
- [Py2exe](http://www.py2exe.org/)
- [pywin32](https://sourceforge.net/projects/pywin32/)

### Mac OSX Specific
- [PyObjC](https://pythonhosted.org/pyobjc/)

### Mac OSX/Linux Specific
- [PyInstaller](http://www.pyinstaller.org/)
- [pexpect](https://pexpect.readthedocs.io/en/stable/)

## How to Run

### 🌐 Web Interface (Recommended)
```bash
# Install dependencies
python3 -m pip install -r requirements.txt

# Set required environment variables
export STITCH_ADMIN_USER=admin
export STITCH_ADMIN_PASSWORD='SuperSecurePassw0rd!'   # 12+ chars

# Optional: Enable HTTPS
export STITCH_ENABLE_HTTPS=true
export STITCH_ALLOWED_ORIGINS=https://yourdomain.com

# Start web interface (includes CLI functionality)
python3 web_app_real.py
```

**Access**: Open `http://localhost:5000` in your browser

### 🖥️ Traditional CLI
```bash
python main.py
# or
./main.py
```

### 🔄 Both Interfaces
The web interface includes the CLI server, so you can:
- Use the web dashboard for visual operations
- Connect CLI clients to the same server
- Switch between interfaces as needed

---

## 🚀 Quick Start Guide

### 1. Setup
```bash
git clone https://github.com/nathanlopez/Stitch.git
cd Stitch
python3 -m pip install -r requirements.txt
```

### 2. Configure Authentication
```bash
export STITCH_ADMIN_USER=admin
export STITCH_ADMIN_PASSWORD='YourSecurePassword123!'
```

### 3. Start Server
```bash
python3 web_app_real.py
```

### 4. Access Interface
- **Web**: `http://localhost:5000`
- **Targets connect to**: `port 4040`

### 5. Connect Targets
- Generate payloads using `stitchgen` command
- Deploy to target systems
- Targets will appear in web dashboard when connected

---

## 🔐 Security & Authentication

### Required Environment Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `STITCH_ADMIN_USER` | Admin username (required) | `admin` |
| `STITCH_ADMIN_PASSWORD` | Admin password 12+ chars (required) | `SuperSecurePassw0rd!` |

### Optional Security Settings
| Variable | Description | Default |
|----------|-------------|---------|
| `STITCH_ENABLE_HTTPS` | Enable HTTPS with auto-generated certs | `false` |
| `STITCH_ALLOWED_ORIGINS` | CORS origins (comma-separated) | `localhost` |
| `STITCH_SESSION_TIMEOUT` | Session timeout in minutes | `30` |

### Security Features
- ✅ **Authentication required** - No default credentials
- ✅ **CSRF protection** - Prevents cross-site attacks  
- ✅ **Rate limiting** - 30 commands/min, 5 login attempts/15min
- ✅ **Input validation** - 500 char limit, control character blocking
- ✅ **Dangerous command confirmations** - 25+ commands require explicit approval
- ✅ **HTTPS support** - Auto-generated certificates
- ✅ **Audit logging** - All actions logged with timestamps and user

---

## 📊 Web Interface Features

### 🎯 Connection Management
- **Visual dashboard** with connection cards
- **Real-time status** updates (online/offline)
- **Click to select** targets for command execution
- **Search & filter** by IP, OS, hostname
- **Connection health** monitoring with last seen timestamps

### ⚡ Command Execution  
- **8 organized categories** with 75+ commands
- **Quick action buttons** for common operations
- **Custom command input** with history (50 commands)
- **Confirmation dialogs** for dangerous operations
- **Real-time output** with timestamps and copy functionality

### 📁 File Management
- **Drag & drop uploads** with progress tracking
- **One-click downloads** from file browser
- **File search** and metadata display
- **100MB upload limit** with validation

### 📋 Monitoring & Logging
- **Real-time debug logs** via WebSocket
- **Export capabilities** (JSON/CSV) for logs and commands
- **Connection health** metrics
- **Audit trail** with user tracking

### 🔒 Security Dashboard
- **Login system** with secure sessions
- **Rate limit monitoring** 
- **Failed login alerts**
- **CSRF token management**

---

## 🎯 Command Categories

### 🔥 Control & Exploit (19 commands)
High-impact operations for system control and data extraction:
- **Keylogger**: Start/stop/dump keystrokes
- **Screenshots**: Capture screen images  
- **Webcam**: List cameras and take photos
- **Credential theft**: Hash dumps, WiFi keys, Chrome passwords
- **System control**: Freeze input, display control, lock screen

### 🪟 Windows-Specific (9 commands)  
Windows security and system modifications:
- **Event log clearing**: Remove forensic evidence
- **Security disabling**: UAC, RDP, Windows Defender
- **Registry operations**: Scan and modify registry
- **Antivirus**: Scan and terminate AV processes

### 📁 File Operations (12 commands)
File system manipulation and data exfiltration:
- **Upload/Download**: Bidirectional file transfer
- **Timestamp modification**: Anti-forensics
- **File hiding**: Stealth operations
- **Directory navigation**: Remote file system access

### 🌐 Network (8 commands)
Network reconnaissance and manipulation:
- **Configuration**: View network settings
- **Firewall control**: Open/close ports, manage rules
- **Hosts file**: Redirect network traffic
- **SSH tunneling**: Lateral movement

### 📊 System Information (9 commands)
Reconnaissance and system profiling:
- **System details**: Hardware, OS, environment
- **Process monitoring**: Running applications
- **Location tracking**: IP geolocation
- **VM detection**: Sandbox evasion

### 🍎 macOS/Linux (2 commands)
Unix-specific operations:
- **Password harvesting**: Fake authentication prompts
- **Privilege escalation**: Sudo password cracking

### ⚙️ Administrative (16 commands)
Server and session management:
- **Connection management**: Sessions, history
- **Key management**: AES encryption keys
- **Payload generation**: Create new implants
- **Server control**: Listen, connect, configure

### ⌨️ Custom Commands
- **Unlimited flexibility**: Execute any Stitch command
- **Parameter support**: Interactive command forms
- **History navigation**: Arrow key command recall

---

## 🔄 Handshake Process

### Connection Establishment
1. **Target connects** to server on port 4040
2. **Magic string exchange** - Confirms Stitch protocol
3. **AES ID transmission** - Target sends encryption identifier  
4. **Key lookup** - Server retrieves AES key from `st_aes_lib.ini`
5. **Metadata exchange** - Encrypted system information (OS, user, hostname)
6. **Context storage** - Connection details cached for session

### Security Details
- **AES encryption** for all command traffic after handshake
- **Key management** via `Application/Stitch_Vars/st_aes_lib.ini`
- **Connection context** includes: AES key, OS, platform, hostname, user, port
- **Automatic cleanup** on connection loss, timeout, or error

### Error Handling
- **Handshake failures** trigger re-authentication on next command
- **Stale contexts** automatically purged on socket errors
- **Connection monitoring** detects and cleans dropped connections

---

## 📈 Metrics & Monitoring

### Available Metrics
Access via `/metrics` (Prometheus format) or `/api/metrics` (JSON):

**Counters**:
- `stitch_commands_total` - Commands executed
- `stitch_command_errors_total` - Failed commands  
- `stitch_logins_total` - Login attempts (success/failed)
- `stitch_api_requests_total` - API endpoint hits

**Gauges**:
- `stitch_active_connections` - Current target connections
- `stitch_active_sessions` - Current user sessions
- `stitch_uptime_seconds` - Server uptime

**Histograms**:
- `stitch_command_duration_seconds` - Command execution times
- `stitch_http_response_time_seconds` - API response times

**System Metrics**:
- CPU, memory, and disk usage
- Process and network statistics

### Monitoring Setup
```bash
# Enable metrics collection
export STITCH_ENABLE_METRICS=true

# Optional: Require authentication for metrics
export STITCH_METRICS_AUTH_REQUIRED=true
```

---

## 🛠️ Operational Runbook

### Environment Variables Reference

#### Required
```bash
STITCH_ADMIN_USER=admin                    # Admin username
STITCH_ADMIN_PASSWORD=SecurePass123!       # Password (12+ chars)
```

#### Security
```bash
STITCH_ENABLE_HTTPS=true                   # Enable HTTPS
STITCH_ALLOWED_ORIGINS=https://domain.com  # CORS origins
STITCH_SESSION_TIMEOUT=30                  # Session timeout (minutes)
STITCH_MAX_LOGIN_ATTEMPTS=5                # Login attempt limit
STITCH_LOGIN_LOCKOUT_MINUTES=15            # Lockout duration
```

#### Performance
```bash
STITCH_COMMANDS_PER_MINUTE=30              # Command rate limit
STITCH_EXECUTIONS_PER_MINUTE=60            # Execute endpoint limit
STITCH_API_POLLING_PER_HOUR=1000           # UI polling limit
STITCH_MAX_UPLOAD_SIZE=104857600           # Upload limit (100MB)
```

#### Logging
```bash
STITCH_LOG_LEVEL=INFO                      # Log verbosity
STITCH_ENABLE_FILE_LOGGING=true            # File logging
STITCH_MAX_DEBUG_LOGS=1000                 # Log buffer size
STITCH_MAX_COMMAND_HISTORY=1000            # Command history size
```

### Backup & Restore
```bash
# Export logs and commands
curl -H "Cookie: session=..." http://localhost:5000/api/export/logs?format=json > logs.json
curl -H "Cookie: session=..." http://localhost:5000/api/export/commands?format=csv > commands.csv

# Backup AES keys
cp Application/Stitch_Vars/st_aes_lib.ini aes_keys_backup.ini

# Backup connection history  
cp Application/Stitch_Vars/history.ini history_backup.ini
```

### Troubleshooting

#### Connection Issues
```bash
# Check server status
curl http://localhost:5000/api/server/status

# View active connections
curl -H "Cookie: session=..." http://localhost:5000/api/connections

# Manual cleanup of stale connections
curl -X POST -H "Cookie: session=..." http://localhost:5000/api/cleanup/connections
```

#### Authentication Issues
```bash
# Verify environment variables
echo $STITCH_ADMIN_USER
echo ${#STITCH_ADMIN_PASSWORD}  # Should be 12+

# Check failed login attempts
tail -f Logs/stitch_web.log | grep "Failed login"
```

#### Performance Issues
```bash
# Check metrics
curl http://localhost:5000/metrics

# Monitor system resources
curl -H "Cookie: session=..." http://localhost:5000/api/metrics | jq '.system'
```

### Security Checklist
- [ ] Strong admin password (12+ characters)
- [ ] HTTPS enabled for production
- [ ] CORS origins restricted (no wildcards)
- [ ] Rate limiting configured appropriately
- [ ] Regular log review and export
- [ ] AES keys backed up securely
- [ ] Failed login monitoring enabled

### Maintenance Tasks
- **Daily**: Review audit logs for suspicious activity
- **Weekly**: Export and archive command history
- **Monthly**: Backup AES keys and configuration
- **Quarterly**: Review and rotate admin credentials

## Motivation
My motivation behind this was to advance my knowledge of python, hacking, and just to see what I could accomplish. Was somewhat discouraged and almost abandoned this project when I found the amazing work done by [n1nj4sec](https://github.com/n1nj4sec/pupy), but still decided to put this up since I had already come so far. 

## Other open-source Python RATs for Reference
* [vesche/basicRAT](https://github.com/vesche/basicRAT)
* [n1nj4sec/pupy](https://github.com/n1nj4sec/pupy)

## Screenshots

![linux options](https://cloud.githubusercontent.com/assets/13227314/21706500/76fdb962-d37c-11e6-9284-093ad065aeca.PNG)
![win_options](https://cloud.githubusercontent.com/assets/13227314/21706517/80d977b4-d37c-11e6-9588-5cd1bb3ecf37.PNG)
![win_upload](https://cloud.githubusercontent.com/assets/13227314/21706518/83c8509e-d37c-11e6-9f6e-f86b3a696c1a.PNG)
![osx_download](https://cloud.githubusercontent.com/assets/13227314/21706506/79f54e96-d37c-11e6-928b-68a8c57df919.PNG)

## License

See [LICENSE](/LICENSE)
