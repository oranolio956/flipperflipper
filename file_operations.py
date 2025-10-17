#!/usr/bin/env python3
"""
File Operations Security and Monitoring Module
Provides secure file handling with comprehensive logging and validation
"""
import os
import hashlib
import mimetypes
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FileOperationMonitor:
    """Monitor and log file operations for security"""
    
    def __init__(self):
        self.upload_history = []
        self.download_history = []
        self.max_history = 1000
    
    def log_upload(self, filename: str, size: int, target_ip: str, user: str, success: bool, error: Optional[str] = None) -> None:
        """
        Log file upload operation
        
        Args:
            filename: Name of uploaded file
            size: File size in bytes
            target_ip: Target IP address
            user: Username who performed upload
            success: Whether upload succeeded
            error: Error message if failed
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': 'upload',
            'filename': filename,
            'size': size,
            'target_ip': target_ip,
            'user': user,
            'success': success,
            'error': error,
            'file_hash': None
        }
        
        self.upload_history.append(entry)
        if len(self.upload_history) > self.max_history:
            self.upload_history.pop(0)
        
        log_level = "INFO" if success else "ERROR"
        logger.log(getattr(logging, log_level), 
                  f"File upload: {filename} ({size} bytes) to {target_ip} by {user} - {'Success' if success else f'Failed: {error}'}")
    
    def log_download(self, filename: str, size: int, source_ip: str, user: str, success: bool, error: Optional[str] = None) -> None:
        """
        Log file download operation
        
        Args:
            filename: Name of downloaded file
            size: File size in bytes
            source_ip: Source IP address
            user: Username who performed download
            success: Whether download succeeded
            error: Error message if failed
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': 'download',
            'filename': filename,
            'size': size,
            'source_ip': source_ip,
            'user': user,
            'success': success,
            'error': error
        }
        
        self.download_history.append(entry)
        if len(self.download_history) > self.max_history:
            self.download_history.pop(0)
        
        log_level = "INFO" if success else "ERROR"
        logger.log(getattr(logging, log_level),
                  f"File download: {filename} ({size} bytes) from {source_ip} by {user} - {'Success' if success else f'Failed: {error}'}")
    
    def get_upload_history(self, limit: int = 50) -> List[Dict]:
        """Get recent upload history"""
        return self.upload_history[-limit:]
    
    def get_download_history(self, limit: int = 50) -> List[Dict]:
        """Get recent download history"""
        return self.download_history[-limit:]
    
    def get_file_statistics(self) -> Dict:
        """Get file operation statistics"""
        total_uploads = len(self.upload_history)
        successful_uploads = sum(1 for entry in self.upload_history if entry['success'])
        
        total_downloads = len(self.download_history)
        successful_downloads = sum(1 for entry in self.download_history if entry['success'])
        
        total_upload_size = sum(entry['size'] for entry in self.upload_history if entry['success'])
        total_download_size = sum(entry['size'] for entry in self.download_history if entry['success'])
        
        return {
            'total_uploads': total_uploads,
            'successful_uploads': successful_uploads,
            'failed_uploads': total_uploads - successful_uploads,
            'total_downloads': total_downloads,
            'successful_downloads': successful_downloads,
            'failed_downloads': total_downloads - successful_downloads,
            'total_upload_bytes': total_upload_size,
            'total_download_bytes': total_download_size,
            'upload_success_rate': (successful_uploads / total_uploads * 100) if total_uploads > 0 else 0,
            'download_success_rate': (successful_downloads / total_downloads * 100) if total_downloads > 0 else 0
        }

class SecureFileHandler:
    """Secure file handling with validation and monitoring"""
    
    # Dangerous file extensions
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.vbs', '.js',
        '.jar', '.app', '.deb', '.rpm', '.dmg', '.pkg', '.msi',
        '.sh', '.bash', '.zsh', '.fish', '.ps1', '.psm1'
    }
    
    # Maximum file sizes by type (in bytes)
    MAX_FILE_SIZES = {
        'image': 10 * 1024 * 1024,    # 10MB for images
        'document': 50 * 1024 * 1024,  # 50MB for documents
        'archive': 100 * 1024 * 1024,  # 100MB for archives
        'default': 25 * 1024 * 1024    # 25MB default
    }
    
    @classmethod
    def validate_file_security(cls, filename: str, file_size: int, file_content: Optional[bytes] = None) -> Tuple[bool, Optional[str]]:
        """
        Comprehensive file security validation
        
        Args:
            filename: Name of the file
            file_size: Size of file in bytes
            file_content: Optional file content for deeper inspection
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check filename
        if not filename or len(filename) > 255:
            return False, "Invalid filename length"
        
        # Check for dangerous extensions
        _, ext = os.path.splitext(filename.lower())
        if ext in cls.DANGEROUS_EXTENSIONS:
            return False, f"Dangerous file extension not allowed: {ext}"
        
        # Check file size based on type
        file_type = cls._get_file_type(filename)
        max_size = cls.MAX_FILE_SIZES.get(file_type, cls.MAX_FILE_SIZES['default'])
        
        if file_size > max_size:
            return False, f"File too large for type {file_type}: {file_size} bytes (max: {max_size})"
        
        # Content-based validation if available
        if file_content:
            # Check for executable signatures
            if cls._has_executable_signature(file_content):
                return False, "File contains executable signature"
            
            # Check for script content
            if cls._contains_script_content(file_content, filename):
                return False, "File contains potentially dangerous script content"
        
        return True, None
    
    @classmethod
    def _get_file_type(cls, filename: str) -> str:
        """Determine file type category"""
        _, ext = os.path.splitext(filename.lower())
        
        image_exts = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp'}
        document_exts = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf'}
        archive_exts = {'.zip', '.tar', '.gz', '.7z', '.rar', '.bz2'}
        
        if ext in image_exts:
            return 'image'
        elif ext in document_exts:
            return 'document'
        elif ext in archive_exts:
            return 'archive'
        else:
            return 'default'
    
    @classmethod
    def _has_executable_signature(cls, content: bytes) -> bool:
        """Check if file has executable signatures"""
        if len(content) < 4:
            return False
        
        # Common executable signatures
        signatures = [
            b'MZ',      # PE/DOS executable
            b'\x7fELF', # ELF executable
            b'\xfe\xed\xfa', # Mach-O executable
            b'\xcf\xfa\xed\xfe', # Mach-O executable
        ]
        
        for sig in signatures:
            if content.startswith(sig):
                return True
        
        return False
    
    @classmethod
    def _contains_script_content(cls, content: bytes, filename: str) -> bool:
        """Check if file contains potentially dangerous script content"""
        try:
            # Try to decode as text
            text_content = content.decode('utf-8', errors='ignore').lower()
        except:
            return False
        
        # Check for script indicators
        script_indicators = [
            'eval(', 'exec(', 'system(', 'subprocess',
            '<script', 'javascript:', 'vbscript:',
            'powershell', 'cmd.exe', '/bin/bash', '/bin/sh'
        ]
        
        for indicator in script_indicators:
            if indicator in text_content:
                return True
        
        return False
    
    @classmethod
    def calculate_file_hash(cls, file_path: str) -> Optional[str]:
        """Calculate SHA-256 hash of file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return None
    
    @classmethod
    def get_file_info(cls, file_path: str) -> Dict:
        """Get comprehensive file information"""
        try:
            stat = os.stat(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            return {
                'filename': os.path.basename(file_path),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'mime_type': mime_type,
                'file_hash': cls.calculate_file_hash(file_path),
                'is_safe': cls.validate_file_security(os.path.basename(file_path), stat.st_size)[0]
            }
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            return {'error': str(e)}

# Global file operation monitor
file_monitor = FileOperationMonitor()

def get_file_monitor() -> FileOperationMonitor:
    """Get the global file operation monitor"""
    return file_monitor

def log_file_upload(filename: str, size: int, target_ip: str, user: str, success: bool, error: Optional[str] = None) -> None:
    """Log file upload operation"""
    file_monitor.log_upload(filename, size, target_ip, user, success, error)

def log_file_download(filename: str, size: int, source_ip: str, user: str, success: bool, error: Optional[str] = None) -> None:
    """Log file download operation"""
    file_monitor.log_download(filename, size, source_ip, user, success, error)

def validate_file_upload(filename: str, file_size: int, file_content: Optional[bytes] = None) -> Tuple[bool, Optional[str]]:
    """Validate file for upload"""
    return SecureFileHandler.validate_file_security(filename, file_size, file_content)

def get_file_statistics() -> Dict:
    """Get file operation statistics"""
    return file_monitor.get_file_statistics()

# Export main classes and functions
__all__ = [
    'FileOperationMonitor',
    'SecureFileHandler',
    'get_file_monitor',
    'log_file_upload',
    'log_file_download',
    'validate_file_upload',
    'get_file_statistics'
]