#!/usr/bin/env python3
"""
SSL Certificate Utilities for Stitch RAT
Handles SSL certificate generation and management
"""

import os
import ssl
import socket
from pathlib import Path
from datetime import datetime, timedelta
try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️  cryptography library not available. SSL auto-generation disabled.")

def get_ssl_context(cert_dir="certs", cert_file="cert.pem", key_file="key.pem", 
                   auto_generate=True, cn="localhost"):
    """
    Get SSL context for Flask application
    
    Args:
        cert_dir: Directory to store certificates
        cert_file: Certificate filename
        key_file: Private key filename
        auto_generate: Whether to auto-generate certificates if missing
        cn: Common name for certificate
    
    Returns:
        SSL context or None if SSL not available
    """
    cert_path = Path(cert_dir)
    cert_path.mkdir(exist_ok=True)
    
    cert_file_path = cert_path / cert_file
    key_file_path = cert_path / key_file
    
    # Check if certificates exist and are valid
    if cert_file_path.exists() and key_file_path.exists():
        if is_certificate_valid(cert_file_path):
            print(f"✓ Using existing SSL certificate: {cert_file_path}")
            return ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        else:
            print("⚠️  Existing certificate is expired or invalid")
    
    # Generate new certificate if needed
    if auto_generate and CRYPTO_AVAILABLE:
        if generate_self_signed_cert(cert_file_path, key_file_path, cn):
            print(f"✓ Generated new SSL certificate: {cert_file_path}")
            return ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    
    print("❌ SSL certificate not available. Running without HTTPS.")
    return None

def generate_self_signed_cert(cert_path, key_path, cn="localhost", 
                            country="US", state="State", city="City", 
                            org="Organization", validity_days=365):
    """
    Generate a self-signed SSL certificate
    
    Args:
        cert_path: Path to save certificate
        key_path: Path to save private key
        cn: Common name (usually domain or IP)
        country: Country code
        state: State/Province
        city: City
        org: Organization
        validity_days: Certificate validity in days
    
    Returns:
        True if successful, False otherwise
    """
    if not CRYPTO_AVAILABLE:
        return False
    
    try:
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate subject
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, country),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state),
            x509.NameAttribute(NameOID.LOCALITY_NAME, city),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, org),
            x509.NameAttribute(NameOID.COMMON_NAME, cn),
        ])
        
        # Create certificate
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=validity_days)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(cn),
                x509.IPAddress(socket.inet_aton(cn)) if is_ip_address(cn) else x509.DNSName("localhost"),
            ]),
            critical=False,
        ).add_extension(
            x509.KeyUsage(
                key_encipherment=True,
                digital_signature=True,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                content_commitment=False,
                data_encipherment=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        ).add_extension(
            x509.ExtendedKeyUsage([
                x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
            ]),
            critical=True,
        ).sign(private_key, hashes.SHA256())
        
        # Write private key
        with open(key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Write certificate
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        # Set proper permissions
        os.chmod(key_path, 0o600)
        os.chmod(cert_path, 0o644)
        
        print(f"✓ Generated SSL certificate for: {cn}")
        print(f"  Certificate: {cert_path}")
        print(f"  Private Key: {key_path}")
        print(f"  Valid until: {datetime.utcnow() + timedelta(days=validity_days)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to generate SSL certificate: {e}")
        return False

def is_certificate_valid(cert_path):
    """
    Check if a certificate file is valid and not expired
    
    Args:
        cert_path: Path to certificate file
    
    Returns:
        True if valid, False otherwise
    """
    if not CRYPTO_AVAILABLE:
        return False
    
    try:
        with open(cert_path, "rb") as f:
            cert_data = f.read()
        
        cert = x509.load_pem_x509_certificate(cert_data)
        
        # Check if certificate is still valid
        now = datetime.utcnow()
        if now < cert.not_valid_before or now > cert.not_valid_after:
            return False
        
        return True
        
    except Exception:
        return False

def is_ip_address(address):
    """
    Check if a string is a valid IP address
    
    Args:
        address: String to check
    
    Returns:
        True if valid IP, False otherwise
    """
    try:
        socket.inet_aton(address)
        return True
    except socket.error:
        return False

def get_certificate_info(cert_path):
    """
    Get information about a certificate
    
    Args:
        cert_path: Path to certificate file
    
    Returns:
        Dictionary with certificate information
    """
    if not CRYPTO_AVAILABLE or not Path(cert_path).exists():
        return None
    
    try:
        with open(cert_path, "rb") as f:
            cert_data = f.read()
        
        cert = x509.load_pem_x509_certificate(cert_data)
        
        return {
            'subject': cert.subject.rfc4514_string(),
            'issuer': cert.issuer.rfc4514_string(),
            'serial_number': str(cert.serial_number),
            'not_valid_before': cert.not_valid_before,
            'not_valid_after': cert.not_valid_after,
            'is_valid': datetime.utcnow() < cert.not_valid_after,
            'days_until_expiry': (cert.not_valid_after - datetime.utcnow()).days
        }
        
    except Exception as e:
        return {'error': str(e)}

if __name__ == "__main__":
    # Test certificate generation
    import sys
    
    if len(sys.argv) > 1:
        cn = sys.argv[1]
    else:
        cn = "localhost"
    
    print(f"Generating test certificate for: {cn}")
    
    cert_dir = Path("test_certs")
    cert_dir.mkdir(exist_ok=True)
    
    cert_path = cert_dir / "cert.pem"
    key_path = cert_dir / "key.pem"
    
    if generate_self_signed_cert(cert_path, key_path, cn):
        info = get_certificate_info(cert_path)
        if info:
            print("\nCertificate Information:")
            for key, value in info.items():
                print(f"  {key}: {value}")
    
    print(f"\nSSL Context: {get_ssl_context(cert_dir)}")