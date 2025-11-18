"""Error recovery and retry mechanisms for agents"""

import asyncio
from typing import Any, Callable, Optional, Type, Tuple
from functools import wraps
import time

from .logger import get_logger

logger = get_logger(__name__)


class RetryStrategy:
    """Retry strategy configuration"""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        """
        Initialize retry strategy

        Args:
            max_attempts: Maximum retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Add random jitter to delays
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )

        if self.jitter:
            import random
            delay *= (0.5 + random.random())

        return delay


def retry_async(
    max_attempts: int = 3,
    retry_on: Tuple[Type[Exception], ...] = (Exception,),
    strategy: Optional[RetryStrategy] = None
):
    """
    Decorator for async functions with retry logic

    Args:
        max_attempts: Maximum retry attempts
        retry_on: Tuple of exception types to retry on
        strategy: Custom retry strategy

    Returns:
        Decorated function
    """
    if strategy is None:
        strategy = RetryStrategy(max_attempts=max_attempts)

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(strategy.max_attempts):
                try:
                    return await func(*args, **kwargs)

                except retry_on as e:
                    last_exception = e

                    if attempt < strategy.max_attempts - 1:
                        delay = strategy.get_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{strategy.max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {strategy.max_attempts} attempts failed for {func.__name__}: {e}"
                        )

            raise last_exception

        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures.

    States: CLOSED (normal), OPEN (failing), HALF_OPEN (testing)
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of failures before opening
            recovery_timeout: Seconds before attempting recovery
            success_threshold: Successes needed to close circuit
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker

        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == "OPEN":
            if time.time() - self.last_failure_time < self.recovery_timeout:
                raise Exception(f"Circuit breaker is OPEN. Retry after {self.recovery_timeout}s")
            else:
                self.state = "HALF_OPEN"
                self.success_count = 0
                logger.info("Circuit breaker entering HALF_OPEN state")

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result

        except Exception as e:
            await self._on_failure()
            raise

    async def _on_success(self):
        """Handle successful execution"""
        self.failure_count = 0

        if self.state == "HALF_OPEN":
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = "CLOSED"
                logger.info("Circuit breaker CLOSED after recovery")

    async def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(f"Circuit breaker OPEN after {self.failure_count} failures")

        if self.state == "HALF_OPEN":
            self.state = "OPEN"
            logger.warning("Circuit breaker reopened during recovery")


class ErrorRecoveryManager:
    """Manages error recovery strategies for agents"""

    def __init__(self):
        """Initialize error recovery manager"""
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.error_history: list[dict] = []

    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """
        Get or create circuit breaker

        Args:
            name: Circuit breaker name

        Returns:
            Circuit breaker instance
        """
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker()
        return self.circuit_breakers[name]

    async def execute_with_recovery(
        self,
        func: Callable,
        *args,
        circuit_breaker_name: Optional[str] = None,
        retry_strategy: Optional[RetryStrategy] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with full error recovery

        Args:
            func: Async function to execute
            circuit_breaker_name: Optional circuit breaker to use
            retry_strategy: Optional retry strategy
            *args, **kwargs: Function arguments

        Returns:
            Function result
        """
        # Wrap with retry
        if retry_strategy:
            @retry_async(strategy=retry_strategy)
            async def retry_wrapper():
                return await func(*args, **kwargs)

            func_to_call = retry_wrapper
        else:
            async def no_retry():
                return await func(*args, **kwargs)
            func_to_call = no_retry

        # Wrap with circuit breaker
        if circuit_breaker_name:
            breaker = self.get_circuit_breaker(circuit_breaker_name)
            return await breaker.call(func_to_call)
        else:
            return await func_to_call()

    def record_error(
        self,
        error: Exception,
        context: dict[str, Any]
    ):
        """
        Record error for analysis

        Args:
            error: Exception that occurred
            context: Error context
        """
        self.error_history.append({
            "error": str(error),
            "type": type(error).__name__,
            "context": context,
            "timestamp": time.time()
        })

        # Keep only recent errors
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]

        logger.error(f"Recorded error: {error}")

    def get_error_stats(self) -> dict[str, Any]:
        """
        Get error statistics

        Returns:
            Error statistics
        """
        if not self.error_history:
            return {"total_errors": 0}

        error_types = {}
        for error in self.error_history:
            error_type = error["type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1

        recent_errors = [e for e in self.error_history if time.time() - e["timestamp"] < 3600]

        return {
            "total_errors": len(self.error_history),
            "recent_errors_1h": len(recent_errors),
            "error_types": error_types,
            "circuit_breakers": {
                name: breaker.state
                for name, breaker in self.circuit_breakers.items()
            }
        }
