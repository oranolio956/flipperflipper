#!/usr/bin/env python3
"""
Database Extensions for Dashboard
Add these methods to Core/database.py EliteDatabase class
"""

def get_agent_connection_count(self, agent_id: str) -> int:
    """Get number of times agent has connected"""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM audit_log 
            WHERE action = 'agent_connected' AND target = ?
        ''', (agent_id,))
        result = cursor.fetchone()
        return result[0] if result else 0

def get_commands_by_date_range(self, start_date, end_date):
    """Get commands within date range"""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM commands 
            WHERE created_at BETWEEN ? AND ?
        ''', (start_date.isoformat(), end_date.isoformat()))
        return [dict(row) for row in cursor.fetchall()]

def get_all_credentials(self):
    """Get all credentials"""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM credentials ORDER BY collected_at DESC')
        return [dict(row) for row in cursor.fetchall()]

def get_agent_credentials(self, agent_id: str):
    """Get credentials for specific agent"""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM credentials 
            WHERE agent_id = ? 
            ORDER BY collected_at DESC
        ''', (agent_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_recent_results(self, limit: int = 100):
    """Get recent command results"""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM results 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]

def get_recent_commands(self, limit: int = 10):
    """Get recent commands"""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM commands 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]

def get_agent_commands(self, agent_id: str):
    """Get all commands for agent"""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM commands 
            WHERE agent_id = ? 
            ORDER BY created_at DESC
        ''', (agent_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_all_commands(self):
    """Get all commands"""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM commands ORDER BY created_at DESC')
        return [dict(row) for row in cursor.fetchall()]

def get_command_result(self, command_id: int):
    """Get result for specific command"""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM results 
            WHERE command_id = ? 
            ORDER BY created_at DESC 
            LIMIT 1
        ''', (command_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_all_files(self):
    """Get all files from database"""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM files ORDER BY uploaded_at DESC')
        return [dict(row) for row in cursor.fetchall()]

def get_agent_files(self, agent_id: str):
    """Get files for specific agent"""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM files 
            WHERE agent_id = ? 
            ORDER BY uploaded_at DESC
        ''', (agent_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_all_keylogs(self):
    """Get all keylogs"""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM keylogs ORDER BY timestamp DESC')
        return [dict(row) for row in cursor.fetchall()]

def get_agent_keylogs(self, agent_id: str):
    """Get keylogs for specific agent"""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM keylogs 
            WHERE agent_id = ? 
            ORDER BY timestamp DESC
        ''', (agent_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_audit_logs(self, limit: int = 1000):
    """Get audit logs"""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM audit_log 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]

def add_audit_log(self, user: str, action: str, target: str = None, 
                  details: str = None, ip_address: str = None):
    """Add audit log entry"""
    with self._lock:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO audit_log (user, action, target, details, ip_address)
                VALUES (?, ?, ?, ?, ?)
            ''', (user, action, target, details, ip_address))
            conn.commit()
