"""
Optional cache abstractions for service functions.
Currently, wraps functools.lru_cache, but you can
swap in Redis or another backend here.
"""
from functools import wraps
import time
from typing import Dict, Any, Callable, TypeVar
from config import settings

F = TypeVar("F", bound=Callable)


# Simple TTL cache implementation
class TTLCache:
    def __init__(self, maxsize: int = 100, ttl: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.maxsize = maxsize
        self.ttl = ttl

    def get(self, key: str) -> Any:
        if key not in self.cache:
            return None

        entry = self.cache[key]
        if time.time() > entry["expires"]:
            del self.cache[key]
            return None

        return entry["value"]

    def set(self, key: str, value: Any) -> None:
        # Evict oldest if at capacity
        if len(self.cache) >= self.maxsize:
            oldest_key = min(self.cache.keys(),
                             key=lambda k: self.cache[k]["expires"])
            del self.cache[oldest_key]

        self.cache[key] = {
            "value": value,
            "expires": time.time() + self.ttl
        }


# Global cache instance
_cache = TTLCache(maxsize=settings.MAX_CACHE_SIZE)


def cached(ttl: int = 3600):
    """Cache decorator with TTL."""

    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_parts = [fn.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            key = ":".join(key_parts)

            # Check cache
            cached_value = _cache.get(key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = fn(*args, **kwargs)
            _cache.set(key, result)
            return result

        return wrapper  # type: ignore

    return decorator
