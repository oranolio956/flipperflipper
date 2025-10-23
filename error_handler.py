#!/usr/bin/env python3
"""
Centralized Error Handler for Oranolio RAT - Elite C2 Framework
Provides comprehensive error handling, logging, and recovery mechanisms
"""

import os
import sys
import traceback
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from functools import wraps
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for classification"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    NETWORK = "network"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    SECURITY = "security"
    SYSTEM = "system"
    APPLICATION = "application"
    EXTERNAL = "external"

@dataclass
class ErrorContext:
    """Context information for errors"""
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    target_id: Optional[str] = None
    command: Optional[str] = None
    additional_data: Dict[str, Any] = None

@dataclass
class ErrorInfo:
    """Structured error information"""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    exception_type: str
    traceback: str
    context: ErrorContext
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

class ErrorRecoveryStrategy:
    """Base class for error recovery strategies"""
    
    def can_handle(self, error: Exception, context: ErrorContext) -> bool:
        """Check if this strategy can handle the error"""
        return False
    
    def recover(self, error: Exception, context: ErrorContext) -> bool:
        """Attempt to recover from the error"""
        return False

class DatabaseRecoveryStrategy(ErrorRecoveryStrategy):
    """Recovery strategy for database errors"""
    
    def can_handle(self, error: Exception, context: ErrorContext) -> bool:
        return isinstance(error, (ConnectionError, TimeoutError)) and context.category == ErrorCategory.DATABASE
    
    def recover(self, error: Exception, context: ErrorContext) -> bool:
        try:
            # Attempt to reconnect to database
            import sqlite3
            # This is a simplified example - in practice, you'd have proper connection management
            logger.info("Attempting database reconnection...")
            time.sleep(1)  # Brief delay before retry
            return True
        except Exception as e:
            logger.error(f"Database recovery failed: {e}")
            return False

class NetworkRecoveryStrategy(ErrorRecoveryStrategy):
    """Recovery strategy for network errors"""
    
    def can_handle(self, error: Exception, context: ErrorContext) -> bool:
        return isinstance(error, (ConnectionError, TimeoutError, OSError)) and context.category == ErrorCategory.NETWORK
    
    def recover(self, error: Exception, context: ErrorContext) -> bool:
        try:
            # Attempt to re-establish network connection
            logger.info("Attempting network reconnection...")
            time.sleep(2)  # Brief delay before retry
            return True
        except Exception as e:
            logger.error(f"Network recovery failed: {e}")
            return False

class FileSystemRecoveryStrategy(ErrorRecoveryStrategy):
    """Recovery strategy for file system errors"""
    
    def can_handle(self, error: Exception, context: ErrorContext) -> bool:
        return isinstance(error, (FileNotFoundError, PermissionError, OSError)) and context.category == ErrorCategory.FILE_SYSTEM
    
    def recover(self, error: Exception, context: ErrorContext) -> bool:
        try:
            # Attempt to create missing directories or fix permissions
            if isinstance(error, FileNotFoundError):
                logger.info("Attempting to create missing directory...")
                os.makedirs(os.path.dirname(str(error.filename)), exist_ok=True)
                return True
            return False
        except Exception as e:
            logger.error(f"File system recovery failed: {e}")
            return False

class CentralizedErrorHandler:
    """Centralized error handling system"""
    
    def __init__(self, log_file: str = "logs/errors.log"):
        self.log_file = log_file
        self.error_history: List[ErrorInfo] = []
        self.recovery_strategies: List[ErrorRecoveryStrategy] = []
        self.error_handlers: Dict[str, Callable] = {}
        self.rate_limits: Dict[str, List[datetime]] = {}
        self.lock = threading.RLock()
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Register default recovery strategies
        self._register_default_strategies()
        
        # Register default error handlers
        self._register_default_handlers()
    
    def _setup_logging(self):
        """Setup error logging"""
        self.error_logger = logging.getLogger("error_handler")
        self.error_logger.setLevel(logging.ERROR)
        
        # File handler for errors
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.ERROR)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        self.error_logger.addHandler(file_handler)
    
    def _register_default_strategies(self):
        """Register default recovery strategies"""
        self.recovery_strategies = [
            DatabaseRecoveryStrategy(),
            NetworkRecoveryStrategy(),
            FileSystemRecoveryStrategy()
        ]
    
    def _register_default_handlers(self):
        """Register default error handlers"""
        self.error_handlers = {
            'authentication': self._handle_authentication_error,
            'authorization': self._handle_authorization_error,
            'validation': self._handle_validation_error,
            'network': self._handle_network_error,
            'database': self._handle_database_error,
            'file_system': self._handle_file_system_error,
            'security': self._handle_security_error,
            'system': self._handle_system_error,
            'application': self._handle_application_error,
            'external': self._handle_external_error
        }
    
    def handle_error(self, error: Exception, context: ErrorContext = None, 
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    category: ErrorCategory = ErrorCategory.APPLICATION) -> ErrorInfo:
        """Handle an error with full context"""
        if context is None:
            context = ErrorContext()
        
        # Generate unique error ID
        error_id = f"ERR_{int(time.time() * 1000)}_{os.urandom(4).hex()}"
        
        # Create error info
        error_info = ErrorInfo(
            error_id=error_id,
            timestamp=datetime.now(),
            severity=severity,
            category=category,
            message=str(error),
            exception_type=type(error).__name__,
            traceback=traceback.format_exc(),
            context=context
        )
        
        with self.lock:
            # Add to history
            self.error_history.append(error_info)
            
            # Keep only last 1000 errors
            if len(self.error_history) > 1000:
                self.error_history = self.error_history[-1000:]
        
        # Log the error
        self._log_error(error_info)
        
        # Check rate limiting
        if self._is_rate_limited(error_info):
            logger.warning(f"Error rate limited: {error_id}")
            return error_info
        
        # Attempt recovery
        if self._attempt_recovery(error, context):
            logger.info(f"Error recovered: {error_id}")
            return error_info
        
        # Call specific error handler
        handler = self.error_handlers.get(category.value)
        if handler:
            try:
                handler(error_info)
            except Exception as e:
                logger.error(f"Error in error handler: {e}")
        
        return error_info
    
    def _log_error(self, error_info: ErrorInfo):
        """Log error information"""
        log_data = {
            "error_id": error_info.error_id,
            "timestamp": error_info.timestamp.isoformat(),
            "severity": error_info.severity.value,
            "category": error_info.category.value,
            "message": error_info.message,
            "exception_type": error_info.exception_type,
            "context": asdict(error_info.context),
            "traceback": error_info.traceback
        }
        
        # Log to file
        self.error_logger.error(json.dumps(log_data))
        
        # Log to console for critical errors
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"CRITICAL ERROR: {error_info.message}")
            logger.critical(f"Error ID: {error_info.error_id}")
    
    def _is_rate_limited(self, error_info: ErrorInfo) -> bool:
        """Check if error is rate limited"""
        key = f"{error_info.category.value}_{error_info.context.user_id or 'anonymous'}"
        now = datetime.now()
        
        # Clean old entries
        if key in self.rate_limits:
            self.rate_limits[key] = [
                timestamp for timestamp in self.rate_limits[key]
                if now - timestamp < timedelta(minutes=5)
            ]
        else:
            self.rate_limits[key] = []
        
        # Check rate limit (max 10 errors per 5 minutes)
        if len(self.rate_limits[key]) >= 10:
            return True
        
        # Add current error
        self.rate_limits[key].append(now)
        return False
    
    def _attempt_recovery(self, error: Exception, context: ErrorContext) -> bool:
        """Attempt to recover from error using registered strategies"""
        for strategy in self.recovery_strategies:
            if strategy.can_handle(error, context):
                try:
                    if strategy.recover(error, context):
                        logger.info(f"Error recovered using {strategy.__class__.__name__}")
                        return True
                except Exception as e:
                    logger.error(f"Recovery strategy failed: {e}")
        
        return False
    
    def _handle_authentication_error(self, error_info: ErrorInfo):
        """Handle authentication errors"""
        logger.warning(f"Authentication error: {error_info.message}")
        
        # Log security event
        if error_info.context.user_id:
            self._log_security_event("authentication_failure", error_info)
    
    def _handle_authorization_error(self, error_info: ErrorInfo):
        """Handle authorization errors"""
        logger.warning(f"Authorization error: {error_info.message}")
        
        # Log security event
        self._log_security_event("authorization_failure", error_info)
    
    def _handle_validation_error(self, error_info: ErrorInfo):
        """Handle validation errors"""
        logger.info(f"Validation error: {error_info.message}")
    
    def _handle_network_error(self, error_info: ErrorInfo):
        """Handle network errors"""
        logger.error(f"Network error: {error_info.message}")
    
    def _handle_database_error(self, error_info: ErrorInfo):
        """Handle database errors"""
        logger.error(f"Database error: {error_info.message}")
    
    def _handle_file_system_error(self, error_info: ErrorInfo):
        """Handle file system errors"""
        logger.error(f"File system error: {error_info.message}")
    
    def _handle_security_error(self, error_info: ErrorInfo):
        """Handle security errors"""
        logger.critical(f"Security error: {error_info.message}")
        
        # Log security event
        self._log_security_event("security_violation", error_info)
    
    def _handle_system_error(self, error_info: ErrorInfo):
        """Handle system errors"""
        logger.error(f"System error: {error_info.message}")
    
    def _handle_application_error(self, error_info: ErrorInfo):
        """Handle application errors"""
        logger.error(f"Application error: {error_info.message}")
    
    def _handle_external_error(self, error_info: ErrorInfo):
        """Handle external service errors"""
        logger.error(f"External service error: {error_info.message}")
    
    def _log_security_event(self, event_type: str, error_info: ErrorInfo):
        """Log security events"""
        security_data = {
            "event_type": event_type,
            "error_id": error_info.error_id,
            "timestamp": error_info.timestamp.isoformat(),
            "user_id": error_info.context.user_id,
            "ip_address": error_info.context.ip_address,
            "user_agent": error_info.context.user_agent,
            "message": error_info.message
        }
        
        # Log to security log file
        security_log_file = "logs/security.log"
        os.makedirs(os.path.dirname(security_log_file), exist_ok=True)
        
        with open(security_log_file, 'a') as f:
            f.write(json.dumps(security_data) + '\n')
    
    def register_recovery_strategy(self, strategy: ErrorRecoveryStrategy):
        """Register a new recovery strategy"""
        self.recovery_strategies.append(strategy)
    
    def register_error_handler(self, category: str, handler: Callable):
        """Register a custom error handler"""
        self.error_handlers[category] = handler
    
    def get_error_history(self, limit: int = 100) -> List[ErrorInfo]:
        """Get recent error history"""
        with self.lock:
            return self.error_history[-limit:]
    
    def get_errors_by_category(self, category: ErrorCategory, limit: int = 100) -> List[ErrorInfo]:
        """Get errors by category"""
        with self.lock:
            return [
                error for error in self.error_history
                if error.category == category
            ][-limit:]
    
    def get_errors_by_severity(self, severity: ErrorSeverity, limit: int = 100) -> List[ErrorInfo]:
        """Get errors by severity"""
        with self.lock:
            return [
                error for error in self.error_history
                if error.severity == severity
            ][-limit:]
    
    def resolve_error(self, error_id: str, resolved_by: str):
        """Mark an error as resolved"""
        with self.lock:
            for error in self.error_history:
                if error.error_id == error_id:
                    error.resolved = True
                    error.resolved_at = datetime.now()
                    error.resolved_by = resolved_by
                    break
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        with self.lock:
            total_errors = len(self.error_history)
            
            if total_errors == 0:
                return {"total_errors": 0}
            
            # Count by category
            category_counts = {}
            for error in self.error_history:
                category = error.category.value
                category_counts[category] = category_counts.get(category, 0) + 1
            
            # Count by severity
            severity_counts = {}
            for error in self.error_history:
                severity = error.severity.value
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Count resolved errors
            resolved_count = sum(1 for error in self.error_history if error.resolved)
            
            # Recent errors (last 24 hours)
            recent_cutoff = datetime.now() - timedelta(hours=24)
            recent_errors = sum(1 for error in self.error_history if error.timestamp > recent_cutoff)
            
            return {
                "total_errors": total_errors,
                "resolved_errors": resolved_count,
                "unresolved_errors": total_errors - resolved_count,
                "recent_errors": recent_errors,
                "category_counts": category_counts,
                "severity_counts": severity_counts
            }

# Global error handler instance
error_handler = CentralizedErrorHandler()

def handle_error(error: Exception, context: ErrorContext = None, 
                severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                category: ErrorCategory = ErrorCategory.APPLICATION) -> ErrorInfo:
    """Convenience function to handle errors"""
    return error_handler.handle_error(error, context, severity, category)

def error_handler_decorator(severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                           category: ErrorCategory = ErrorCategory.APPLICATION):
    """Decorator for automatic error handling"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = ErrorContext(
                    additional_data={
                        'function': func.__name__,
                        'args': str(args),
                        'kwargs': str(kwargs)
                    }
                )
                handle_error(e, context, severity, category)
                raise
        return wrapper
    return decorator

def safe_execute(func: Callable, *args, **kwargs) -> tuple:
    """Safely execute a function and return (success, result, error)"""
    try:
        result = func(*args, **kwargs)
        return True, result, None
    except Exception as e:
        context = ErrorContext(
            additional_data={
                'function': func.__name__,
                'args': str(args),
                'kwargs': str(kwargs)
            }
        )
        error_info = handle_error(e, context)
        return False, None, error_info

# Example usage and testing
if __name__ == "__main__":
    print("Centralized Error Handler")
    print("=" * 30)
    
    # Test error handling
    try:
        # Simulate an error
        raise ValueError("Test error message")
    except Exception as e:
        context = ErrorContext(
            user_id="test_user",
            ip_address="127.0.0.1",
            command="test_command"
        )
        error_info = handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        print(f"Error handled: {error_info.error_id}")
    
    # Test error statistics
    stats = error_handler.get_error_statistics()
    print(f"Error statistics: {stats}")
    
    print("Error handler ready!")