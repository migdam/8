"""Caching utilities for agent responses and tool results"""

from typing import Any, Optional, Callable
import hashlib
import json
import time
from functools import wraps
import asyncio

from .logger import get_logger

logger = get_logger(__name__)


class Cache:
    """Simple in-memory cache with TTL support"""

    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache

        Args:
            default_ttl: Default time-to-live in seconds
        """
        self.default_ttl = default_ttl
        self.cache: dict[str, dict[str, Any]] = {}

    def _is_expired(self, entry: dict[str, Any]) -> bool:
        """Check if cache entry is expired"""
        if entry["ttl"] == 0:  # Never expires
            return False
        return time.time() > entry["expires_at"]

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if key not in self.cache:
            return None

        entry = self.cache[key]

        if self._is_expired(entry):
            del self.cache[key]
            logger.debug(f"Cache expired: {key}")
            return None

        entry["hits"] += 1
        entry["last_accessed"] = time.time()
        logger.debug(f"Cache hit: {key}")
        return entry["value"]

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = use default, 0 = never expire)
        """
        if ttl is None:
            ttl = self.default_ttl

        now = time.time()
        self.cache[key] = {
            "value": value,
            "ttl": ttl,
            "created_at": now,
            "expires_at": now + ttl if ttl > 0 else float('inf'),
            "last_accessed": now,
            "hits": 0
        }

        logger.debug(f"Cache set: {key} (TTL: {ttl}s)")

    def delete(self, key: str):
        """Delete entry from cache"""
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"Cache deleted: {key}")

    def clear(self):
        """Clear entire cache"""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"Cache cleared: {count} entries")

    def cleanup_expired(self):
        """Remove expired entries"""
        expired = [
            key for key, entry in self.cache.items()
            if self._is_expired(entry)
        ]

        for key in expired:
            del self.cache[key]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired cache entries")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        total_hits = sum(entry["hits"] for entry in self.cache.values())

        return {
            "size": len(self.cache),
            "total_hits": total_hits,
            "keys": list(self.cache.keys())
        }


def _make_cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments"""
    key_data = {
        "args": str(args),
        "kwargs": str(sorted(kwargs.items()))
    }
    key_str = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()


def cached(
    cache: Cache,
    ttl: Optional[int] = None,
    key_func: Optional[Callable] = None
):
    """
    Decorator to cache async function results

    Args:
        cache: Cache instance
        ttl: Time-to-live in seconds
        key_func: Optional function to generate cache key

    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{_make_cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            cache.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator


class ResponseCache:
    """Specialized cache for LLM responses"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize response cache

        Args:
            max_size: Maximum cache entries
            default_ttl: Default TTL in seconds
        """
        self.cache = Cache(default_ttl=default_ttl)
        self.max_size = max_size

    def _evict_oldest(self):
        """Evict oldest entries when cache is full"""
        if len(self.cache.cache) <= self.max_size:
            return

        # Sort by last accessed time
        entries = sorted(
            self.cache.cache.items(),
            key=lambda x: x[1]["last_accessed"]
        )

        # Remove oldest 10%
        to_remove = max(1, len(entries) // 10)
        for key, _ in entries[:to_remove]:
            self.cache.delete(key)

        logger.info(f"Evicted {to_remove} cache entries")

    def cache_response(
        self,
        prompt: str,
        response: str,
        model: str,
        ttl: Optional[int] = None
    ):
        """
        Cache an LLM response

        Args:
            prompt: Input prompt
            response: LLM response
            model: Model name
            ttl: Time-to-live
        """
        # Create cache key from prompt and model
        key_data = f"{model}:{prompt}"
        cache_key = hashlib.md5(key_data.encode()).hexdigest()

        self.cache.set(cache_key, response, ttl)
        self._evict_oldest()

    def get_cached_response(
        self,
        prompt: str,
        model: str
    ) -> Optional[str]:
        """
        Get cached response

        Args:
            prompt: Input prompt
            model: Model name

        Returns:
            Cached response or None
        """
        key_data = f"{model}:{prompt}"
        cache_key = hashlib.md5(key_data.encode()).hexdigest()

        return self.cache.get(cache_key)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        return self.cache.get_stats()
