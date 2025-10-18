#!/usr/bin/env python3
"""
SSL/TLS Certificate Generation Utility
Generates self-signed certificates for HTTPS support with configurable OPSEC-friendly fields
"""
import os
import subprocess
import sys
from pathlib import Path

def generate_self_signed_cert(cert_dir="certs"):
    """
    Generate a self-signed SSL certificate for development/testing.
    
    Uses environment variables for certificate fields (OPSEC-friendly):
    - STITCH_SSL_COUNTRY: Country code (default: US)
    - STITCH_SSL_STATE: State/Province (default: State)
    - STITCH_SSL_CITY: City/Locality (default: City)
    - STITCH_SSL_ORG: Organization name (default: Web Services)
    - STITCH_SSL_CN: Common Name (default: localhost)
    
    Args:
        cert_dir: Directory to store certificates (default: 'certs')
    
    Returns:
        tuple: (cert_path, key_path) or (None, None) if generation fails
    """
    cert_path = os.path.join(cert_dir, "cert.pem")
    key_path = os.path.join(cert_dir, "key.pem")
    
    if os.path.exists(cert_path) and os.path.exists(key_path):
        print(f"✓ SSL: Using existing certificates in {cert_dir}/")
        return cert_path, key_path
    
    os.makedirs(cert_dir, exist_ok=True)
    
    # Get certificate subject fields from environment (neutral defaults for OPSEC)
    cert_country = os.getenv('STITCH_SSL_COUNTRY', 'US')
    cert_state = os.getenv('STITCH_SSL_STATE', 'State')
    cert_city = os.getenv('STITCH_SSL_CITY', 'City')
    cert_org = os.getenv('STITCH_SSL_ORG', 'Web Services')
    cert_cn = os.getenv('STITCH_SSL_CN', 'localhost')
    
    subject_string = f'/C={cert_country}/ST={cert_state}/L={cert_city}/O={cert_org}/CN={cert_cn}'
    
    print("🔐 Generating self-signed SSL certificate...")
    print("   This may take a moment...")
    
    try:
        subprocess.run([
            'openssl', 'req',
            '-x509',
            '-newkey', 'rsa:4096',
            '-nodes',
            '-out', cert_path,
            '-keyout', key_path,
            '-days', '365',
            '-subj', subject_string
        ], check=True, capture_output=True, text=True)
        
        print(f"✓ SSL: Self-signed certificate generated")
        print(f"   Certificate: {cert_path}")
        print(f"   Private key: {key_path}")
        print(f"   Valid for: 365 days")
        print("\n⚠️  WARNING: Self-signed certificates are NOT TRUSTED by browsers!")
        print("   For production, use certificates from a trusted CA (Let's Encrypt, etc.)")
        print()
        
        return cert_path, key_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ SSL: Failed to generate certificate: {e.stderr}")
        return None, None
    except FileNotFoundError:
        print("❌ SSL: OpenSSL not found. Install openssl to use HTTPS.")
        return None, None

def get_ssl_context():
    """
    Get SSL context for Flask application based on environment configuration.
    
    Returns:
        tuple: (cert_path, key_path) for SSL or (None, None) for HTTP
    """
    https_enabled = os.getenv('STITCH_ENABLE_HTTPS', 'false').lower() in ('true', '1', 'yes')
    
    if not https_enabled:
        return None, None
    
    custom_cert = os.getenv('STITCH_SSL_CERT')
    custom_key = os.getenv('STITCH_SSL_KEY')
    
    if custom_cert and custom_key:
        if os.path.exists(custom_cert) and os.path.exists(custom_key):
            print(f"✓ SSL: Using custom certificates")
            print(f"   Certificate: {custom_cert}")
            print(f"   Private key: {custom_key}\n")
            return custom_cert, custom_key
        else:
            print("❌ SSL: Custom certificate files not found!")
            print(f"   STITCH_SSL_CERT={custom_cert} (exists: {os.path.exists(custom_cert)})")
            print(f"   STITCH_SSL_KEY={custom_key} (exists: {os.path.exists(custom_key)})")
            print("   Falling back to auto-generated certificate...\n")
    
    return generate_self_signed_cert()

if __name__ == '__main__':
    print("SSL Certificate Generator\n")
    cert, key = generate_self_signed_cert()
    
    if cert and key:
        print("\n✓ Certificates generated successfully!")
        print("\nTo use HTTPS with Stitch:")
        print("  1. Set: export STITCH_ENABLE_HTTPS=true")
        print("  2. Run: python3 web_app_real.py")
        print("\nOr use custom certificates:")
        print("  export STITCH_ENABLE_HTTPS=true")
        print("  export STITCH_SSL_CERT=/path/to/your/cert.pem")
        print("  export STITCH_SSL_KEY=/path/to/your/key.pem")
    else:
        print("\n❌ Certificate generation failed!")
        sys.exit(1)
