"""Performance monitoring and optimization utilities."""

import asyncio
import time
from collections.abc import Callable
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, TypeVar

from utils.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class PerformanceMetrics:
    """Track performance metrics for operations."""

    def __init__(self) -> None:
        """Initialize metrics storage."""
        self.metrics: dict[str, list[float]] = {}

    def record(self, operation: str, duration: float) -> None:
        """Record operation duration."""
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(duration)
        logger.info("performance_recorded", operation=operation, duration_ms=duration * 1000)

    def get_stats(self, operation: str) -> dict[str, float]:
        """Get statistics for an operation."""
        if operation not in self.metrics or not self.metrics[operation]:
            return {}

        durations = self.metrics[operation]
        return {
            "count": len(durations),
            "total_ms": sum(durations) * 1000,
            "avg_ms": (sum(durations) / len(durations)) * 1000,
            "min_ms": min(durations) * 1000,
            "max_ms": max(durations) * 1000,
        }

    def clear(self, operation: str = None) -> None:
        """Clear metrics."""
        if operation:
            if operation in self.metrics:
                self.metrics[operation] = []
        else:
            self.metrics = {}


# Global metrics instance
metrics = PerformanceMetrics()


def track_performance(operation: str) -> Callable:
    """Decorator to track operation performance."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                metrics.record(operation, duration)
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(
                    "operation_failed",
                    operation=operation,
                    duration_ms=duration * 1000,
                    error=str(e),
                )
                raise

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                metrics.record(operation, duration)
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(
                    "operation_failed",
                    operation=operation,
                    duration_ms=duration * 1000,
                    error=str(e),
                )
                raise

        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


@asynccontextmanager
async def measure_performance(operation: str, **context: Any):
    """Context manager to measure operation performance."""
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        metrics.record(operation, duration)
        logger.info(
            "operation_complete",
            operation=operation,
            duration_ms=duration * 1000,
            **context,
        )


async def get_performance_report() -> dict[str, Any]:
    """Generate performance report."""
    report = {}
    for operation, durations in metrics.metrics.items():
        if durations:
            report[operation] = metrics.get_stats(operation)

    return report


class RateLimiter:
    """Rate limiter for operations."""

    def __init__(self, max_requests: int = 10, time_window: int = 60) -> None:
        """Initialize rate limiter."""
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: dict[str, list[float]] = {}

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed."""
        now = time.time()

        if key not in self.requests:
            self.requests[key] = []

        # Clean old requests
        self.requests[key] = [t for t in self.requests[key] if now - t < self.time_window]

        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            logger.warning(
                "rate_limit_exceeded",
                key=key,
                limit=self.max_requests,
                window_seconds=self.time_window,
            )
            return False

        # Record request
        self.requests[key].append(now)
        return True

    def reset(self, key: str = None) -> None:
        """Reset rate limiter."""
        if key:
            if key in self.requests:
                self.requests[key] = []
        else:
            self.requests = {}


class CacheManager:
    """Simple in-memory cache manager."""

    def __init__(self, ttl: int = 3600) -> None:
        """Initialize cache manager."""
        self.ttl = ttl
        self.cache: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Any:
        """Get value from cache."""
        if key not in self.cache:
            return None

        value, timestamp = self.cache[key]
        if time.time() - timestamp > self.ttl:
            del self.cache[key]
            return None

        logger.debug("cache_hit", key=key)
        return value

    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        self.cache[key] = (value, time.time())
        logger.debug("cache_set", key=key)

    def delete(self, key: str) -> None:
        """Delete value from cache."""
        if key in self.cache:
            del self.cache[key]

    def clear(self) -> None:
        """Clear entire cache."""
        self.cache = {}
        logger.info("cache_cleared")

    def get_stats(self) -> dict[str, int]:
        """Get cache statistics."""
        return {
            "cached_items": len(self.cache),
            "memory_bytes": sum(len(str(v[0])) for v in self.cache.values()),
        }


# Global cache instance
cache = CacheManager()


def cached(ttl: int = 3600) -> Callable:
    """Decorator to cache operation results."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result)
            return result

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            # Create cache key
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result

        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator
