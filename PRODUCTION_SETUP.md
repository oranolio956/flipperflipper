# Oranolio RAT - Production Setup Guide

## 🚀 Quick Start

The system has been configured for optimal performance and security. Follow these steps to launch:

### 1. Wait for Dev Container Build

The dev container is currently building with all required dependencies. This includes:
- Python 3.x
- All system libraries (SSL, FFI, libmagic)
- Redis server
- Build tools

**Status**: The container will automatically rebuild. Wait for it to complete.

### 2. Run Complete Setup

Once Python is available, run the automated setup script:

```bash
bash complete_setup.sh
```

This script will:
- ✅ Verify Python installation
- ✅ Install all Python dependencies from requirements.txt
- ✅ Create required directories (data, logs, uploads, etc.)
- ✅ Initialize all databases with optimized schemas
- ✅ Start Redis server (or configure memory backend)
- ✅ Run health checks
- ✅ Create default admin user

### 3. Start the Application

After setup completes, start the application:

```bash
python3 production_start.py
```

Or for development mode with auto-reload:

```bash
python3 main.py
```

### 4. Access the Web Interface

The application will be available at:
- **URL**: `http://localhost:5000`
- **Default Admin Email**: `admin@oranolio.local`

## 📋 What's Been Configured

### Production-Grade Features

1. **Optimized Dockerfile**
   - Minimal base image
   - Efficient layer caching
   - All required system dependencies

2. **Environment Configuration** (`.env`)
   - Security best practices
   - Performance optimizations
   - Rate limiting configured
   - Session management settings

3. **Database System** (`init_all_databases.py`)
   - Email authentication database
   - MFA/2FA database
   - Session management database
   - Logging database
   - Main application database
   - Optimized with indexes and WAL mode

4. **Logging System** (`production_logging.py`)
   - Structured JSON logging
   - Rotating log files (10MB max, 10 backups)
   - Separate logs for: app, errors, security, performance
   - Colored console output
   - Third-party logger suppression

5. **Health Monitoring** (`production_health.py`)
   - Database health checks
   - System resource monitoring (CPU, memory, disk)
   - Directory verification
   - Redis connection status
   - Comprehensive health reports

6. **Startup System** (`production_start.py`)
   - Graceful shutdown handling
   - Automatic directory creation
   - Database initialization
   - Redis startup
   - Health checks before launch
   - Signal handling (SIGINT, SIGTERM)

7. **Redis Configuration** (`start_redis.sh`)
   - Optimized for session management
   - 256MB memory limit
   - LRU eviction policy
   - Persistence enabled
   - Automatic fallback to memory backend

## 🔧 Configuration Files

### `.env` - Environment Variables
All configuration is centralized in the `.env` file:
- Application settings
- Server configuration
- Security settings
- Authentication parameters
- Rate limiting
- Database paths
- Logging configuration
- Performance tuning

### Key Settings

```bash
# Server
STITCH_HOST=0.0.0.0
STITCH_PORT=5000

# Security
MAX_LOGIN_ATTEMPTS=5
SESSION_TIMEOUT=3600
ENABLE_2FA=true

# Performance
MAX_CONNECTIONS=5000
GUNICORN_WORKERS=4
GUNICORN_THREADS=4

# Rate Limiting
COMMANDS_PER_MINUTE=120
API_POLLING_PER_HOUR=2000
```

## 📊 Performance Optimizations

### Database
- **WAL Mode**: Better concurrency
- **Cache Size**: 10,000 pages
- **Page Size**: 4KB (optimal for most workloads)
- **Indexes**: All critical queries indexed
- **ANALYZE**: Query optimizer statistics updated

### Application
- **Threading**: Multi-threaded request handling
- **Connection Pooling**: Redis connection pooling
- **Rate Limiting**: Prevents resource exhaustion
- **Caching**: Redis-backed session caching

### Logging
- **Async Logging**: Non-blocking log writes
- **Log Rotation**: Prevents disk space issues
- **Structured Logs**: JSON format for easy parsing
- **Log Levels**: Configurable verbosity

## 🔒 Security Features

### Authentication
- Email-based authentication (zero-config)
- Multi-factor authentication (TOTP)
- Session management with device fingerprinting
- Login attempt limiting
- Account lockout protection

### Security Headers
- HSTS enabled
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection enabled
- CSP configured

### Input Validation
- Multi-layer validation
- SQL injection prevention
- XSS protection
- CSRF protection
- File upload restrictions

## 📈 Monitoring

### Health Checks

Run manual health check:
```bash
python3 production_health.py
```

Health check includes:
- Database connectivity and size
- System resources (CPU, memory, disk)
- Directory permissions
- Redis status
- Overall system health

### Logs

Log files are located in the `logs/` directory:
- `oranolio_rat.log` - Main application log
- `oranolio_rat_errors.log` - Errors only
- `oranolio_rat_security.log` - Security events
- `oranolio_rat_performance.log` - Performance metrics

View logs in real-time:
```bash
tail -f logs/oranolio_rat.log
```

## 🛠️ Troubleshooting

### Python Not Found
Wait for the dev container to finish building. The Dockerfile installs Python 3.

### Dependencies Installation Fails
```bash
pip3 install --upgrade pip
pip3 install -r requirements.txt --no-cache-dir
```

### Database Errors
Reinitialize databases:
```bash
rm -rf data/*.db
python3 init_all_databases.py
```

### Redis Not Starting
The application will automatically fall back to memory-based sessions if Redis is unavailable.

### Port Already in Use
Change the port in `.env`:
```bash
STITCH_PORT=8080
```

## 📦 Directory Structure

```
flipperflipper/
├── .devcontainer/          # Dev container configuration
│   ├── Dockerfile          # Optimized container image
│   └── devcontainer.json   # Container settings
├── data/                   # SQLite databases
├── logs/                   # Application logs
├── uploads/                # Uploaded files
├── downloads/              # Downloaded files
├── backups/                # Database backups
├── payloads/               # Generated payloads
├── .env                    # Environment configuration
├── requirements.txt        # Python dependencies
├── production_start.py     # Production startup script
├── init_all_databases.py   # Database initialization
├── production_health.py    # Health check system
├── production_logging.py   # Logging configuration
├── start_redis.sh          # Redis startup script
└── complete_setup.sh       # Automated setup script
```

## 🎯 Next Steps

1. **Wait for container build** to complete
2. **Run setup script**: `bash complete_setup.sh`
3. **Start application**: `python3 production_start.py`
4. **Access web interface**: `http://localhost:5000`
5. **Login with**: `admin@oranolio.local`

## 📞 Support

For issues or questions:
1. Check logs in `logs/` directory
2. Run health check: `python3 production_health.py`
3. Review this documentation
4. Check the main README.md for application features

## ⚠️ Important Notes

- **Security**: This is a C2 framework. Use only for authorized security testing.
- **Legal**: Ensure compliance with all applicable laws and regulations.
- **Ethics**: Only use on systems you own or have explicit permission to test.
- **Responsibility**: Users are solely responsible for their use of this software.

---

**System Status**: Ready for deployment after container build completes.
**Configuration**: Production-optimized for performance and security.
**Monitoring**: Comprehensive health checks and logging enabled.
