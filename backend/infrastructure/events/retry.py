"""
FleetGuard — Retry Framework
A generic, extensible framework for handling transient infrastructure failures.
"""

import asyncio
import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Optional, Tuple, Type

from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("fleetguard.infrastructure.retry")

# =============================================================================
# Exceptions
# =============================================================================

class RetryFrameworkError(Exception):
    """Base exception for the Retry Framework."""
    pass

class NonRetryableError(RetryFrameworkError):
    """Raised when an error is classified as non-retryable."""
    def __init__(self, original_exception: Exception):
        self.original_exception = original_exception
        super().__init__(f"Non-retryable failure encountered: {original_exception}")

class RetriesExhaustedError(RetryFrameworkError):
    """Raised when the maximum number of retries is exhausted."""
    def __init__(self, original_exception: Exception, context: 'RetryContext'):
        self.original_exception = original_exception
        self.context = context
        super().__init__(f"Retries exhausted after {context.max_attempts} attempts. Last error: {original_exception}")


# =============================================================================
# Context
# =============================================================================

@dataclass
class RetryContext:
    """Tracks the state of an ongoing retry loop."""
    current_attempt: int = 1
    max_attempts: int = 0
    first_failure_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    last_exception: Optional[Exception] = None
    retry_delay: float = 0.0

    def record_failure(self, error: Exception, delay: float) -> None:
        """Updates the context with the latest failure."""
        now = datetime.now(timezone.utc)
        if self.first_failure_time is None:
            self.first_failure_time = now
        self.last_failure_time = now
        self.last_exception = error
        self.retry_delay = delay
        self.current_attempt += 1


# =============================================================================
# Strategies
# =============================================================================

class RetryStrategy(ABC):
    """Defines how to compute the delay before the next retry attempt."""
    
    @abstractmethod
    def compute_delay(self, context: RetryContext) -> float:
        pass


class FixedDelayStrategy(RetryStrategy):
    """Delays for a fixed amount of time between retries."""
    
    def __init__(self, delay_seconds: float):
        self.delay_seconds = delay_seconds
        
    def compute_delay(self, context: RetryContext) -> float:
        return self.delay_seconds


class ExponentialBackoffStrategy(RetryStrategy):
    """Delays exponentially, capping at a maximum delay."""
    
    def __init__(self, base_delay: float = 2.0, max_delay: float = 30.0, multiplier: float = 2.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        
    def compute_delay(self, context: RetryContext) -> float:
        # attempt 1 fails -> delay before attempt 2 is base_delay
        # attempt 2 fails -> delay before attempt 3 is base_delay * multiplier
        exponent = context.current_attempt - 1
        delay = self.base_delay * (self.multiplier ** exponent)
        return min(delay, self.max_delay)


class ExponentialBackoffWithJitterStrategy(RetryStrategy):
    """Delays exponentially, adding randomness to prevent thundering herds."""
    
    def __init__(self, base_delay: float = 2.0, max_delay: float = 30.0, multiplier: float = 2.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        
    def compute_delay(self, context: RetryContext) -> float:
        exponent = context.current_attempt - 1
        raw_delay = self.base_delay * (self.multiplier ** exponent)
        capped_delay = min(raw_delay, self.max_delay)
        
        # Jitter: Randomize the delay between 50% and 100% of the calculated backoff
        jittered_delay = capped_delay * random.uniform(0.5, 1.0)
        return jittered_delay


# =============================================================================
# Error Classification
# =============================================================================

class ErrorClassifier(ABC):
    """Determines if an exception is a transient, retryable failure."""
    
    @abstractmethod
    def is_retryable(self, error: Exception) -> bool:
        pass


class DefaultErrorClassifier(ErrorClassifier):
    """
    Default classification rules for FleetGuard infrastructure.
    Only explicit transient infrastructure errors are retryable.
    Generic exceptions default to False.
    """
    
    RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
        SQLAlchemyError,
        ConnectionError,
        TimeoutError,
        asyncio.TimeoutError,
    )
    
    def is_retryable(self, error: Exception) -> bool:
        # Default unknown exceptions to Non-Retryable
        return isinstance(error, self.RETRYABLE_EXCEPTIONS)


# =============================================================================
# Policy & Executor
# =============================================================================

@dataclass
class RetryPolicy:
    """Configuration for executing a retry loop."""
    max_attempts: int = 5
    strategy: RetryStrategy = field(default_factory=lambda: ExponentialBackoffWithJitterStrategy())
    classifier: ErrorClassifier = field(default_factory=lambda: DefaultErrorClassifier())


class RetryExecutor:
    """
    Executes a callable under a RetryPolicy.
    Completely transport-agnostic (knows nothing about Kafka).
    """
    
    def __init__(self, policy: RetryPolicy):
        self.policy = policy
        
    async def execute(self, coro_fn: Callable[..., Coroutine[Any, Any, Any]], *args: Any, **kwargs: Any) -> Any:
        """
        Executes the provided coroutine function with retries on transient failures.
        """
        context = RetryContext(max_attempts=self.policy.max_attempts)
        
        while context.current_attempt <= self.policy.max_attempts:
            try:
                # Attempt execution
                return await coro_fn(*args, **kwargs)
                
            except Exception as e:
                # 1. Classification
                if not self.policy.classifier.is_retryable(e):
                    logger.debug(f"RetryExecutor: Encountered NonRetryableError: {type(e).__name__} - {e}")
                    raise NonRetryableError(e) from e
                    
                # 2. Check exhaustion
                if context.current_attempt >= self.policy.max_attempts:
                    logger.warning(f"RetryExecutor: Retries exhausted ({self.policy.max_attempts}). Final error: {e}")
                    raise RetriesExhaustedError(e, context) from e
                    
                # 3. Calculate delay & Sleep
                delay = self.policy.strategy.compute_delay(context)
                context.record_failure(e, delay)
                
                logger.info(
                    f"RetryExecutor: Transient failure ({type(e).__name__}). "
                    f"Attempt {context.current_attempt - 1}/{self.policy.max_attempts}. "
                    f"Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
                
        # Fallback (should be unreachable due to Check Exhaustion above)
        raise RetriesExhaustedError(Exception("Unexpected loop exit"), context)
