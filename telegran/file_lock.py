"""
File Locking System - Prevent concurrent database access
Critical for preventing database corruption
"""

import os
import time
import fcntl
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class FileLock:
    """Cross-process file locking using fcntl"""
    
    def __init__(self, lock_file: str, timeout: int = 10):
        """
        Initialize file lock
        
        Args:
            lock_file: Path to lock file
            timeout: Maximum seconds to wait for lock
        """
        self.lock_file = lock_file
        self.timeout = timeout
        self.lock_fd = None
    
    def acquire(self, blocking: bool = True) -> bool:
        """
        Acquire the lock
        
        Args:
            blocking: Wait for lock if True, return immediately if False
            
        Returns:
            True if lock acquired, False otherwise
        """
        # Create lock file if doesn't exist
        self.lock_fd = open(self.lock_file, 'w')
        
        if blocking:
            # Wait for lock with timeout
            start_time = time.time()
            while True:
                try:
                    fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    logger.debug(f"🔒 Lock acquired: {self.lock_file}")
                    return True
                except IOError:
                    # Lock held by another process
                    if time.time() - start_time > self.timeout:
                        logger.error(f"❌ Lock timeout: {self.lock_file}")
                        self.lock_fd.close()
                        return False
                    time.sleep(0.1)
        else:
            # Non-blocking
            try:
                fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                logger.debug(f"🔒 Lock acquired: {self.lock_file}")
                return True
            except IOError:
                self.lock_fd.close()
                return False
    
    def release(self):
        """Release the lock"""
        if self.lock_fd:
            try:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                self.lock_fd.close()
                logger.debug(f"🔓 Lock released: {self.lock_file}")
            except Exception as e:
                logger.error(f"❌ Error releasing lock: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        if not self.acquire():
            raise RuntimeError(f"Could not acquire lock: {self.lock_file}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()


@contextmanager
def locked_file(file_path: str, timeout: int = 10):
    """
    Context manager for file locking
    
    Usage:
        with locked_file('database.json'):
            # Do file operations
            pass
    """
    lock_file = f"{file_path}.lock"
    lock = FileLock(lock_file, timeout)
    
    try:
        lock.acquire()
        yield
    finally:
        lock.release()
        # Clean up lock file
        try:
            os.remove(lock_file)
        except:
            pass


class DatabaseLock:
    """Specialized lock for database operations"""
    
    def __init__(self, db_file: str = 'userbot_data.json'):
        self.db_file = db_file
        self.lock_file = f"{db_file}.lock"
    
    @contextmanager
    def transaction(self):
        """
        Start a locked database transaction
        
        Usage:
            with db_lock.transaction():
                # Read/write database
                pass
        """
        lock = FileLock(self.lock_file, timeout=10)
        
        try:
            if not lock.acquire():
                raise RuntimeError("Could not acquire database lock")
            
            logger.debug("📦 Database transaction started")
            yield
            
        finally:
            lock.release()
            logger.debug("📦 Database transaction complete")


# Test if fcntl is available (Windows doesn't have it)
def is_locking_available() -> bool:
    """Check if file locking is available on this platform"""
    try:
        import fcntl
        return True
    except ImportError:
        return False


# Fallback for Windows
if not is_locking_available():
    logger.warning("⚠️  fcntl not available (Windows?), using fallback locking")
    
    class FileLock:
        """Fallback file lock using file creation (less reliable)"""
        
        def __init__(self, lock_file: str, timeout: int = 10):
            self.lock_file = lock_file
            self.timeout = timeout
        
        def acquire(self, blocking: bool = True) -> bool:
            """Try to create lock file"""
            start_time = time.time()
            
            while True:
                try:
                    # Try to create file exclusively
                    fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                    os.close(fd)
                    return True
                except FileExistsError:
                    if not blocking:
                        return False
                    
                    if time.time() - start_time > self.timeout:
                        return False
                    
                    time.sleep(0.1)
        
        def release(self):
            """Remove lock file"""
            try:
                os.remove(self.lock_file)
            except:
                pass
        
        def __enter__(self):
            if not self.acquire():
                raise RuntimeError(f"Could not acquire lock: {self.lock_file}")
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.release()
