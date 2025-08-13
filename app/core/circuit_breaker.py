import asyncio
import time
from enum import Enum
from typing import Callable, Optional, Any, TypeVar, Union
from functools import wraps
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: int = 60
    expected_exception: type = Exception
    success_threshold: int = 2


class CircuitBreaker:
    def __init__(self, config: CircuitBreakerConfig = None):
        self.config = config or CircuitBreakerConfig()
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.success_count = 0
        self._lock = asyncio.Lock()

    async def _record_success(self):
        async with self._lock:
            self.failure_count = 0
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.success_count = 0
                    logger.info("Circuit breaker closed after successful recovery")

    async def _record_failure(self):
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            self.success_count = 0
            
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

    async def _check_state(self):
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self.last_failure_time and \
                   time.time() - self.last_failure_time >= self.config.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info("Circuit breaker moved to half-open state")
                    return True
                return False
            return True

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not await self._check_state():
                raise Exception("Circuit breaker is open")
            
            try:
                result = await func(*args, **kwargs)
                await self._record_success()
                return result
            except self.config.expected_exception as e:
                await self._record_failure()
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we use a simplified approach
            if self.state == CircuitState.OPEN:
                if self.last_failure_time and \
                   time.time() - self.last_failure_time >= self.config.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise Exception("Circuit breaker is open")
            
            try:
                result = func(*args, **kwargs)
                self.failure_count = 0
                if self.state == CircuitState.HALF_OPEN:
                    self.success_count += 1
                    if self.success_count >= self.config.success_threshold:
                        self.state = CircuitState.CLOSED
                        self.success_count = 0
                return result
            except self.config.expected_exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                self.success_count = 0
                if self.failure_count >= self.config.failure_threshold:
                    self.state = CircuitState.OPEN
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    def is_open(self) -> bool:
        """Check if circuit breaker is currently open"""
        if self.state == CircuitState.OPEN:
            if self.last_failure_time and \
               time.time() - self.last_failure_time >= self.config.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return False
            return True
        return False

    def is_closed(self) -> bool:
        """Check if circuit breaker is currently closed"""
        return self.state == CircuitState.CLOSED

    def reset(self):
        """Manually reset the circuit breaker"""
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def force_open(self):
        """Manually open the circuit breaker"""
        self.state = CircuitState.OPEN
        self.last_failure_time = time.time()


# Global circuit breaker instance
circuit_breaker = CircuitBreaker()