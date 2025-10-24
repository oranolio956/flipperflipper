#!/usr/bin/env python3
"""
Production Logging Configuration
High-performance logging with rotation and structured output
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import json

# Ensure logs directory exists
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'user_email'):
            log_data["user_email"] = record.user_email
        if hasattr(record, 'ip_address'):
            log_data["ip_address"] = record.ip_address
        if hasattr(record, 'request_id'):
            log_data["request_id"] = record.request_id
        
        return json.dumps(log_data)

class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Format message
        message = super().format(record)
        
        return f"{color}[{timestamp}] [{record.levelname}]{reset} {record.name}: {message}"

def setup_production_logging(
    app_name: str = "oranolio_rat",
    log_level: str = None,
    enable_json: bool = True,
    enable_console: bool = True
):
    """
    Setup production-grade logging configuration
    
    Args:
        app_name: Application name for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_json: Enable JSON formatted logging
        enable_console: Enable console output
    """
    
    # Get log level from environment or parameter
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    log_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colors
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_formatter = ColoredFormatter()
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # Main application log file (rotating)
    app_log_file = LOGS_DIR / f"{app_name}.log"
    app_handler = logging.handlers.RotatingFileHandler(
        app_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    app_handler.setLevel(log_level)
    
    if enable_json:
        app_formatter = JSONFormatter()
    else:
        app_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    app_handler.setFormatter(app_formatter)
    root_logger.addHandler(app_handler)
    
    # Error log file (errors and above only)
    error_log_file = LOGS_DIR / f"{app_name}_errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    
    if enable_json:
        error_formatter = JSONFormatter()
    else:
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(pathname)s:%(lineno)d'
        )
    
    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)
    
    # Security log file
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.INFO)
    security_logger.propagate = False
    
    security_log_file = LOGS_DIR / f"{app_name}_security.log"
    security_handler = logging.handlers.RotatingFileHandler(
        security_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=20,  # Keep more security logs
        encoding='utf-8'
    )
    security_handler.setLevel(logging.INFO)
    
    if enable_json:
        security_formatter = JSONFormatter()
    else:
        security_formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
        )
    
    security_handler.setFormatter(security_formatter)
    security_logger.addHandler(security_handler)
    
    # Performance log file
    perf_logger = logging.getLogger('performance')
    perf_logger.setLevel(logging.INFO)
    perf_logger.propagate = False
    
    perf_log_file = LOGS_DIR / f"{app_name}_performance.log"
    perf_handler = logging.handlers.RotatingFileHandler(
        perf_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    perf_handler.setLevel(logging.INFO)
    
    if enable_json:
        perf_formatter = JSONFormatter()
    else:
        perf_formatter = logging.Formatter(
            '%(asctime)s - PERFORMANCE - %(message)s'
        )
    
    perf_handler.setFormatter(perf_formatter)
    perf_logger.addHandler(perf_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('socketio').setLevel(logging.WARNING)
    logging.getLogger('engineio').setLevel(logging.WARNING)
    
    # Log startup message
    root_logger.info(f"Logging initialized for {app_name}")
    root_logger.info(f"Log level: {logging.getLevelName(log_level)}")
    root_logger.info(f"Log directory: {LOGS_DIR.absolute()}")
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)

def log_security_event(event_type: str, details: dict, severity: str = "INFO"):
    """Log a security event"""
    logger = logging.getLogger('security')
    log_func = getattr(logger, severity.lower(), logger.info)
    
    message = f"{event_type}: {json.dumps(details)}"
    log_func(message)

def log_performance_metric(metric_name: str, value: float, unit: str = "ms"):
    """Log a performance metric"""
    logger = logging.getLogger('performance')
    logger.info(f"{metric_name}: {value}{unit}")

# Initialize logging on import
if __name__ != "__main__":
    setup_production_logging()
