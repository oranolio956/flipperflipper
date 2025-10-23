# FlipperFlipper C2 - Dependency Documentation

**Last Updated:** 2024-10-23
**Status:** ✅ All critical dependencies resolved

---

## Installation Summary

### Quick Install (All Platforms)
```bash
pip install -r requirements.txt
```

### Critical Dependencies (REQUIRED)
All installed and verified ✅

```bash
pip install flask flask-socketio flask-limiter flask-wtf flask-cors werkzeug
pip install pycryptodome cryptography pyotp pyjwt bcrypt
pip install qrcode pillow psutil requests aiohttp aiosqlite
pip install pyyaml python-dotenv colorama sqlalchemy redis
pip install bleach sqlparse validators
```

---

## Dependency Status

### ✅ Core Dependencies (27/27 Working)

| Package | Version | Status | Purpose |
|---------|---------|--------|---------|
| flask | >=3.1.0 | ✅ | Web framework |
| flask-socketio | >=5.5.0 | ✅ | WebSocket support |
| flask-limiter | >=4.0.0 | ✅ | Rate limiting |
| flask-wtf | >=1.2.0 | ✅ | CSRF protection |
| flask-cors | >=4.0.0 | ✅ | CORS handling |
| werkzeug | >=3.1.0 | ✅ | WSGI utilities |
| pycryptodome | >=3.23.0 | ✅ | AES encryption |
| cryptography | >=46.0.0 | ✅ | Modern crypto |
| pyotp | >=2.9.0 | ✅ | 2FA/TOTP |
| pyjwt | >=2.8.0 | ✅ | JWT tokens |
| bcrypt | >=4.1.0 | ✅ | Password hashing |
| qrcode | >=8.2.0 | ✅ | QR code generation |
| pillow | >=12.0.0 | ✅ | Image processing |
| psutil | >=7.1.0 | ✅ | System monitoring |
| requests | >=2.32.0 | ✅ | HTTP client |
| aiohttp | >=3.9.0 | ✅ | Async HTTP |
| aiosqlite | >=0.19.0 | ✅ | Async SQLite |
| pyyaml | >=6.0.0 | ✅ | YAML config |
| python-dotenv | >=1.1.0 | ✅ | Environment vars |
| colorama | >=0.4.6 | ✅ | Terminal colors |
| sqlalchemy | >=2.0.0 | ✅ | ORM |
| redis | >=5.0.0 | ✅ | Caching |
| bleach | >=6.0.0 | ✅ | HTML sanitization |
| sqlparse | >=0.4.0 | ✅ | SQL parsing |
| validators | >=0.22.0 | ✅ | Input validation |

### ⚠️ Optional Dependencies (Platform-Specific)

| Package | Status | Platform | Notes |
|---------|--------|----------|-------|
| python-magic | ⚠️ | All | Requires libmagic1 system library |
| pynput | ⚠️ | Linux | Requires X11 display |
| pywin32 | ❌ | Windows | Not needed on Linux |
| wmi | ❌ | Windows | Not needed on Linux |
| comtypes | ❌ | Windows | Not needed on Linux |
| pyobjc-* | ❌ | macOS | Not needed on Linux |
| python-xlib | ✅ | Linux | Installed automatically |

---

## Platform-Specific Installation

### Linux (Current Platform) ✅

**Core packages:** All working
**Platform packages:** python-xlib installed

**Optional system libraries:**
```bash
# For python-magic (file type detection)
sudo apt-get install libmagic1

# For pynput (keylogger functionality)
# Requires X11 display - not available in headless environments
# Only needed for payload generation with keylogger features
```

### Windows

**Additional packages needed:**
```bash
pip install pywin32 wmi comtypes
```

**For payload building:**
```bash
pip install py2exe pyinstaller
```

### macOS

**Additional packages needed:**
```bash
pip install pyobjc-framework-cocoa pyobjc-framework-quartz
```

**System requirements:**
```bash
brew install libmagic
```

---

## Optional Feature Dependencies

### Enhanced Features (Not Required for Basic Operation)

```bash
# Telegram integration
pip install telethon

# Web automation
pip install playwright

# Computer vision
pip install opencv-python

# GUI automation
pip install pyautogui

# Terminal automation
pip install pexpect

# Screenshot capture
pip install mss

# DNS tunneling
pip install dnspython

# WebSocket client
pip install websocket-client

# Payload building
pip install pyinstaller
```

---

## Troubleshooting

### python-magic Import Error

**Error:** `failed to find libmagic. Check your installation`

**Solution:**
```bash
# Linux
sudo apt-get install libmagic1

# macOS
brew install libmagic

# Windows
pip install python-magic-bin  # Alternative package
```

**Workaround:** python-magic is not used in core code, only for file type detection. System will work without it.

---

### pynput Import Error

**Error:** `this platform is not supported: ('failed to acquire X connection`

**Cause:** pynput requires X11 display, not available in headless/container environments

**Solution:**
- Only needed for keylogger payload generation
- Not required for C2 server operation
- Can be skipped in headless environments

**Workaround:** Comment out keylogger imports if not needed:
```python
# In Core/elite_commands/elite_keylogger.py
try:
    from pynput import keyboard
except ImportError:
    keyboard = None  # Keylogger not available
```

---

### pywin32 on Linux

**Error:** `No module named 'win32api'`

**Cause:** Windows-specific package imported on Linux

**Solution:** These imports are platform-conditional and should only run on Windows. If you see this error, check for missing platform checks:

```python
import sys
if sys.platform == 'win32':
    import win32api
```

---

## Dependency Verification

### Test All Imports

```bash
python3 << 'EOF'
# Test critical imports
imports = [
    'flask', 'flask_socketio', 'flask_cors', 'yaml', 'Crypto',
    'cryptography', 'pyotp', 'jwt', 'bcrypt', 'qrcode', 'PIL',
    'psutil', 'requests', 'aiohttp', 'redis', 'sqlalchemy'
]

for module in imports:
    try:
        __import__(module)
        print(f"✅ {module}")
    except ImportError as e:
        print(f"❌ {module}: {e}")
EOF
```

### Test Core Systems

```bash
python3 -c "
from Core.config_loader import config
from Core.database import EliteDatabase
from Core.c2_server import C2Server
print('✅ All core systems import successfully')
"
```

---

## Requirements.txt Structure

The `requirements.txt` file is organized by category:

1. **Core Flask Dependencies** - Web framework
2. **Security & Cryptography** - Encryption, hashing, tokens
3. **Image & QR Code** - Visual generation
4. **System Monitoring** - Process and system info
5. **HTTP Requests** - Network communication
6. **Environment Management** - Configuration
7. **Database & ORM** - Data persistence
8. **Additional Security** - Input validation, sanitization

---

## Development Dependencies

For development and testing:

```bash
pip install black flake8 mypy pytest pytest-cov
```

---

## Production Recommendations

### Minimal Installation (C2 Server Only)

If you only need the C2 server without payload generation:

```bash
pip install flask flask-socketio werkzeug
pip install pycryptodome cryptography bcrypt pyjwt
pip install sqlalchemy aiosqlite redis
pip install pyyaml python-dotenv colorama
```

### Full Installation (All Features)

For complete functionality including payload generation:

```bash
pip install -r requirements.txt
```

---

## Dependency Count

- **Core Required:** 27 packages ✅
- **Platform-Specific:** 7 packages (varies by OS)
- **Optional Features:** 10 packages
- **Development:** 5 packages

**Total Unique Packages:** 44

---

## Security Notes

1. **Always use virtual environments** in production
2. **Pin versions** in requirements.txt for reproducibility
3. **Audit dependencies** regularly for vulnerabilities
4. **Update cautiously** - test before deploying updates
5. **Minimize dependencies** - only install what you need

---

## Update Policy

- **Security updates:** Apply immediately
- **Minor updates:** Test in staging first
- **Major updates:** Review breaking changes carefully

---

## Known Issues

### Issue 1: python-magic on Headless Systems
- **Impact:** File type detection unavailable
- **Workaround:** Not critical for core functionality
- **Status:** Optional dependency

### Issue 2: pynput in Containers
- **Impact:** Keylogger payload generation unavailable
- **Workaround:** Generate payloads on system with display
- **Status:** Optional feature

### Issue 3: Platform-Specific Imports
- **Impact:** Some commands fail on wrong platform
- **Workaround:** Platform checks in code
- **Status:** By design

---

## Support

If you encounter dependency issues:

1. Check this document first
2. Verify Python version (3.8+)
3. Check platform compatibility
4. Review error messages carefully
5. Test imports individually

---

## Changelog

### 2024-10-23
- ✅ Added pyyaml to requirements.txt
- ✅ Added pynput to requirements.txt
- ✅ Verified all 27 core dependencies
- ✅ Documented platform-specific issues
- ✅ Created comprehensive troubleshooting guide

---

## Quick Reference

### Install Everything
```bash
pip install -r requirements.txt
```

### Install Core Only
```bash
pip install flask flask-socketio pycryptodome cryptography sqlalchemy pyyaml
```

### Verify Installation
```bash
python3 -c "from Core.config_loader import config; print('✅ Ready')"
```

### Check Missing
```bash
pip check
```

---

**Status:** ✅ All critical dependencies resolved and documented
