"""
Enterprise Security Headers
Implements comprehensive security headers for production deployment
"""

from flask import Flask

def add_security_headers(app: Flask):
    """
    Add enterprise-grade security headers to all responses
    Follows OWASP recommendations and industry best practices
    """
    
    @app.after_request
    def set_security_headers(response):
        """Set comprehensive security headers on all responses"""
        
        # Prevent clickjacking attacks
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Enable XSS protection (legacy browsers)
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer policy - balance privacy and functionality
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions policy - restrict browser features
        response.headers['Permissions-Policy'] = (
            'geolocation=(), '
            'microphone=(), '
            'camera=(), '
            'payment=(), '
            'usb=(), '
            'magnetometer=(), '
            'gyroscope=(), '
            'accelerometer=()'
        )
        
        # Content Security Policy (CSP)
        # Strict policy for maximum security
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "upgrade-insecure-requests"
        ]
        response.headers['Content-Security-Policy'] = '; '.join(csp_directives)
        
        # Strict Transport Security (HSTS)
        # Force HTTPS for 1 year, include subdomains
        if app.config.get('SESSION_COOKIE_SECURE', False):
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains; preload'
            )
        
        # Expect-CT header for certificate transparency
        response.headers['Expect-CT'] = 'max-age=86400, enforce'
        
        # Cross-Origin policies
        response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
        response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'
        
        # Cache control for sensitive pages
        if request.endpoint and 'admin' in request.endpoint:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        # Server header - remove version info
        response.headers['Server'] = 'Oranolio'
        
        return response
    
    return app


def configure_session_security(app: Flask):
    """
    Configure secure session management
    """
    # Session cookie security
    app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JavaScript access
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
    
    # Session lifetime
    from datetime import timedelta
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    
    # Session regeneration on login
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    
    return app


def configure_csrf_protection(app: Flask):
    """
    Configure CSRF protection
    """
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = None  # No time limit
    app.config['WTF_CSRF_SSL_STRICT'] = True  # Strict HTTPS checking
    app.config['WTF_CSRF_METHODS'] = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    return app


def configure_rate_limiting(app: Flask):
    """
    Configure rate limiting for API endpoints
    """
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",
        strategy="fixed-window"
    )
    
    # Stricter limits for authentication endpoints
    @limiter.limit("5 per minute")
    def auth_rate_limit():
        pass
    
    return app, limiter


def init_security(app: Flask):
    """
    Initialize all security features
    One-stop function to secure the application
    """
    # Add security headers
    add_security_headers(app)
    
    # Configure session security
    configure_session_security(app)
    
    # Configure CSRF protection
    configure_csrf_protection(app)
    
    # Log security initialization
    app.logger.info('Enterprise security features initialized')
    app.logger.info('- Security headers enabled')
    app.logger.info('- Session security configured')
    app.logger.info('- CSRF protection enabled')
    
    return app


# Import for convenience
from flask import request
