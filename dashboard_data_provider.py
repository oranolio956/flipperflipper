#!/usr/bin/env python3
"""
Dashboard Data Provider
Provides real data from databases for dashboard display
Optimized queries with caching and error handling
"""

import os
import sys
import sqlite3
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from functools import lru_cache
from dataclasses import dataclass, asdict

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AgentInfo:
    """Agent information"""
    id: str
    hostname: str
    username: Optional[str]
    ip_address: Optional[str]
    platform: Optional[str]
    architecture: Optional[str]
    privileges: Optional[str]
    first_seen: str
    last_seen: str
    last_beacon: Optional[str]
    status: str
    notes: Optional[str]
    metadata: Optional[Dict[str, Any]]


@dataclass
class CommandInfo:
    """Command information"""
    id: int
    agent_id: str
    command: str
    status: str
    created_at: str
    executed_at: Optional[str]
    completed_at: Optional[str]
    retry_count: int
    priority: int


@dataclass
class DashboardStats:
    """Dashboard statistics"""
    total_agents: int
    active_agents: int
    inactive_agents: int
    new_agents_24h: int
    total_commands: int
    pending_commands: int
    completed_commands_24h: int
    failed_commands_24h: int
    success_rate: float
    avg_execution_time: float


class DashboardDataProvider:
    """
    Provides data for dashboard from multiple databases
    """
    
    def __init__(self):
        """Initialize data provider"""
        self.db_path = Config.APPLICATION_DIR / 'stitch.db'
        self.cache_ttl = 60  # Cache for 60 seconds
        self._ensure_database()
    
    def _ensure_database(self):
        """Ensure database exists and has correct schema"""
        if not self.db_path.exists():
            logger.warning(f"Database not found at {self.db_path}, creating...")
            self._create_database()
    
    def _create_database(self):
        """Create database with schema"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Agents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                hostname TEXT NOT NULL,
                username TEXT,
                ip_address TEXT,
                platform TEXT,
                architecture TEXT,
                privileges TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_beacon TIMESTAMP,
                status TEXT DEFAULT 'active',
                notes TEXT,
                metadata TEXT
            )
        ''')
        
        # Commands table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                command TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                executed_at TIMESTAMP,
                completed_at TIMESTAMP,
                retry_count INTEGER DEFAULT 0,
                priority INTEGER DEFAULT 5,
                FOREIGN KEY (agent_id) REFERENCES agents (id)
            )
        ''')
        
        # Results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_id INTEGER NOT NULL,
                agent_id TEXT NOT NULL,
                output TEXT,
                error TEXT,
                exit_code INTEGER,
                execution_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (command_id) REFERENCES commands (id),
                FOREIGN KEY (agent_id) REFERENCES agents (id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_agents_last_seen ON agents(last_seen)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_commands_status ON commands(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_commands_agent ON commands(agent_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_command ON results(command_id)')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Database created at {self.db_path}")
    
    def get_dashboard_stats(self) -> DashboardStats:
        """Get dashboard statistics"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Total agents
            cursor.execute("SELECT COUNT(*) as count FROM agents")
            total_agents = cursor.fetchone()['count']
            
            # Active agents (seen in last 5 minutes)
            five_min_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
            cursor.execute("""
                SELECT COUNT(*) as count FROM agents 
                WHERE last_seen > ? AND status = 'active'
            """, (five_min_ago,))
            active_agents = cursor.fetchone()['count']
            
            # Inactive agents
            inactive_agents = total_agents - active_agents
            
            # New agents in last 24 hours
            twenty_four_hours_ago = (datetime.now() - timedelta(hours=24)).isoformat()
            cursor.execute("""
                SELECT COUNT(*) as count FROM agents 
                WHERE first_seen > ?
            """, (twenty_four_hours_ago,))
            new_agents_24h = cursor.fetchone()['count']
            
            # Total commands
            cursor.execute("SELECT COUNT(*) as count FROM commands")
            total_commands = cursor.fetchone()['count']
            
            # Pending commands
            cursor.execute("""
                SELECT COUNT(*) as count FROM commands 
                WHERE status = 'pending'
            """)
            pending_commands = cursor.fetchone()['count']
            
            # Completed commands in last 24 hours
            cursor.execute("""
                SELECT COUNT(*) as count FROM commands 
                WHERE status = 'completed' AND completed_at > ?
            """, (twenty_four_hours_ago,))
            completed_commands_24h = cursor.fetchone()['count']
            
            # Failed commands in last 24 hours
            cursor.execute("""
                SELECT COUNT(*) as count FROM commands 
                WHERE status = 'failed' AND completed_at > ?
            """, (twenty_four_hours_ago,))
            failed_commands_24h = cursor.fetchone()['count']
            
            # Success rate
            total_recent = completed_commands_24h + failed_commands_24h
            success_rate = (completed_commands_24h / total_recent * 100) if total_recent > 0 else 100.0
            
            # Average execution time
            cursor.execute("""
                SELECT AVG(execution_time) as avg_time FROM results 
                WHERE created_at > ?
            """, (twenty_four_hours_ago,))
            result = cursor.fetchone()
            avg_execution_time = result['avg_time'] if result['avg_time'] else 0.0
            
            conn.close()
            
            return DashboardStats(
                total_agents=total_agents,
                active_agents=active_agents,
                inactive_agents=inactive_agents,
                new_agents_24h=new_agents_24h,
                total_commands=total_commands,
                pending_commands=pending_commands,
                completed_commands_24h=completed_commands_24h,
                failed_commands_24h=failed_commands_24h,
                success_rate=round(success_rate, 2),
                avg_execution_time=round(avg_execution_time, 3)
            )
        
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            # Return default stats on error
            return DashboardStats(
                total_agents=0,
                active_agents=0,
                inactive_agents=0,
                new_agents_24h=0,
                total_commands=0,
                pending_commands=0,
                completed_commands_24h=0,
                failed_commands_24h=0,
                success_rate=0.0,
                avg_execution_time=0.0
            )
    
    def get_agents(self, limit: int = 100, status: Optional[str] = None) -> List[AgentInfo]:
        """Get list of agents"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM agents"
            params = []
            
            if status:
                query += " WHERE status = ?"
                params.append(status)
            
            query += " ORDER BY last_seen DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            agents = []
            for row in rows:
                metadata = json.loads(row['metadata']) if row['metadata'] else None
                agents.append(AgentInfo(
                    id=row['id'],
                    hostname=row['hostname'],
                    username=row['username'],
                    ip_address=row['ip_address'],
                    platform=row['platform'],
                    architecture=row['architecture'],
                    privileges=row['privileges'],
                    first_seen=row['first_seen'],
                    last_seen=row['last_seen'],
                    last_beacon=row['last_beacon'],
                    status=row['status'],
                    notes=row['notes'],
                    metadata=metadata
                ))
            
            return agents
        
        except Exception as e:
            logger.error(f"Error getting agents: {e}")
            return []
    
    def get_agent_by_id(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent by ID"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                metadata = json.loads(row['metadata']) if row['metadata'] else None
                return AgentInfo(
                    id=row['id'],
                    hostname=row['hostname'],
                    username=row['username'],
                    ip_address=row['ip_address'],
                    platform=row['platform'],
                    architecture=row['architecture'],
                    privileges=row['privileges'],
                    first_seen=row['first_seen'],
                    last_seen=row['last_seen'],
                    last_beacon=row['last_beacon'],
                    status=row['status'],
                    notes=row['notes'],
                    metadata=metadata
                )
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting agent {agent_id}: {e}")
            return None
    
    def get_recent_commands(self, limit: int = 20) -> List[CommandInfo]:
        """Get recent commands"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM commands 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            commands = []
            for row in rows:
                commands.append(CommandInfo(
                    id=row['id'],
                    agent_id=row['agent_id'],
                    command=row['command'],
                    status=row['status'],
                    created_at=row['created_at'],
                    executed_at=row['executed_at'],
                    completed_at=row['completed_at'],
                    retry_count=row['retry_count'],
                    priority=row['priority']
                ))
            
            return commands
        
        except Exception as e:
            logger.error(f"Error getting recent commands: {e}")
            return []
    
    def get_command_result(self, command_id: int) -> Optional[Dict[str, Any]]:
        """Get command result"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM results 
                WHERE command_id = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (command_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row['id'],
                    'command_id': row['command_id'],
                    'agent_id': row['agent_id'],
                    'output': row['output'],
                    'error': row['error'],
                    'exit_code': row['exit_code'],
                    'execution_time': row['execution_time'],
                    'created_at': row['created_at']
                }
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting command result {command_id}: {e}")
            return None
    
    def add_sample_data(self):
        """Add sample data for testing"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Add sample agents
            sample_agents = [
                ('agent-001', 'WORKSTATION-01', 'admin', '192.168.1.100', 'Windows 10', 'x64', 'admin', 'active'),
                ('agent-002', 'SERVER-PROD', 'root', '10.0.0.50', 'Ubuntu 20.04', 'x64', 'root', 'active'),
                ('agent-003', 'LAPTOP-MOBILE', 'user', '172.16.0.10', 'macOS 12', 'arm64', 'user', 'inactive'),
            ]
            
            for agent in sample_agents:
                cursor.execute("""
                    INSERT OR IGNORE INTO agents 
                    (id, hostname, username, ip_address, platform, architecture, privileges, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, agent)
            
            # Add sample commands
            sample_commands = [
                ('agent-001', 'sysinfo', 'completed'),
                ('agent-001', 'screenshot', 'completed'),
                ('agent-002', 'ps', 'completed'),
                ('agent-003', 'whoami', 'pending'),
            ]
            
            for cmd in sample_commands:
                cursor.execute("""
                    INSERT INTO commands (agent_id, command, status)
                    VALUES (?, ?, ?)
                """, cmd)
            
            conn.commit()
            conn.close()
            
            logger.info("Sample data added successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error adding sample data: {e}")
            return False


# Global instance
dashboard_data_provider = DashboardDataProvider()


if __name__ == "__main__":
    # Test the data provider
    print("Dashboard Data Provider - Test")
    print("=" * 60)
    
    # Add sample data
    print("\n[*] Adding sample data...")
    dashboard_data_provider.add_sample_data()
    
    # Get stats
    print("\n[*] Getting dashboard stats...")
    stats = dashboard_data_provider.get_dashboard_stats()
    print(f"  Total Agents: {stats.total_agents}")
    print(f"  Active Agents: {stats.active_agents}")
    print(f"  Total Commands: {stats.total_commands}")
    print(f"  Success Rate: {stats.success_rate}%")
    
    # Get agents
    print("\n[*] Getting agents...")
    agents = dashboard_data_provider.get_agents(limit=10)
    for agent in agents:
        print(f"  {agent.hostname} ({agent.ip_address}) - {agent.status}")
    
    # Get recent commands
    print("\n[*] Getting recent commands...")
    commands = dashboard_data_provider.get_recent_commands(limit=5)
    for cmd in commands:
        print(f"  [{cmd.status}] {cmd.command} on {cmd.agent_id}")
    
    print("\n✓ Test completed successfully")
