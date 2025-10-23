# Stitch Elite RAT System - Replit Setup Guide

## 🚀 Quick Start

1. **Clone/Import** this repository into Replit
2. **Run Setup**: `python setup_replit.py`
3. **Start System**: `python main.py`
4. **Access Web Interface**: Click the "Open in new tab" button or visit the provided URL

## 🌐 Access Information

- **Web Interface**: Available on the Replit webview
- **Username**: `admin`
- **Password**: `SuperSecurePass123!`
- **Port**: 5000 (automatically configured)

## 📋 Features Available

### Core Features
- ✅ Web-based Command & Control Interface
- ✅ Real-time Payload Management
- ✅ Multi-Factor Authentication (MFA)
- ✅ Webhook Authentication System
- ✅ Advanced Security Features
- ✅ Session Management
- ✅ Rate Limiting
- ✅ CSRF Protection

### Backend Services
- ✅ Stitch Server Integration
- ✅ Native Payload Generation
- ✅ Cross-platform Support
- ✅ Database Management
- ✅ Logging System

## 🔧 System Requirements

### Dependencies (Auto-installed)
- Python 3.11+
- Flask & Flask-SocketIO
- Cryptography & Security Libraries
- Database Support (SQLite)
- Redis (Memory-based)
- Telegram Integration
- Web Scraping (Playwright)

### Replit Configuration
- **Language**: Python 3
- **Runtime**: Python 3.11
- **Port**: 5000
- **Environment**: Development

## 📁 Project Structure

```
/
├── main.py                 # Main entry point
├── setup_replit.py        # Replit setup script
├── web_app_real.py        # Web interface
├── Application/           # Core application modules
├── Core/                  # Elite command system
├── Configuration/         # System configuration
├── templates/             # Web templates
├── static/               # Static web assets
├── requirements.txt       # Python dependencies
├── .replit               # Replit configuration
└── replit.nix           # Nix system dependencies
```

## 🛠️ Manual Setup (if needed)

If the automatic setup fails, run these commands:

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Setup databases
python create_mfa_tables.py
python create_email_tables.py

# Start the system
python main.py
```

## 🔒 Security Features

### Authentication
- Multi-Factor Authentication (MFA)
- Webhook-based Authentication
- Session Management
- Rate Limiting
- CSRF Protection

### Data Protection
- Encrypted Communications
- Secure Password Hashing
- Input Validation
- SQL Injection Prevention
- XSS Protection

## 📊 Monitoring & Logging

- Real-time System Monitoring
- Comprehensive Logging
- Performance Metrics
- Error Tracking
- Security Auditing

## 🚨 Troubleshooting

### Common Issues

1. **Port Already in Use**
   - The system automatically handles this
   - If issues persist, restart the Replit container

2. **Import Errors**
   - Run `python setup_replit.py` again
   - Check that all dependencies are installed

3. **Database Errors**
   - Run the database setup scripts manually
   - Check file permissions

4. **Web Interface Not Loading**
   - Wait a few seconds for startup
   - Check the console for error messages
   - Try refreshing the page

### Debug Mode

To enable debug mode, set environment variables:
```bash
export STITCH_DEBUG=true
export FLASK_DEBUG=true
```

## 📞 Support

If you encounter issues:

1. Check the console output for error messages
2. Verify all dependencies are installed
3. Ensure proper file permissions
4. Check Replit logs for system errors

## ⚠️ Important Notes

- This system is for educational and testing purposes only
- Use only in authorized environments
- Follow all applicable laws and regulations
- Keep credentials secure
- Regular security updates recommended

## 🔄 Updates

To update the system:
1. Pull latest changes from repository
2. Run `python setup_replit.py` again
3. Restart the system with `python main.py`

---

**Ready to go!** 🎉 Your Stitch Elite RAT System is now configured for Replit.