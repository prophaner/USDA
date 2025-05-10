"""
Optional cache abstractions for service functions.
Currently, wraps functools.lru_cache, but you can
swap in Redis or another backend here.
"""
from functools import lru_cache
from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable)

def cached(maxsize: int = 128):
    """
    Decorator to cache service function results.
    Usage:

        @cached(maxsize=256)
        def my_service(...):
            ...
    """
    def decorator(fn: F) -> F:
        return lru_cache(maxsize=maxsize)(fn)  # type: ignore
    return decorator
