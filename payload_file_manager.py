#!/usr/bin/env python3
"""
Payload File Manager for Stitch RAT
Manages temporary files, downloads, and cleanup for compiled payloads
"""

import os
import time
import threading
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import tempfile

class PayloadFileManager:
    """Manages compiled payload files and downloads"""
    
    def __init__(self, base_storage_dir: str = None, max_file_age_hours: int = 24):
        """
        Initialize payload file manager
        
        Args:
            base_storage_dir: Base directory for storing files (default: temp)
            max_file_age_hours: Maximum age of files before cleanup (default: 24 hours)
        """
        if base_storage_dir is None:
            base_storage_dir = os.path.join(tempfile.gettempdir(), 'stitch_payloads')
        
        self.base_storage_dir = Path(base_storage_dir)
        self.max_file_age = timedelta(hours=max_file_age_hours)
        self.file_registry = {}  # {file_id: file_info}
        self.registry_lock = threading.Lock()
        
        # Create storage directory
        self.base_storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_running = True
        self.cleanup_thread.start()
    
    def register_file(self, file_path: str, metadata: Dict = None) -> str:
        """
        Register a file for managed download
        
        Args:
            file_path: Path to the file to register
            metadata: Additional metadata about the file
        
        Returns:
            Unique file ID for download
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Generate unique file ID
        file_id = self._generate_file_id(file_path)
        
        # Create managed storage path
        managed_path = self.base_storage_dir / f"{file_id}_{os.path.basename(file_path)}"
        
        # Copy file to managed storage
        shutil.copy2(file_path, managed_path)
        
        # Register file info
        file_info = {
            'file_id': file_id,
            'original_path': file_path,
            'managed_path': str(managed_path),
            'filename': os.path.basename(file_path),
            'size': os.path.getsize(managed_path),
            'created_at': datetime.now(),
            'downloaded_count': 0,
            'metadata': metadata or {}
        }
        
        with self.registry_lock:
            self.file_registry[file_id] = file_info
        
        return file_id
    
    def get_file_info(self, file_id: str) -> Optional[Dict]:
        """Get information about a registered file"""
        with self.registry_lock:
            return self.file_registry.get(file_id)
    
    def get_file_path(self, file_id: str) -> Optional[str]:
        """Get the managed path for a file"""
        file_info = self.get_file_info(file_id)
        if file_info and os.path.exists(file_info['managed_path']):
            return file_info['managed_path']
        return None
    
    def increment_download_count(self, file_id: str):
        """Increment download counter for a file"""
        with self.registry_lock:
            if file_id in self.file_registry:
                self.file_registry[file_id]['downloaded_count'] += 1
    
    def list_files(self, include_expired: bool = False) -> List[Dict]:
        """List all registered files"""
        with self.registry_lock:
            files = []
            for file_info in self.file_registry.values():
                if include_expired or not self._is_file_expired(file_info):
                    files.append(file_info.copy())
            return files
    
    def cleanup_expired_files(self) -> int:
        """Clean up expired files and return count of cleaned files"""
        cleaned_count = 0
        
        with self.registry_lock:
            expired_ids = []
            for file_id, file_info in self.file_registry.items():
                if self._is_file_expired(file_info):
                    expired_ids.append(file_id)
            
            for file_id in expired_ids:
                file_info = self.file_registry[file_id]
                try:
                    # Remove managed file
                    if os.path.exists(file_info['managed_path']):
                        os.remove(file_info['managed_path'])
                    
                    # Remove from registry
                    del self.file_registry[file_id]
                    cleaned_count += 1
                    
                except Exception as e:
                    print(f"Error cleaning up file {file_id}: {e}")
        
        return cleaned_count
    
    def remove_file(self, file_id: str) -> bool:
        """Manually remove a file"""
        with self.registry_lock:
            if file_id not in self.file_registry:
                return False
            
            file_info = self.file_registry[file_id]
            try:
                # Remove managed file
                if os.path.exists(file_info['managed_path']):
                    os.remove(file_info['managed_path'])
                
                # Remove from registry
                del self.file_registry[file_id]
                return True
                
            except Exception as e:
                print(f"Error removing file {file_id}: {e}")
                return False
    
    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        with self.registry_lock:
            total_files = len(self.file_registry)
            total_size = sum(info['size'] for info in self.file_registry.values())
            
            expired_count = sum(1 for info in self.file_registry.values() 
                              if self._is_file_expired(info))
            
            return {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'expired_files': expired_count,
                'storage_directory': str(self.base_storage_dir)
            }
    
    def _generate_file_id(self, file_path: str) -> str:
        """Generate unique file ID based on file content and timestamp"""
        # Create hash from file content and current time
        hasher = hashlib.sha256()
        
        # Add file content
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        
        # Add timestamp for uniqueness
        hasher.update(str(time.time()).encode())
        
        return hasher.hexdigest()[:16]  # 16 character ID
    
    def _is_file_expired(self, file_info: Dict) -> bool:
        """Check if a file is expired"""
        return datetime.now() - file_info['created_at'] > self.max_file_age
    
    def _cleanup_worker(self):
        """Background worker for periodic cleanup"""
        while self.cleanup_running:
            try:
                cleaned = self.cleanup_expired_files()
                if cleaned > 0:
                    print(f"Cleaned up {cleaned} expired payload files")
                
                # Sleep for 1 hour between cleanups
                time.sleep(3600)
                
            except Exception as e:
                print(f"Error in cleanup worker: {e}")
                time.sleep(300)  # Sleep 5 minutes on error
    
    def shutdown(self):
        """Shutdown the file manager"""
        self.cleanup_running = False
        if self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5)

class PayloadDownloadManager:
    """Manages payload downloads with security and tracking"""
    
    def __init__(self, file_manager: PayloadFileManager):
        self.file_manager = file_manager
        self.download_sessions = {}  # {session_id: session_info}
        self.session_lock = threading.Lock()
    
    def create_download_session(self, file_id: str, user_info: Dict = None) -> str:
        """
        Create a secure download session
        
        Args:
            file_id: ID of file to download
            user_info: Information about the user requesting download
        
        Returns:
            Session ID for secure download
        """
        file_info = self.file_manager.get_file_info(file_id)
        if not file_info:
            raise ValueError(f"File not found: {file_id}")
        
        # Generate session ID
        session_id = hashlib.sha256(
            f"{file_id}_{time.time()}_{os.urandom(16).hex()}".encode()
        ).hexdigest()[:20]
        
        # Create session info
        session_info = {
            'session_id': session_id,
            'file_id': file_id,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=30),  # 30 minute expiry
            'user_info': user_info or {},
            'downloaded': False
        }
        
        with self.session_lock:
            self.download_sessions[session_id] = session_info
        
        return session_id
    
    def validate_download_session(self, session_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a download session
        
        Returns:
            (is_valid, file_id)
        """
        with self.session_lock:
            session_info = self.download_sessions.get(session_id)
            
            if not session_info:
                return False, None
            
            # Check if expired
            if datetime.now() > session_info['expires_at']:
                # Clean up expired session
                del self.download_sessions[session_id]
                return False, None
            
            # Check if already downloaded (one-time use)
            if session_info['downloaded']:
                return False, None
            
            return True, session_info['file_id']
    
    def mark_session_downloaded(self, session_id: str):
        """Mark a session as downloaded"""
        with self.session_lock:
            if session_id in self.download_sessions:
                self.download_sessions[session_id]['downloaded'] = True
                
                # Increment file download counter
                file_id = self.download_sessions[session_id]['file_id']
                self.file_manager.increment_download_count(file_id)
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired download sessions"""
        cleaned_count = 0
        
        with self.session_lock:
            expired_sessions = []
            for session_id, session_info in self.download_sessions.items():
                if datetime.now() > session_info['expires_at']:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.download_sessions[session_id]
                cleaned_count += 1
        
        return cleaned_count
    
    def get_session_stats(self) -> Dict:
        """Get download session statistics"""
        with self.session_lock:
            total_sessions = len(self.download_sessions)
            downloaded_sessions = sum(1 for s in self.download_sessions.values() if s['downloaded'])
            
            return {
                'total_sessions': total_sessions,
                'downloaded_sessions': downloaded_sessions,
                'active_sessions': total_sessions - downloaded_sessions
            }

# Global instances
payload_file_manager = PayloadFileManager()
payload_download_manager = PayloadDownloadManager(payload_file_manager)

def register_payload_file(file_path: str, metadata: Dict = None) -> str:
    """Register a payload file for download - for API use"""
    return payload_file_manager.register_file(file_path, metadata)

def create_payload_download_session(file_id: str, user_info: Dict = None) -> str:
    """Create a download session - for API use"""
    return payload_download_manager.create_download_session(file_id, user_info)

def validate_payload_download(session_id: str) -> Tuple[bool, Optional[str]]:
    """Validate a download session - for API use"""
    return payload_download_manager.validate_download_session(session_id)

def get_payload_file_path(file_id: str) -> Optional[str]:
    """Get file path for a payload - for API use"""
    return payload_file_manager.get_file_path(file_id)

def mark_payload_downloaded(session_id: str):
    """Mark payload as downloaded - for API use"""
    payload_download_manager.mark_session_downloaded(session_id)

def get_payload_storage_stats() -> Dict:
    """Get storage statistics - for API use"""
    return payload_file_manager.get_storage_stats()

if __name__ == "__main__":
    # Test the payload file manager
    import tempfile
    
    print("=== Testing Payload File Manager ===")
    
    # Create test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test payload content")
        test_file = f.name
    
    try:
        # Test file registration
        file_id = register_payload_file(test_file, {'type': 'test', 'version': '1.0'})
        print(f"Registered file with ID: {file_id}")
        
        # Test download session
        session_id = create_payload_download_session(file_id, {'user': 'test_user'})
        print(f"Created download session: {session_id}")
        
        # Test validation
        valid, retrieved_file_id = validate_payload_download(session_id)
        print(f"Session valid: {valid}, File ID: {retrieved_file_id}")
        
        # Test stats
        stats = get_payload_storage_stats()
        print(f"Storage stats: {stats}")
        
    finally:
        # Cleanup
        os.unlink(test_file)