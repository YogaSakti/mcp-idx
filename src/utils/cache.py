"""Caching layer for IDX Stock MCP Server."""

from typing import Any, Optional
from datetime import datetime, timedelta
from cachetools import TTLCache
from src.config.settings import settings


class CacheManager:
    """Cache manager with TTL support."""

    def __init__(self):
        """Initialize cache manager."""
        self.enabled = settings.CACHE_ENABLED
        self.caches = {
            "price": TTLCache(maxsize=settings.CACHE_MAX_SIZE, ttl=60),  # 1 minute
            "historical_intraday": TTLCache(
                maxsize=settings.CACHE_MAX_SIZE, ttl=300
            ),  # 5 minutes
            "historical_daily": TTLCache(
                maxsize=settings.CACHE_MAX_SIZE, ttl=3600
            ),  # 1 hour
            "info": TTLCache(maxsize=settings.CACHE_MAX_SIZE, ttl=86400),  # 24 hours
            "search": TTLCache(maxsize=settings.CACHE_MAX_SIZE, ttl=21600),  # 6 hours
            "market": TTLCache(maxsize=settings.CACHE_MAX_SIZE, ttl=60),  # 1 minute
        }

    def get(self, cache_type: str, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            cache_type: Type of cache (price, historical_intraday, etc.)
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.enabled:
            return None

        cache = self.caches.get(cache_type)
        if cache is None:
            return None

        return cache.get(key)

    def set(self, cache_type: str, key: str, value: Any) -> None:
        """
        Set value in cache.

        Args:
            cache_type: Type of cache (price, historical_intraday, etc.)
            key: Cache key
            value: Value to cache
        """
        if not self.enabled:
            return

        cache = self.caches.get(cache_type)
        if cache is None:
            return

        cache[key] = value

    def clear(self, cache_type: Optional[str] = None) -> None:
        """
        Clear cache.

        Args:
            cache_type: Type of cache to clear, or None to clear all
        """
        if cache_type:
            cache = self.caches.get(cache_type)
            if cache:
                cache.clear()
        else:
            for cache in self.caches.values():
                cache.clear()

    def generate_key(self, *args: Any) -> str:
        """
        Generate cache key from arguments.

        Args:
            *args: Arguments to include in key

        Returns:
            Cache key string
        """
        return ":".join(str(arg) for arg in args)


# Global cache instance
cache_manager = CacheManager()

