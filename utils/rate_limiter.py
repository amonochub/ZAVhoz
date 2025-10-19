"""Rate limiting utilities with support for both in-memory and Redis backends."""

import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiterBackend(ABC):
    """Abstract base class for rate limiter backends."""

    @abstractmethod
    async def is_allowed(
        self, user_id: int, action: str = "default", max_requests: int = 5, time_window: int = 60
    ) -> bool:
        """Check if a request is allowed under rate limit.

        Args:
            user_id: User ID
            action: Action name for grouping
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds

        Returns:
            True if request is allowed, False otherwise
        """
        pass


class MemoryRateLimiter(RateLimiterBackend):
    """In-memory rate limiter (single instance only)."""

    def __init__(self) -> None:
        """Initialize in-memory rate limiter."""
        self.requests: dict[str, list[float]] = {}

    async def is_allowed(
        self, user_id: int, action: str = "default", max_requests: int = 5, time_window: int = 60
    ) -> bool:
        """Check if request is allowed.

        Args:
            user_id: User ID
            action: Action name for grouping
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds

        Returns:
            True if request is allowed, False otherwise
        """
        key = f"{user_id}_{action}"
        current_time = time.time()

        if key not in self.requests:
            self.requests[key] = []

        # Clean old requests
        self.requests[key] = [t for t in self.requests[key] if current_time - t < time_window]

        # Check limit
        if len(self.requests[key]) >= max_requests:
            logger.warning(f"Rate limit exceeded for {key}")
            return False

        # Add current request
        self.requests[key].append(current_time)
        return True


class RedisRateLimiter(RateLimiterBackend):
    """Redis-backed rate limiter (distributed, production-ready)."""

    def __init__(self, redis_url: Optional[str] = None) -> None:
        """Initialize Redis rate limiter.

        Args:
            redis_url: Redis connection URL (optional, uses env var if not provided)
        """
        import redis.asyncio as redis

        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)

    async def is_allowed(
        self, user_id: int, action: str = "default", max_requests: int = 5, time_window: int = 60
    ) -> bool:
        """Check if request is allowed using Redis.

        Args:
            user_id: User ID
            action: Action name for grouping
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds

        Returns:
            True if request is allowed, False otherwise
        """
        try:
            key = f"rate_limit:{user_id}:{action}"
            current = await self.redis_client.incr(key)

            if current == 1:
                # Set expiration only on first request in window
                await self.redis_client.expire(key, time_window)

            if current > max_requests:
                logger.warning(f"Rate limit exceeded for {key}")
                return False

            return True
        except Exception as e:
            logger.error(f"Redis rate limiter error: {e}", exc_info=True)
            # Fail open - allow request if Redis is down
            return True

    async def close(self) -> None:
        """Close Redis connection."""
        await self.redis_client.close()


def get_rate_limiter() -> RateLimiterBackend:
    """Factory function to get appropriate rate limiter based on configuration.

    Returns:
        RateLimiterBackend instance (Redis or in-memory)
    """
    redis_url = os.getenv("REDIS_URL")

    if redis_url:
        logger.info("Using Redis rate limiter for distributed deployments")
        try:
            return RedisRateLimiter(redis_url)
        except Exception as e:
            logger.error(f"Failed to initialize Redis rate limiter: {e}, falling back to in-memory")
            return MemoryRateLimiter()
    else:
        logger.info("Using in-memory rate limiter (single instance)")
        return MemoryRateLimiter()


# Global rate limiter instance
rate_limiter = get_rate_limiter()
