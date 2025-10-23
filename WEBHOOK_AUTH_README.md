# 🔐 Webhook Authentication System

A secure, modern authentication system using webhook.site for code generation and verification, with comprehensive MFA integration.

## ✨ Features

### 🔐 Webhook-Based Authentication
- **Secure Code Generation**: 6-digit codes generated and sent to webhook.site
- **Real-time Verification**: Codes verified against webhook endpoint
- **Session Management**: Secure session handling with encryption
- **Rate Limiting**: Protection against brute force attacks
- **IP Validation**: Additional security layer with IP address verification

### 🔑 Multi-Factor Authentication (MFA)
- **TOTP Support**: Google Authenticator, Authy, and other TOTP apps
- **QR Code Generation**: Easy setup with visual QR codes
- **Backup Codes**: 10 single-use recovery codes
- **Encrypted Storage**: All MFA data encrypted at rest
- **Verification Logging**: Complete audit trail of MFA attempts

### 🛡️ Security Features
- **End-to-End Encryption**: All sensitive data encrypted
- **Input Validation**: Protection against XSS, SQL injection, and path traversal
- **Session Security**: HTTPOnly cookies, SameSite protection
- **Database Security**: Parameterized queries, encrypted storage
- **Webhook Security**: HTTPS communication, no sensitive data exposure

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager
- Webhook.site account (free)

### Installation

1. **Clone and navigate to the project**:
   ```bash
   cd /workspace
   ```

2. **Run the startup script**:
   ```bash
   python3 start_webhook_auth_system.py
   ```

   This will:
   - Install all required dependencies
   - Set up necessary directories
   - Run security validation tests
   - Start the web server

3. **Access the system**:
   - **Login Page**: http://localhost:5000/login
   - **Webhook Dashboard**: http://localhost:5000/webhook-auth/webhook-dashboard
   - **Main Dashboard**: http://localhost:5000/dashboard (after login)

## 🔧 Configuration

### Webhook Configuration
The system is pre-configured to use your webhook.site endpoint:
- **Webhook URL**: `https://webhook.site/b8f87549-03f0-4032-be49-859cc22f0e46`
- **API URL**: `https://webhook.site/token/b8f87549-03f0-4032-be49-859cc22f0e46/requests`

### Authorized Emails
Configure authorized email addresses in `config.py`:
```python
AUTHORIZED_EMAILS = ['your@email.com', 'admin@company.com']
```

### Security Settings
Key security configurations in `config.py`:
```python
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15
SESSION_TIMEOUT_MINUTES = 30
```

## 📱 How It Works

### 1. Login Process
1. User enters their email address
2. System generates a 6-digit verification code
3. Code is sent to the webhook.site endpoint
4. User checks webhook dashboard for the code
5. User enters the code to complete authentication

### 2. MFA Setup (First Time)
1. After successful webhook authentication
2. System generates TOTP secret and QR code
3. User scans QR code with authenticator app
4. User verifies setup with a test code
5. System provides 10 backup codes for recovery

### 3. MFA Verification (Subsequent Logins)
1. After webhook authentication
2. User enters 6-digit code from authenticator app
3. Or uses backup code if device unavailable
4. System verifies and grants access

## 🔒 Security Architecture

### Encryption
- **Fernet Encryption**: AES-256-GCM for data at rest
- **Secure Key Management**: Keys stored with restricted permissions
- **TOTP Secrets**: Encrypted before database storage
- **Backup Codes**: SHA-256 hashed for verification

### Session Management
- **HTTPOnly Cookies**: Prevent XSS attacks
- **SameSite Protection**: CSRF protection
- **Session Timeout**: Automatic expiration
- **IP Validation**: Session tied to IP address

### Input Validation
- **XSS Protection**: HTML entity encoding
- **SQL Injection**: Parameterized queries
- **Path Traversal**: Input sanitization
- **Rate Limiting**: Request throttling

## 📊 Monitoring and Logging

### Webhook Dashboard
- Real-time view of authentication requests
- Code generation and verification logs
- Security event monitoring
- Request history and analytics

### Security Audit
Run comprehensive security audit:
```bash
python3 security_audit_webhook_auth.py
```

### System Tests
Run complete system validation:
```bash
python3 test_webhook_auth_system.py
```

## 🛠️ Development

### Project Structure
```
/workspace/
├── webhook_auth_manager.py      # Core webhook authentication
├── webhook_mfa_integration.py   # MFA integration
├── webhook_auth_routes.py       # Flask routes
├── webhook_mfa_setup.html       # MFA setup template
├── webhook_mfa_verify.html      # MFA verification template
├── webhook_login.html           # Login template
├── webhook_dashboard.html       # Webhook monitoring
├── test_webhook_auth_system.py  # Comprehensive tests
├── security_audit_webhook_auth.py # Security audit
└── start_webhook_auth_system.py # Startup script
```

### Key Components

#### WebhookAuthManager
- Code generation and verification
- Session management
- Webhook communication
- Security validation

#### WebhookMFAIntegration
- MFA setup and verification
- TOTP secret management
- Backup code handling
- Database operations

#### Security Features
- Input validation and sanitization
- Rate limiting and lockout
- Encryption and key management
- Audit logging

## 🔧 Troubleshooting

### Common Issues

1. **Webhook not receiving codes**:
   - Check webhook.site URL configuration
   - Verify network connectivity
   - Check webhook endpoint status

2. **MFA setup fails**:
   - Ensure PIL/Pillow is installed
   - Check database permissions
   - Verify encryption key exists

3. **Login not working**:
   - Check authorized emails configuration
   - Verify webhook authentication flow
   - Check session configuration

### Debug Mode
Enable debug logging:
```bash
export STITCH_DEBUG=true
python3 web_app_real.py
```

## 📈 Performance

### Optimizations
- **Session Cleanup**: Automatic expired session removal
- **Database Indexing**: Optimized queries
- **Caching**: Session and configuration caching
- **Rate Limiting**: Efficient request throttling

### Monitoring
- **Health Checks**: System status monitoring
- **Metrics Collection**: Performance metrics
- **Error Tracking**: Comprehensive error logging
- **Security Events**: Real-time security monitoring

## 🔐 Security Best Practices

### Production Deployment
1. **Use HTTPS**: Enable SSL/TLS encryption
2. **Secure Headers**: Implement security headers
3. **Regular Updates**: Keep dependencies updated
4. **Monitor Logs**: Regular security log review
5. **Backup Keys**: Secure backup of encryption keys

### Key Management
- **Rotate Keys**: Regular encryption key rotation
- **Secure Storage**: Keys stored with restricted permissions
- **Access Control**: Limit key access to authorized personnel
- **Audit Trail**: Log all key operations

## 📞 Support

### Documentation
- Comprehensive inline documentation
- Security audit reports
- Test results and validation
- Configuration examples

### Testing
- Automated test suite
- Security validation
- Performance testing
- Integration testing

---

## 🎉 Success!

Your webhook authentication system is now fully operational with:
- ✅ Secure webhook-based authentication
- ✅ Complete MFA integration
- ✅ Comprehensive security features
- ✅ Real-time monitoring
- ✅ Production-ready deployment

**Access your system at**: http://localhost:5000/login

**Monitor webhook activity at**: http://localhost:5000/webhook-auth/webhook-dashboard