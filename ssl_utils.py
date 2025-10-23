#!/usr/bin/env python3
"""
SSL/TLS Utilities for Oranolio RAT - Elite C2 Framework
Provides SSL certificate generation, management, and secure communication
"""

import os
import ssl
import socket
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
import tempfile
import subprocess
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CertificateManager:
    """Manages SSL certificates for the C2 framework"""
    
    def __init__(self, cert_dir: str = "certs"):
        self.cert_dir = Path(cert_dir)
        self.cert_dir.mkdir(exist_ok=True)
        
        # Certificate file paths
        self.cert_file = self.cert_dir / "server.crt"
        self.key_file = self.cert_dir / "server.key"
        self.ca_cert_file = self.cert_dir / "ca.crt"
        self.ca_key_file = self.cert_dir / "ca.key"
        
        # Certificate configuration
        self.cert_config = {
            'country': 'US',
            'state': 'California',
            'city': 'San Francisco',
            'organization': 'Oranolio Security',
            'organizational_unit': 'C2 Framework',
            'common_name': 'oranolio-c2.local',
            'email': 'admin@oranolio.local',
            'validity_days': 365
        }
    
    def generate_self_signed_certificate(self, hostname: str = None) -> Tuple[bool, str]:
        """Generate a self-signed certificate for development"""
        try:
            if hostname:
                self.cert_config['common_name'] = hostname
            
            # Check if certificates already exist
            if self.cert_file.exists() and self.key_file.exists():
                logger.info("Certificates already exist, skipping generation")
                return True, "Certificates already exist"
            
            # Generate private key
            key_command = [
                'openssl', 'genrsa', '-out', str(self.key_file), '2048'
            ]
            
            result = subprocess.run(key_command, capture_output=True, text=True)
            if result.returncode != 0:
                return False, f"Failed to generate private key: {result.stderr}"
            
            # Create certificate signing request
            csr_file = self.cert_dir / "server.csr"
            csr_command = [
                'openssl', 'req', '-new', '-key', str(self.key_file),
                '-out', str(csr_file), '-subj',
                f"/C={self.cert_config['country']}/ST={self.cert_config['state']}/"
                f"L={self.cert_config['city']}/O={self.cert_config['organization']}/"
                f"OU={self.cert_config['organizational_unit']}/"
                f"CN={self.cert_config['common_name']}/"
                f"emailAddress={self.cert_config['email']}"
            ]
            
            result = subprocess.run(csr_command, capture_output=True, text=True)
            if result.returncode != 0:
                return False, f"Failed to create CSR: {result.stderr}"
            
            # Generate self-signed certificate
            cert_command = [
                'openssl', 'x509', '-req', '-days', str(self.cert_config['validity_days']),
                '-in', str(csr_file), '-signkey', str(self.key_file),
                '-out', str(self.cert_file)
            ]
            
            result = subprocess.run(cert_command, capture_output=True, text=True)
            if result.returncode != 0:
                return False, f"Failed to generate certificate: {result.stderr}"
            
            # Clean up CSR file
            csr_file.unlink()
            
            logger.info(f"Self-signed certificate generated: {self.cert_file}")
            return True, "Certificate generated successfully"
            
        except FileNotFoundError:
            return False, "OpenSSL not found. Please install OpenSSL to generate certificates."
        except Exception as e:
            return False, f"Error generating certificate: {e}"
    
    def generate_ca_certificate(self) -> Tuple[bool, str]:
        """Generate a Certificate Authority for internal use"""
        try:
            # Check if CA already exists
            if self.ca_cert_file.exists() and self.ca_key_file.exists():
                logger.info("CA certificate already exists, skipping generation")
                return True, "CA certificate already exists"
            
            # Generate CA private key
            ca_key_command = [
                'openssl', 'genrsa', '-out', str(self.ca_key_file), '4096'
            ]
            
            result = subprocess.run(ca_key_command, capture_output=True, text=True)
            if result.returncode != 0:
                return False, f"Failed to generate CA private key: {result.stderr}"
            
            # Create CA certificate
            ca_cert_command = [
                'openssl', 'req', '-new', '-x509', '-days', '3650',
                '-key', str(self.ca_key_file), '-out', str(self.ca_cert_file),
                '-subj',
                f"/C={self.cert_config['country']}/ST={self.cert_config['state']}/"
                f"L={self.cert_config['city']}/O={self.cert_config['organization']}/"
                f"OU={self.cert_config['organizational_unit']}/"
                f"CN=Oranolio CA/emailAddress={self.cert_config['email']}"
            ]
            
            result = subprocess.run(ca_cert_command, capture_output=True, text=True)
            if result.returncode != 0:
                return False, f"Failed to create CA certificate: {result.stderr}"
            
            logger.info(f"CA certificate generated: {self.ca_cert_file}")
            return True, "CA certificate generated successfully"
            
        except FileNotFoundError:
            return False, "OpenSSL not found. Please install OpenSSL to generate certificates."
        except Exception as e:
            return False, f"Error generating CA certificate: {e}"
    
    def generate_signed_certificate(self, hostname: str) -> Tuple[bool, str]:
        """Generate a certificate signed by the CA"""
        try:
            # Ensure CA exists
            if not self.ca_cert_file.exists() or not self.ca_key_file.exists():
                success, message = self.generate_ca_certificate()
                if not success:
                    return False, f"Failed to create CA: {message}"
            
            # Generate private key for the hostname
            hostname_key_file = self.cert_dir / f"{hostname}.key"
            key_command = [
                'openssl', 'genrsa', '-out', str(hostname_key_file), '2048'
            ]
            
            result = subprocess.run(key_command, capture_output=True, text=True)
            if result.returncode != 0:
                return False, f"Failed to generate private key for {hostname}: {result.stderr}"
            
            # Create certificate signing request
            csr_file = self.cert_dir / f"{hostname}.csr"
            csr_command = [
                'openssl', 'req', '-new', '-key', str(hostname_key_file),
                '-out', str(csr_file), '-subj',
                f"/C={self.cert_config['country']}/ST={self.cert_config['state']}/"
                f"L={self.cert_config['city']}/O={self.cert_config['organization']}/"
                f"OU={self.cert_config['organizational_unit']}/"
                f"CN={hostname}/emailAddress={self.cert_config['email']}"
            ]
            
            result = subprocess.run(csr_command, capture_output=True, text=True)
            if result.returncode != 0:
                return False, f"Failed to create CSR for {hostname}: {result.stderr}"
            
            # Create certificate configuration for SAN
            config_file = self.cert_dir / f"{hostname}.conf"
            with open(config_file, 'w') as f:
                f.write(f"""[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = {self.cert_config['country']}
ST = {self.cert_config['state']}
L = {self.cert_config['city']}
O = {self.cert_config['organization']}
OU = {self.cert_config['organizational_unit']}
CN = {hostname}

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = {hostname}
DNS.2 = *.{hostname}
IP.1 = 127.0.0.1
IP.2 = ::1
""")
            
            # Generate signed certificate
            hostname_cert_file = self.cert_dir / f"{hostname}.crt"
            cert_command = [
                'openssl', 'x509', '-req', '-days', str(self.cert_config['validity_days']),
                '-in', str(csr_file), '-CA', str(self.ca_cert_file),
                '-CAkey', str(self.ca_key_file), '-CAcreateserial',
                '-out', str(hostname_cert_file), '-extensions', 'v3_req',
                '-extfile', str(config_file)
            ]
            
            result = subprocess.run(cert_command, capture_output=True, text=True)
            if result.returncode != 0:
                return False, f"Failed to generate signed certificate for {hostname}: {result.stderr}"
            
            # Clean up temporary files
            csr_file.unlink()
            config_file.unlink()
            
            logger.info(f"Signed certificate generated for {hostname}: {hostname_cert_file}")
            return True, f"Certificate generated successfully for {hostname}"
            
        except Exception as e:
            return False, f"Error generating signed certificate: {e}"
    
    def get_ssl_context(self, cert_file: str = None, key_file: str = None) -> ssl.SSLContext:
        """Get SSL context for secure communication"""
        try:
            cert_file = cert_file or str(self.cert_file)
            key_file = key_file or str(self.key_file)
            
            # Check if certificate files exist
            if not os.path.exists(cert_file) or not os.path.exists(key_file):
                logger.warning("Certificate files not found, generating new ones...")
                success, message = self.generate_self_signed_certificate()
                if not success:
                    raise Exception(f"Failed to generate certificates: {message}")
            
            # Create SSL context
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(cert_file, key_file)
            
            # Configure SSL settings
            context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
            context.options |= ssl.OP_NO_SSLv2
            context.options |= ssl.OP_NO_SSLv3
            context.options |= ssl.OP_NO_TLSv1
            context.options |= ssl.OP_NO_TLSv1_1
            
            # Enable hostname checking
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            
            logger.info("SSL context created successfully")
            return context
            
        except Exception as e:
            logger.error(f"Error creating SSL context: {e}")
            raise
    
    def get_client_ssl_context(self, ca_cert_file: str = None) -> ssl.SSLContext:
        """Get SSL context for client connections"""
        try:
            ca_cert_file = ca_cert_file or str(self.ca_cert_file)
            
            # Create SSL context for client
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            
            # Load CA certificate if it exists
            if os.path.exists(ca_cert_file):
                context.load_verify_locations(ca_cert_file)
                context.verify_mode = ssl.CERT_REQUIRED
            else:
                context.verify_mode = ssl.CERT_NONE
                logger.warning("CA certificate not found, disabling certificate verification")
            
            # Configure SSL settings
            context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
            context.options |= ssl.OP_NO_SSLv2
            context.options |= ssl.OP_NO_SSLv3
            context.options |= ssl.OP_NO_TLSv1
            context.options |= ssl.OP_NO_TLSv1_1
            
            logger.info("Client SSL context created successfully")
            return context
            
        except Exception as e:
            logger.error(f"Error creating client SSL context: {e}")
            raise
    
    def verify_certificate(self, cert_file: str = None) -> Tuple[bool, str]:
        """Verify certificate validity"""
        try:
            cert_file = cert_file or str(self.cert_file)
            
            if not os.path.exists(cert_file):
                return False, "Certificate file not found"
            
            # Check certificate validity
            verify_command = [
                'openssl', 'x509', '-in', cert_file, '-text', '-noout'
            ]
            
            result = subprocess.run(verify_command, capture_output=True, text=True)
            if result.returncode != 0:
                return False, f"Certificate verification failed: {result.stderr}"
            
            # Check expiration date
            check_command = [
                'openssl', 'x509', '-in', cert_file, '-noout', '-dates'
            ]
            
            result = subprocess.run(check_command, capture_output=True, text=True)
            if result.returncode != 0:
                return False, f"Failed to check certificate dates: {result.stderr}"
            
            logger.info("Certificate verification successful")
            return True, "Certificate is valid"
            
        except Exception as e:
            return False, f"Error verifying certificate: {e}"
    
    def get_certificate_info(self, cert_file: str = None) -> Dict[str, Any]:
        """Get certificate information"""
        try:
            cert_file = cert_file or str(self.cert_file)
            
            if not os.path.exists(cert_file):
                return {"error": "Certificate file not found"}
            
            # Get certificate details
            info_command = [
                'openssl', 'x509', '-in', cert_file, '-noout', '-text'
            ]
            
            result = subprocess.run(info_command, capture_output=True, text=True)
            if result.returncode != 0:
                return {"error": f"Failed to get certificate info: {result.stderr}"}
            
            # Parse certificate information
            info = {
                "cert_file": cert_file,
                "raw_info": result.stdout,
                "valid": True
            }
            
            # Extract common name
            cn_command = [
                'openssl', 'x509', '-in', cert_file, '-noout', '-subject'
            ]
            
            result = subprocess.run(cn_command, capture_output=True, text=True)
            if result.returncode == 0:
                info["subject"] = result.stdout.strip()
            
            # Extract validity dates
            dates_command = [
                'openssl', 'x509', '-in', cert_file, '-noout', '-dates'
            ]
            
            result = subprocess.run(dates_command, capture_output=True, text=True)
            if result.returncode == 0:
                info["dates"] = result.stdout.strip()
            
            return info
            
        except Exception as e:
            return {"error": f"Error getting certificate info: {e}"}

def get_ssl_context(cert_file: str = None, key_file: str = None) -> ssl.SSLContext:
    """Convenience function to get SSL context"""
    manager = CertificateManager()
    return manager.get_ssl_context(cert_file, key_file)

def get_client_ssl_context(ca_cert_file: str = None) -> ssl.SSLContext:
    """Convenience function to get client SSL context"""
    manager = CertificateManager()
    return manager.get_client_ssl_context(ca_cert_file)

def generate_certificates(hostname: str = None) -> Tuple[bool, str]:
    """Convenience function to generate certificates"""
    manager = CertificateManager()
    return manager.generate_self_signed_certificate(hostname)

def verify_certificates() -> Tuple[bool, str]:
    """Convenience function to verify certificates"""
    manager = CertificateManager()
    return manager.verify_certificate()

# Example usage and testing
if __name__ == "__main__":
    print("SSL Certificate Manager")
    print("=" * 30)
    
    manager = CertificateManager()
    
    # Generate self-signed certificate
    print("Generating self-signed certificate...")
    success, message = manager.generate_self_signed_certificate()
    print(f"Result: {message}")
    
    if success:
        # Verify certificate
        print("\nVerifying certificate...")
        success, message = manager.verify_certificate()
        print(f"Result: {message}")
        
        # Get certificate info
        print("\nCertificate information:")
        info = manager.get_certificate_info()
        if "error" not in info:
            print(f"Subject: {info.get('subject', 'N/A')}")
            print(f"Dates: {info.get('dates', 'N/A')}")
        else:
            print(f"Error: {info['error']}")
    
    print("\nSSL utilities ready for use!")