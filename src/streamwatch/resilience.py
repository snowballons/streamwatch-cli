"""
StreamWatch Resilience Module

This module provides error recovery strategies including retry logic with exponential backoff
and circuit breaker patterns for robust handling of streamlink operations.
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, Union

from . import config
from .exceptions import AuthenticationError, NetworkError, StreamlinkError, TimeoutError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class RetryConfig:
    """Configuration for retry logic."""

    max_attempts: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0  # Maximum delay in seconds
    exponential_base: float = 2.0  # Exponential backoff multiplier
    jitter: bool = True  # Add random jitter to prevent thundering herd


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Number of failures before opening circuit
    recovery_timeout: float = 60.0  # Time to wait before trying half-open
    success_threshold: int = 2  # Successes needed in half-open to close circuit


@dataclass
class CircuitBreakerState:
    """Internal state of a circuit breaker."""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    next_attempt_time: float = 0.0


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""

    def __init__(self, message: str = "Circuit breaker is open"):
        super().__init__(message)


class RetryableOperation:
    """
    Handles retry logic with exponential backoff for operations.
    """

    def __init__(self, retry_config: Optional[RetryConfig] = None):
        """
        Initialize RetryableOperation.

        Args:
            retry_config: Configuration for retry behavior
        """
        self.config = retry_config or RetryConfig()

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if an operation should be retried based on the exception type.

        Args:
            exception: The exception that occurred
            attempt: Current attempt number (1-based)

        Returns:
            bool: True if the operation should be retried
        """
        if attempt >= self.config.max_attempts:
            return False

        # Retry on network errors and timeouts, but not on authentication errors
        # or stream not found errors (those are likely permanent)
        if isinstance(exception, (NetworkError, TimeoutError)):
            return True
        elif isinstance(exception, AuthenticationError):
            return False  # Don't retry auth errors
        elif isinstance(exception, StreamlinkError):
            # For generic streamlink errors, retry a few times
            return attempt <= 2
        else:
            # For unexpected errors, retry once
            return attempt == 1

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay before next retry attempt.

        Args:
            attempt: Current attempt number (1-based)

        Returns:
            float: Delay in seconds
        """
        delay = min(
            self.config.base_delay * (self.config.exponential_base ** (attempt - 1)),
            self.config.max_delay,
        )

        if self.config.jitter:
            # Add ±25% jitter to prevent thundering herd
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)

    def execute(
        self, operation: Callable[[], T], operation_name: str = "operation"
    ) -> T:
        """
        Execute an operation with retry logic.

        Args:
            operation: The operation to execute
            operation_name: Name for logging purposes

        Returns:
            T: Result of the operation

        Raises:
            Exception: The last exception if all retries fail
        """
        last_exception = None

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                logger.debug(
                    f"Executing {operation_name}, attempt {attempt}/{self.config.max_attempts}"
                )
                result = operation()

                if attempt > 1:
                    logger.info(f"{operation_name} succeeded on attempt {attempt}")

                return result

            except Exception as e:
                last_exception = e

                if not self.should_retry(e, attempt):
                    logger.warning(
                        f"{operation_name} failed on attempt {attempt}, not retrying: {e}"
                    )
                    break

                if attempt < self.config.max_attempts:
                    delay = self.calculate_delay(attempt)
                    logger.warning(
                        f"{operation_name} failed on attempt {attempt}, retrying in {delay:.2f}s: {e}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"{operation_name} failed on final attempt {attempt}: {e}"
                    )

        # All retries exhausted
        raise last_exception


class CircuitBreaker:
    """
    Circuit breaker implementation for failing operations.
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize CircuitBreaker.

        Args:
            name: Name of the circuit breaker for logging
            config: Configuration for circuit breaker behavior
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState()

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker."""
        return (
            self.state.state == CircuitState.OPEN
            and time.time() >= self.state.next_attempt_time
        )

    def _record_success(self):
        """Record a successful operation."""
        if self.state.state == CircuitState.HALF_OPEN:
            self.state.success_count += 1
            if self.state.success_count >= self.config.success_threshold:
                logger.info(
                    f"Circuit breaker '{self.name}' closing after successful recovery"
                )
                self.state.state = CircuitState.CLOSED
                self.state.failure_count = 0
                self.state.success_count = 0
        elif self.state.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.state.failure_count = 0

    def _record_failure(self, exception: Exception):
        """Record a failed operation."""
        self.state.failure_count += 1
        self.state.last_failure_time = time.time()

        if self.state.state == CircuitState.CLOSED:
            if self.state.failure_count >= self.config.failure_threshold:
                logger.warning(
                    f"Circuit breaker '{self.name}' opening after {self.state.failure_count} failures"
                )
                self.state.state = CircuitState.OPEN
                self.state.next_attempt_time = (
                    time.time() + self.config.recovery_timeout
                )
        elif self.state.state == CircuitState.HALF_OPEN:
            logger.warning(
                f"Circuit breaker '{self.name}' reopening after failed recovery attempt"
            )
            self.state.state = CircuitState.OPEN
            self.state.success_count = 0
            self.state.next_attempt_time = time.time() + self.config.recovery_timeout

    def execute(
        self, operation: Callable[[], T], operation_name: str = "operation"
    ) -> T:
        """
        Execute an operation through the circuit breaker.

        Args:
            operation: The operation to execute
            operation_name: Name for logging purposes

        Returns:
            T: Result of the operation

        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            Exception: Any exception from the operation
        """
        # Check if circuit should transition to half-open
        if self._should_attempt_reset():
            logger.info(
                f"Circuit breaker '{self.name}' transitioning to half-open for recovery test"
            )
            self.state.state = CircuitState.HALF_OPEN
            self.state.success_count = 0

        # Fail fast if circuit is open
        if self.state.state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is open. "
                f"Next attempt allowed at {time.ctime(self.state.next_attempt_time)}"
            )

        try:
            result = operation()
            self._record_success()
            return result
        except Exception as e:
            self._record_failure(e)
            raise

    def get_state_info(self) -> Dict[str, Any]:
        """Get current state information for monitoring."""
        return {
            "name": self.name,
            "state": self.state.state.value,
            "failure_count": self.state.failure_count,
            "success_count": self.state.success_count,
            "last_failure_time": self.state.last_failure_time,
            "next_attempt_time": (
                self.state.next_attempt_time
                if self.state.state == CircuitState.OPEN
                else None
            ),
        }


# Global circuit breakers for different operations
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str, config: Optional[CircuitBreakerConfig] = None
) -> CircuitBreaker:
    """
    Get or create a circuit breaker for a named operation.

    Args:
        name: Name of the circuit breaker
        config: Configuration for the circuit breaker

    Returns:
        CircuitBreaker: The circuit breaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]


def resilient_operation(
    operation_name: str,
    retry_config: Optional[RetryConfig] = None,
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
    use_circuit_breaker: bool = True,
):
    """
    Decorator to make operations resilient with retry logic and circuit breaker.

    Args:
        operation_name: Name of the operation for logging
        retry_config: Configuration for retry behavior
        circuit_breaker_config: Configuration for circuit breaker
        use_circuit_breaker: Whether to use circuit breaker pattern
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            retry_handler = RetryableOperation(retry_config)

            def execute_operation():
                if use_circuit_breaker:
                    circuit_breaker = get_circuit_breaker(
                        operation_name, circuit_breaker_config
                    )
                    return circuit_breaker.execute(
                        lambda: func(*args, **kwargs), operation_name
                    )
                else:
                    return func(*args, **kwargs)

            return retry_handler.execute(execute_operation, operation_name)

        return wrapper

    return decorator
