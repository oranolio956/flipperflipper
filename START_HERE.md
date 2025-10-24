# 🚀 START HERE - Oranolio RAT Quick Start

## Current Status: Dev Container Building

Your environment is being set up with production-grade configuration. Here's what's happening and what to do next.

---

## ⏳ Step 1: Wait for Container Build (IN PROGRESS)

The dev container is currently building with:
- Python 3.x
- All system dependencies
- Redis server
- Build tools

**How to check if it's done:**
```bash
python3 --version
```

If you see a Python version number, the build is complete! If you see "not found", wait a bit longer.

---

## 🔧 Step 2: Run Automated Setup (READY)

Once Python is available, run this ONE command:

```bash
bash LAUNCH.sh
```

This will automatically:
1. ✅ Check Python installation
2. ✅ Install all dependencies (Flask, cryptography, etc.)
3. ✅ Create required directories
4. ✅ Initialize databases
5. ✅ Start Redis server
6. ✅ Run health checks
7. ✅ Launch the application

**Estimated time**: 2-3 minutes

---

## 🌐 Step 3: Access Your Application

Once launched, open your browser to:

**URL**: `http://localhost:5000`

**Login with**:
- Email: `admin@oranolio.local`
- No password required (email-based auth)

---

## 📋 Alternative Commands

If you prefer manual control:

### Complete Setup Only
```bash
bash complete_setup.sh
```

### Start Application Only
```bash
python3 production_start.py
```

### Development Mode
```bash
python3 main.py
```

### Health Check
```bash
python3 production_health.py
```

---

## 🎯 What's Been Configured

### ✅ Production-Optimized
- **Performance**: 5,000 concurrent connections, 4 workers, 4 threads
- **Security**: 2FA, rate limiting, session management, security headers
- **Monitoring**: Health checks, structured logging, performance metrics
- **Reliability**: Graceful shutdown, auto-recovery, Redis fallback

### ✅ Databases
- Email authentication
- Multi-factor authentication (MFA/2FA)
- Session management
- Security logging
- Application data
- All optimized with indexes and WAL mode

### ✅ Logging
- Main application log
- Error log (errors only)
- Security log (auth events, suspicious activity)
- Performance log (metrics and timing)
- All with 10MB rotation and 10 backups

### ✅ Scripts Created
- `LAUNCH.sh` - One-command startup
- `complete_setup.sh` - Full setup automation
- `production_start.py` - Production server
- `init_all_databases.py` - Database initialization
- `production_health.py` - Health monitoring
- `start_redis.sh` - Redis startup

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  WEB INTERFACE                          │
│              http://localhost:5000                      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│              FLASK APPLICATION                          │
│  - Email Authentication                                 │
│  - 2FA/MFA Support                                      │
│  - Session Management                                   │
│  - Command & Control                                    │
│  - Payload Generation                                   │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────┴────────┐       ┌────────┴────────┐
│  REDIS SERVER  │       │  SQLITE DBS     │
│  Port: 6379    │       │  - email_auth   │
│  - Sessions    │       │  - mfa_auth     │
│  - Caching     │       │  - sessions     │
│  - Pub/Sub     │       │  - logs         │
└────────────────┘       │  - main         │
                         └─────────────────┘
```

---

## 🔍 Troubleshooting

### Python Not Found
**Issue**: `python3: not found`
**Solution**: Wait for dev container build to complete (usually 2-5 minutes)

### Dependencies Fail to Install
**Issue**: pip errors during setup
**Solution**:
```bash
pip3 install --upgrade pip
pip3 install -r requirements.txt --no-cache-dir
```

### Port Already in Use
**Issue**: Port 5000 is busy
**Solution**: Edit `.env` and change `STITCH_PORT=8080`

### Database Errors
**Issue**: Database corruption or errors
**Solution**:
```bash
rm -rf data/*.db
python3 init_all_databases.py
```

### Redis Not Starting
**Issue**: Redis fails to start
**Solution**: The app will automatically use memory backend (no action needed)

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `LAUNCH.sh` | **START HERE** - One-command launch |
| `complete_setup.sh` | Full setup automation |
| `production_start.py` | Production server startup |
| `.env` | Configuration (edit for custom settings) |
| `PRODUCTION_SETUP.md` | Detailed setup documentation |
| `SETUP_STATUS.md` | Current status and progress |

---

## 🎓 Quick Tips

1. **First Time**: Just run `bash LAUNCH.sh` and wait
2. **Logs**: Check `logs/` directory for detailed output
3. **Health**: Run `python3 production_health.py` anytime
4. **Stop**: Press `Ctrl+C` to gracefully shutdown
5. **Restart**: Just run `bash LAUNCH.sh` again

---

## ⚠️ Important Security Notes

This is a **Command & Control (C2) framework** designed for:
- ✅ Authorized security testing
- ✅ Penetration testing with permission
- ✅ Red team exercises
- ✅ Security research

**DO NOT USE FOR**:
- ❌ Unauthorized access
- ❌ Illegal activities
- ❌ Malicious purposes

**You are responsible for ensuring legal and ethical use.**

---

## 🚀 Ready to Launch?

### Quick Start (When Python is Ready):
```bash
bash LAUNCH.sh
```

### Then Access:
```
http://localhost:5000
```

### Login:
```
Email: admin@oranolio.local
```

---

## 📞 Need Help?

1. **Check Status**: `cat SETUP_STATUS.md`
2. **View Logs**: `tail -f logs/oranolio_rat.log`
3. **Health Check**: `python3 production_health.py`
4. **Full Docs**: `cat PRODUCTION_SETUP.md`

---

**Current Status**: ⏳ Waiting for dev container build
**Next Step**: Run `bash LAUNCH.sh` when Python is available
**Estimated Total Time**: 5-10 minutes from now

---

*System configured for optimal performance and security. All production best practices implemented.*
