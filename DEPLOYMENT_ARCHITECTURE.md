# 🏗️ Deployment Architecture & Flow Diagrams

## Visual Guide to Your Ubuntu VPS Deployment

---

## 📊 Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          INTERNET / USERS                            │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 │ HTTPS (Port 443)
                                 │ HTTP (Port 80)
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         IONOS CLOUD FIREWALL                         │
│  Rules: Allow 22 (SSH), 80 (HTTP), 443 (HTTPS)                     │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         YOUR UBUNTU VPS                              │
│  IP: YOUR_VPS_IP                                                    │
│  OS: Ubuntu 20.04/22.04                                             │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                    UFW FIREWALL                             │   │
│  │  Port 22  → SSH (Your IP only - recommended)               │   │
│  │  Port 80  → HTTP (Redirect to 443)                         │   │
│  │  Port 443 → HTTPS (Nginx)                                  │   │
│  │  Port 5000→ App (Internal only)                            │   │
│  └────────────────────────────┬───────────────────────────────┘   │
│                                │                                     │
│                                ▼                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │              NGINX (Reverse Proxy)                          │   │
│  │  - Port 80: Redirect to 443                                │   │
│  │  - Port 443: SSL/TLS Termination                           │   │
│  │  - Proxy to: localhost:5000                                │   │
│  │  - WebSocket support for Socket.IO                         │   │
│  └────────────────────────────┬───────────────────────────────┘   │
│                                │                                     │
│                                ▼                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │          GUNICORN (WSGI HTTP Server)                        │   │
│  │  - Port: 127.0.0.1:5000 (localhost only)                   │   │
│  │  - Workers: 4 (gevent)                                      │   │
│  │  - Timeout: 300s                                            │   │
│  └────────────────────────────┬───────────────────────────────┘   │
│                                │                                     │
│                                ▼                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │           FLASK APPLICATION                                 │   │
│  │  - web_app_real.py                                          │   │
│  │  - Python 3.8+                                              │   │
│  │  - Virtual Environment: /opt/elite-rat/venv                │   │
│  │  - Flask-SocketIO for real-time                            │   │
│  └────────────────────────────┬───────────────────────────────┘   │
│                                │                                     │
│                                ▼                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │              SQLITE DATABASE                                │   │
│  │  Location: /opt/elite-rat/data/elite.db                    │   │
│  │  - Session data                                             │   │
│  │  - User data                                                │   │
│  │  - Application state                                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │              SYSTEMD SERVICE                                │   │
│  │  Name: elite-rat.service                                    │   │
│  │  - Auto-start on boot                                       │   │
│  │  - Auto-restart on failure                                  │   │
│  │  - Logging to journald                                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │              SUPPORTING SERVICES                            │   │
│  │  - Fail2ban: SSH brute force protection                    │   │
│  │  - Netdata: System monitoring (port 19999)                 │   │
│  │  - Cron: Automated backups                                  │   │
│  │  - Logrotate: Log management                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Request Flow Diagram

```
User Browser
    │
    │ 1. HTTPS Request
    │    https://your-domain.com
    ▼
┌────────────────┐
│   DNS Server   │ 2. Resolve domain to VPS IP
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  IONOS Cloud   │ 3. Check firewall rules
│   Firewall     │    Allow 443? → Yes
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  Ubuntu UFW    │ 4. Check local firewall
│   Firewall     │    Allow 443? → Yes
└───────┬────────┘
        │
        ▼
┌────────────────┐
│     Nginx      │ 5. SSL/TLS Termination
│   Port 443     │    Decrypt HTTPS
└───────┬────────┘
        │
        │ 6. Proxy to localhost:5000
        ▼
┌────────────────┐
│   Gunicorn     │ 7. Forward to worker
│  Port 5000     │    Select gevent worker
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  Flask App     │ 8. Process request
│  (Python)      │    - Route matching
└───────┬────────┘    - Auth check
        │             - Business logic
        │
        ▼
┌────────────────┐
│  SQLite DB     │ 9. Database operations
│  elite.db      │    - Query data
└───────┬────────┘    - Store session
        │
        │ 10. Generate response
        ▼
┌────────────────┐
│  Flask App     │ 11. Return HTML/JSON
└───────┬────────┘
        │
        ▼
┌────────────────┐
│   Gunicorn     │ 12. Send to Nginx
└───────┬────────┘
        │
        ▼
┌────────────────┐
│     Nginx      │ 13. Encrypt response
└───────┬────────┘     Add headers
        │
        │ 14. Send HTTPS response
        ▼
    User Browser
```

---

## 📁 File System Structure

```
/opt/elite-rat/                           # Main application directory
├── venv/                                 # Python virtual environment
│   ├── bin/
│   │   ├── python                        # Python interpreter
│   │   ├── pip                           # Package manager
│   │   └── gunicorn                      # WSGI server
│   └── lib/                              # Installed packages
│
├── Application/                          # Application modules
│   ├── stitch_cmd.py
│   ├── stitch_lib.py
│   └── ...
│
├── Core/                                 # Core functionality
│   ├── elite_executor.py
│   ├── crypto_system.py
│   └── ...
│
├── static/                               # Static files (CSS, JS)
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/                            # HTML templates
│   └── ...
│
├── data/                                 # Application data
│   └── elite.db                          # SQLite database
│
├── logs/                                 # Application logs
│   ├── access.log                        # Gunicorn access
│   ├── error.log                         # Gunicorn errors
│   └── elite-rat.log                     # Application logs
│
├── keys/                                 # Encryption keys
│   └── ...
│
├── ssl/                                  # SSL certificates (if self-signed)
│   ├── cert.pem
│   └── key.pem
│
├── generated/                            # Generated files
│   └── ...
│
├── web_app_real.py                       # Main application entry
├── config.yaml                           # Configuration file
├── requirements.txt                      # Python dependencies
├── .env                                  # Environment variables (SECRET!)
├── backup.sh                             # Backup script
└── update.sh                             # Update script

/etc/
├── nginx/
│   └── sites-available/
│       └── elite-rat                     # Nginx configuration
│
├── systemd/system/
│   └── elite-rat.service                 # Systemd service file
│
└── logrotate.d/
    └── elite-rat                         # Log rotation config

/var/log/
├── nginx/
│   ├── elite-rat-access.log             # Nginx access logs
│   └── elite-rat-error.log              # Nginx error logs
│
└── auth.log                              # SSH authentication logs

/opt/backups/                             # Backup storage
└── elite-rat-backup-YYYYMMDD_HHMMSS.tar.gz

/etc/letsencrypt/                         # Let's Encrypt certificates
└── live/
    └── your-domain.com/
        ├── fullchain.pem
        └── privkey.pem
```

---

## 🚀 Deployment Flow Diagram

```
START
  │
  ▼
┌─────────────────────────────────┐
│ 1. PREPARATION PHASE             │
│ ✓ Complete checklist            │
│ ✓ Verify VPS access             │
│ ✓ Configure DNS                 │
│ ✓ Prepare credentials           │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 2. SYSTEM SETUP PHASE           │
│ ✓ Update Ubuntu packages        │
│ ✓ Install dependencies          │
│ ✓ Configure firewall (UFW)      │
│ ✓ Create non-root user          │
│ ✓ Secure SSH                    │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 3. APPLICATION SETUP PHASE      │
│ ✓ Clone GitHub repository       │
│ ✓ Create virtual environment    │
│ ✓ Install Python packages       │
│ ✓ Configure .env file           │
│ ✓ Create directories            │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 4. WEB SERVER SETUP PHASE       │
│ ✓ Install Nginx                 │
│ ✓ Generate SSL certificate      │
│ ✓ Configure Nginx reverse proxy │
│ ✓ Test Nginx configuration      │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 5. SERVICE SETUP PHASE          │
│ ✓ Create systemd service        │
│ ✓ Enable auto-start             │
│ ✓ Start application             │
│ ✓ Verify service running        │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 6. MONITORING SETUP PHASE       │
│ ✓ Configure log rotation        │
│ ✓ Install monitoring tools      │
│ ✓ Setup fail2ban                │
│ ✓ Create backup script          │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 7. TESTING PHASE                │
│ ✓ Test HTTP/HTTPS access        │
│ ✓ Verify SSL certificate        │
│ ✓ Test login functionality      │
│ ✓ Check all services            │
│ ✓ Review logs                   │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 8. DEPLOYMENT COMPLETE! 🎉      │
│ Application is live and secure  │
└─────────────────────────────────┘
```

---

## 🔒 Security Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                              │
└────────────────────────────────────────────────────────────────┘

Layer 1: Network Security
├─ IONOS Cloud Firewall     → Block unwanted traffic at provider level
├─ UFW Firewall (Ubuntu)    → Block unwanted traffic at OS level
├─ Fail2ban                 → Ban IPs after failed login attempts
└─ SSH Key Authentication   → No password authentication

Layer 2: Transport Security
├─ TLS/SSL (Let's Encrypt)  → Encrypt all traffic
├─ HTTPS Only               → Redirect HTTP to HTTPS
├─ Strong Cipher Suites     → TLS 1.2+ only
└─ HSTS Headers             → Force HTTPS in browsers

Layer 3: Application Security
├─ Flask Session Management → Secure session cookies
├─ CSRF Protection          → Prevent cross-site attacks
├─ Rate Limiting            → Prevent brute force
├─ Input Validation         → Prevent injection attacks
└─ Authentication System    → Verify user identity

Layer 4: System Security
├─ Non-root User            → Don't run as root
├─ File Permissions         → Restrict file access
├─ Process Isolation        → Systemd security features
└─ Regular Updates          → Keep system patched

Layer 5: Data Security
├─ Encrypted Database       → Protect data at rest
├─ Secure Environment Vars  → .env file not in Git
├─ Log Encryption           → Protect log files
└─ Regular Backups          → Disaster recovery
```

---

## 🔄 Service Lifecycle

```
BOOT
  │
  ▼
┌──────────────────────┐
│  Systemd Init        │
│  - Read service file │
└─────────┬────────────┘
          │
          ▼
┌──────────────────────┐
│  Start elite-rat     │
│  - Load .env         │
│  - Set working dir   │
└─────────┬────────────┘
          │
          ▼
┌──────────────────────┐
│  Activate venv       │
│  - Python from venv  │
└─────────┬────────────┘
          │
          ▼
┌──────────────────────┐
│  Start Gunicorn      │
│  - Bind to 127.0.0.1:5000│
│  - Spawn 4 workers   │
└─────────┬────────────┘
          │
          ▼
┌──────────────────────┐
│  Load Flask App      │
│  - Import modules    │
│  - Connect to DB     │
│  - Initialize        │
└─────────┬────────────┘
          │
          ▼
┌──────────────────────┐
│  READY               │
│  - Listening on :5000│
│  - Accepting requests│
└──────────────────────┘
          │
          │ If crash
          ▼
┌──────────────────────┐
│  Auto Restart        │
│  - Wait 10 seconds   │
│  - Restart service   │
└─────────┬────────────┘
          │
          └──────────► Loop back to "Start elite-rat"
```

---

## 📊 Traffic Flow with WebSocket

```
Standard HTTP Request:
User → Nginx → Gunicorn → Flask → Response → Gunicorn → Nginx → User

WebSocket Connection (Socket.IO):
User → Nginx (Upgrade) → Gunicorn → Flask-SocketIO
                                          │
                                          ↓
                                     Persistent
                                     Connection
                                          │
                                          ↓
User ← Nginx ← Gunicorn ← Flask-SocketIO (Real-time updates)
```

---

## 🛠️ Maintenance Workflow

```
Daily:
├─ Check service status:     systemctl status elite-rat
├─ Review error logs:        journalctl -u elite-rat -n 50
├─ Check disk space:         df -h
└─ Monitor resource usage:   htop

Weekly:
├─ Review all logs:          tail -f /opt/elite-rat/logs/*
├─ Check backup success:     ls -lh /opt/backups/
├─ Verify SSL validity:      certbot certificates
└─ Review access patterns:   tail -f /var/log/nginx/elite-rat-access.log

Monthly:
├─ System updates:           apt update && apt upgrade
├─ Python package updates:   pip install -r requirements.txt --upgrade
├─ Restart services:         systemctl restart elite-rat nginx
├─ Test backup restoration:  Test restoring from backup
└─ Security audit:           Review fail2ban logs, check for updates
```

---

## 🔍 Troubleshooting Decision Tree

```
Problem?
   │
   ├─ Can't access website
   │   ├─ Is DNS working? → No → Fix DNS records
   │   │                   → Yes ↓
   │   ├─ Is firewall open? → No → sudo ufw allow 443/tcp
   │   │                    → Yes ↓
   │   └─ Is Nginx running? → No → systemctl start nginx
   │                        → Yes → Check application
   │
   ├─ Application not responding
   │   ├─ Is service running? → No → systemctl start elite-rat
   │   │                      → Yes ↓
   │   ├─ Check logs: journalctl -u elite-rat -n 50
   │   ├─ Port 5000 open? → No → Check if process crashed
   │   └─ Database locked? → Yes → Restart application
   │
   ├─ SSL Certificate error
   │   ├─ Expired? → Yes → certbot renew
   │   ├─ Wrong domain? → Yes → Reissue certificate
   │   └─ Not trusted? → Self-signed → Get Let's Encrypt cert
   │
   └─ Performance issues
       ├─ High CPU? → Increase workers or optimize code
       ├─ High Memory? → Reduce workers or add RAM
       ├─ Slow response? → Check database queries
       └─ High traffic? → Consider load balancer
```

---

## 🎯 Port Reference Table

| Port | Service | Purpose | External Access |
|------|---------|---------|-----------------|
| 22 | SSH | Server management | Yes (restricted) |
| 80 | Nginx | HTTP (redirects to 443) | Yes |
| 443 | Nginx | HTTPS (production) | Yes |
| 5000 | Gunicorn | Application server | No (localhost only) |
| 19999 | Netdata | Monitoring dashboard | Optional |

---

## 🔐 Credential Flow

```
User enters credentials
        │
        ▼
┌─────────────────┐
│ HTTPS (Nginx)   │ → Transport encryption
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Flask App       │ → Session validation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Check .env file │ → Compare with stored credentials
└────────┬────────┘
         │
         ├─ Match? → Yes → Create session → Grant access
         │
         └─ No? → Track failed attempt → Check lockout
                                              │
                                              ├─ < 5 attempts → Allow retry
                                              └─ ≥ 5 attempts → Lock for 30 min
```

---

## 📈 Scaling Considerations

```
Current Setup (Single Server):
┌─────────────────┐
│   Ubuntu VPS    │
│  - Nginx        │
│  - Gunicorn (4) │
│  - SQLite       │
└─────────────────┘
     │
     └→ Handles: ~1000 concurrent users

Future Scaling Options:

Option 1: Vertical Scaling
┌─────────────────┐
│  Bigger VPS     │
│  - Nginx        │
│  - Gunicorn (16)│ → More workers
│  - PostgreSQL   │ → Better database
└─────────────────┘
     │
     └→ Handles: ~5000 concurrent users

Option 2: Horizontal Scaling
┌──────────────┐
│ Load Balancer│
└──────┬───────┘
       │
       ├──→ ┌─────────────┐
       │    │  VPS 1      │
       │    └─────────────┘
       │
       ├──→ ┌─────────────┐
       │    │  VPS 2      │
       │    └─────────────┘
       │         │
       └──→ ┌─────────────┐
            │  VPS 3      │
            └─────────────┘
                 │
            ┌─────────────┐
            │ PostgreSQL  │ → Shared database
            └─────────────┘
```

---

## 🎨 Technology Stack Diagram

```
┌────────────────────────────────────────────────┐
│              PRESENTATION LAYER                 │
│  HTML, CSS, JavaScript                         │
│  Bootstrap, jQuery, Socket.IO Client           │
└───────────────────┬────────────────────────────┘
                    │
┌────────────────────────────────────────────────┐
│              APPLICATION LAYER                  │
│  Flask Framework                               │
│  - Routes & Controllers                        │
│  - Flask-SocketIO (WebSocket)                  │
│  - Flask-CORS                                  │
│  - Authentication & Authorization              │
└───────────────────┬────────────────────────────┘
                    │
┌────────────────────────────────────────────────┐
│              BUSINESS LOGIC LAYER              │
│  Python Modules                                │
│  - Elite Command Executor                      │
│  - Crypto System                               │
│  - Security Bypass                             │
│  - Payload Generator                           │
└───────────────────┬────────────────────────────┘
                    │
┌────────────────────────────────────────────────┐
│              DATA ACCESS LAYER                 │
│  SQLite Database                               │
│  - Sessions                                    │
│  - User data                                   │
│  - Application state                           │
└────────────────────────────────────────────────┘
```

---

## 📞 Quick Reference Commands

```bash
# Check all services
systemctl status elite-rat nginx fail2ban

# View logs in real-time
journalctl -u elite-rat -f

# Restart application
systemctl restart elite-rat

# Test Nginx config
nginx -t

# View active connections
netstat -tulpn | grep -E '(80|443|5000)'

# Check disk usage
df -h

# Check memory
free -h

# Health check
/opt/elite-rat/health_check.sh
```

---

**This architecture is designed for security, scalability, and maintainability!** 🚀
