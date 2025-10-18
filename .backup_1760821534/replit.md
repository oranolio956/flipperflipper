# Stitch RAT - Real-Time Web Interface

## Overview
Stitch is a Remote Administration Tool (RAT) with both command-line and web interfaces. This project delivers a real-time web interface providing full functionality for managing and interacting with connected targets. The application has undergone significant security hardening, addressing critical vulnerabilities to achieve production readiness. It offers a graphical dashboard for monitoring connections, executing commands, and managing files on remote systems, serving as a user-friendly alternative to the command-line interface.

## Recent Changes (October 17, 2025)

### Latest Updates - Interactive Commands & Production-Ready Execution ✅
- **Interactive command support** - 8 previously CLI-only commands (firewall, hostsfile, popup, clearev, timestomp, logintext) now work in web interface
- **Command definitions registry** - Comprehensive metadata system with parameter schemas, validation rules, OS-specific handling
- **Greenlet-safe input mocking** - Uses eventlet.corolocal.local() for proper greenlet isolation in concurrent Flask/eventlet requests
- **Critical cleanup** - Finally block always restores builtins.input to prevent global state pollution
- **Inline parameter syntax** - Supports commands like `firewall open port=80 protocol=tcp direction=IN`
- **Parameter validation** - Port range checking (1-65535), required field validation, type checking before execution
- **Early validation** - Parameters validated before any monkey-patching, fail-fast on errors
- **API endpoint for metadata** - `/api/command_definitions` returns command schemas to frontend
- **Complete command execution rewrite** - Properly uses `stitch_commands_library` methods with pyexec protocol
- **Health check endpoint** - `/health` for deployment health checks (200, no auth required)
- **Deployment configuration** - Corrected to `python3 web_app_real.py`, autoscale target
- **Command routing** - 47+ commands (40 non-interactive + 7 interactive) with proper OS-specific handling
- **Output capture** - Stdout redirection captures st_print output from library methods
- **Production-ready status** - Architect-approved: No concurrency hazards, proper cleanup, robust validation

### Interface Optimization Sweep (Previous)
- **Smart connection selection** - No auto-switch to Commands tab; user stays in context while selecting targets
- **Persistent target indicator** - Always-visible active target display in sidebar (🎯 online / ⚫ offline)
- **Quick action buttons** - 4 instant-execute buttons on ONLINE connection cards (Info, Screen, Hashes, Commands)
- **Reorganized command categories** - Most ruthless/useful commands first (Control & Exploit is now default)
- **Confirmation dialogs** for 25+ dangerous commands (clearev, avkill, shutdown, keylogger, etc.)
- **Pagination system** for connections and files (10/25/50/100 items per page)
- **Heartbeat monitoring** with last_seen and connected_at timestamps
- **Comprehensive documentation** suite (BACKUP_RESTORE.md, MULTI_USER.md, COMMANDS_INVENTORY.md, CLI_VS_WEB_COMPARISON.md, SECURITY_AUDIT.md)

### Core Features
- **Redesigned login page** with modern animated gradient background, glassmorphism card design
- **Added 75+ Stitch commands** organized in 8 categories with command history navigation
- **File upload with drag-and-drop** supporting 100MB files with progress tracking
- **Search and filter** for connections (by IP/OS/hostname) and files
- **Export functionality** for logs and command history (JSON/CSV formats)
- **Complete session management** with per-user tracking and isolation

## User Preferences
- I want iterative development.
- Ask before making major changes.

## System Architecture
The web interface (`web_app_real.py`) runs as a standalone process, integrating a `stitch_server` instance in a background thread. The server listens on port 4040 for target connections, while the Flask web server operates on port 5000 for the UI. Both share the same `stitch_server` instance within the process, accessing shared data structures like `server.inf_sock` for connection status.

**UI/UX Decisions:**
- Modern, responsive dashboard design with a dark theme optimized for offensive operators.
- Visual indicators for online/offline status with persistent active target display.
- Click-to-select functionality for connections with smart context preservation.
- Quick action buttons on connection cards for instant command execution.
- Command categories prioritized by danger/frequency (Control & Exploit first).
- WebSocket-based real-time updates for connections and logs, refreshing every 5 seconds.

**Technical Implementations & Feature Specifications:**
- **Real-time Connection Tracking:** Displays actual online/offline status of targets from socket connections with heartbeat monitoring (last seen, connected at timestamps).
- **Command Execution:** Supports all 75+ Stitch commands organized in 8 categories prioritized for offensive operations (Control & Exploit, Windows, Files, Network, System Info, Admin, macOS/Linux, Custom). Includes:
    - Command history navigation with arrow keys (50-command storage)
    - Confirmation dialogs for 25+ dangerous commands
    - Real-time output with timestamps
    - Copy to clipboard functionality
- **File Management:** 
    - Browsing and downloading of files from targets
    - Drag-and-drop file upload with progress tracking (100MB limit)
    - Multi-layer validation (client + server)
    - Search/Filter: Real-time search for connections (IP, OS, hostname) and files
    - Status filtering (all/online/offline)
    - Pagination (10/25/50/100 items per page)
- **Export Functionality:** Download logs and command history in JSON or CSV format with timestamped filenames
- **Debug Logging:** Real-time log streaming via WebSocket with filtering capabilities (34 audit points tracking all user actions).
- **Security Features:**
    - Environment variable-based credentials (`STITCH_ADMIN_USER`, `STITCH_ADMIN_PASSWORD`) with 12+ character enforcement.
    - Rate limiting using Flask-Limiter for login attempts (5 per 15 min) and API throttling.
    - Secured CORS policy, rejecting wildcards and defaulting to localhost, configurable for production.
    - HTTPS support with auto-generated 4096-bit RSA certificates or custom certificates.
    - Debug mode disabled by default for production safety.
    - Session-based authentication, CSRF protection, and AES encryption for target communication.
    - Input validation on all endpoints (500 char limit, control character blocking, file size limits)

**System Design Choices:**
- Flask with Flask-SocketIO for real-time capabilities.
- Eventlet for asynchronous task handling.
- Werkzeug for security utilities (e.g., password hashing).
- Thread-safe access to the shared `stitch_server` instance using locks.
- The web interface and CLI use the same underlying Stitch server code and AES encryption, accepting connections on port 4040.

## External Dependencies
- **Flask**: Web framework for building the application.
- **Flask-SocketIO**: Enables real-time, two-way communication via WebSockets.
- **Flask-Limiter**: Implements rate limiting for API endpoints and login attempts.
- **Eventlet**: Asynchronous I/O library for concurrent operations.
- **Werkzeug**: WSGI utility library, used for security features like password hashing.
- **OpenSSL**: Required for HTTPS certificate generation and management.
- **Python 3.8+**: Minimum required Python version.

## Documentation Suite
- **HOW_TO_LOGIN.md** - Credential management and login guide
- **BACKUP_RESTORE.md** - Comprehensive backup and disaster recovery procedures
- **MULTI_USER.md** - Multi-user management and RBAC implementation guide
- **COMMANDS_INVENTORY.md** - Complete listing of all 75+ commands with descriptions
- **CLI_VS_WEB_COMPARISON.md** - Feature parity analysis between CLI and web interfaces
- **SECURITY_AUDIT.md** - Security assessment and production deployment checklist
- **TASK_LIST.md** - Development task tracking

## Quick Start
1. Set credentials in Replit Secrets (`STITCH_ADMIN_USER`, `STITCH_ADMIN_PASSWORD`)
2. Run `python3 check_credentials.py` to verify setup
3. Start the server (workflow starts automatically)
4. Navigate to the web interface
5. Login with your credentials
6. Targets connect to port 4040 automatically

## Production Deployment
See `SECURITY_AUDIT.md` for complete production checklist including:
- HTTPS configuration
- CORS policy setup
- Rate limiting tuning
- Backup procedures
- Security hardening