"""
Health Monitoring System
Monitors bot health and sends alerts on failures
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Monitor bot health and send alerts"""
    
    def __init__(self, alert_methods: list = None):
        """
        Initialize health monitor
        
        Args:
            alert_methods: List of alert methods ('log', 'telegram', 'file')
        """
        self.alert_methods = alert_methods or ['log', 'file']
        self.last_heartbeat = datetime.now(timezone.utc)
        self.heartbeat_interval = 60  # seconds
        self.health_status = 'healthy'
        self.error_count = 0
        self.alerts_sent = []
    
    async def heartbeat_loop(self):
        """Send periodic heartbeats"""
        while True:
            await asyncio.sleep(self.heartbeat_interval)
            self.last_heartbeat = datetime.now(timezone.utc)
            logger.debug(f"💓 Heartbeat at {self.last_heartbeat}")
    
    def record_success(self, action: str):
        """Record successful action"""
        logger.debug(f"✅ Success: {action}")
        # Reset error count on success
        if self.error_count > 0:
            self.error_count = max(0, self.error_count - 1)
    
    def record_error(self, action: str, error: Exception):
        """Record error and potentially alert"""
        self.error_count += 1
        logger.error(f"❌ Error in {action}: {error}")
        
        # Alert thresholds
        if self.error_count >= 5:
            self.send_alert(
                severity='high',
                message=f"High error count: {self.error_count} errors",
                details=str(error)
            )
    
    def send_alert(self, severity: str, message: str, details: str = ""):
        """Send health alert"""
        alert = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'severity': severity,
            'message': message,
            'details': details
        }
        
        self.alerts_sent.append(alert)
        
        if 'log' in self.alert_methods:
            logger.critical(f"🚨 ALERT [{severity}]: {message}")
            if details:
                logger.critical(f"   Details: {details}")
        
        if 'file' in self.alert_methods:
            self._write_alert_to_file(alert)
        
        if 'telegram' in self.alert_methods:
            # TODO: Send Telegram message to yourself
            pass
    
    def _write_alert_to_file(self, alert: dict):
        """Write alert to alerts.log"""
        try:
            with open('alerts.log', 'a') as f:
                f.write(f"{alert['timestamp']} [{alert['severity']}] {alert['message']}\n")
                if alert['details']:
                    f.write(f"  Details: {alert['details']}\n")
        except Exception as e:
            logger.error(f"Failed to write alert: {e}")
    
    def get_health_status(self) -> dict:
        """Get current health status"""
        time_since_heartbeat = (
            datetime.now(timezone.utc) - self.last_heartbeat
        ).total_seconds()
        
        is_healthy = (
            time_since_heartbeat < self.heartbeat_interval * 2 and
            self.error_count < 10
        )
        
        return {
            'status': 'healthy' if is_healthy else 'unhealthy',
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'seconds_since_heartbeat': time_since_heartbeat,
            'error_count': self.error_count,
            'alerts_sent': len(self.alerts_sent)
        }
    
    async def check_disk_space(self):
        """Monitor disk space"""
        while True:
            await asyncio.sleep(3600)  # Check hourly
            
            try:
                import shutil
                total, used, free = shutil.disk_usage('.')
                
                free_percent = (free / total) * 100
                
                if free_percent < 10:
                    self.send_alert(
                        severity='high',
                        message=f"Low disk space: {free_percent:.1f}% free"
                    )
                elif free_percent < 20:
                    logger.warning(f"⚠️  Disk space low: {free_percent:.1f}% free")
            except Exception as e:
                logger.error(f"Error checking disk space: {e}")
    
    async def check_database_size(self):
        """Monitor database file size"""
        while True:
            await asyncio.sleep(3600)  # Check hourly
            
            try:
                if os.path.exists('userbot_data.json'):
                    size = os.path.getsize('userbot_data.json')
                    size_mb = size / (1024 * 1024)
                    
                    if size_mb > 100:
                        self.send_alert(
                            severity='medium',
                            message=f"Database large: {size_mb:.1f} MB"
                        )
                        logger.warning(f"⚠️  Database size: {size_mb:.1f} MB - consider cleanup")
            except Exception as e:
                logger.error(f"Error checking database size: {e}")


class AlertManager:
    """Manage different alert channels"""
    
    def __init__(self):
        self.telegram_client = None
        self.admin_id = os.getenv('ADMIN_ID')
    
    async def send_telegram_alert(self, message: str):
        """Send alert via Telegram to yourself"""
        if not self.telegram_client or not self.admin_id:
            return
        
        try:
            await self.telegram_client.send_message(
                int(self.admin_id),
                f"🚨 Bot Alert:\n{message}"
            )
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
    
    async def send_email_alert(self, subject: str, body: str):
        """Send email alert (requires SMTP config)"""
        # TODO: Implement email alerts
        pass
