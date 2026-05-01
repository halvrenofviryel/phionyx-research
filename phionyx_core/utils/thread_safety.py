"""
Thread Safety Utilities
========================

Utilities for thread-safe operations in multi-tenant environments.
"""

import logging
import threading
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ThreadSafeDict:
    """
    Thread-safe dictionary wrapper.

    Provides thread-safe operations for dictionary access in multi-tenant environments.
    """

    def __init__(self, *args, **kwargs):
        """Initialize thread-safe dictionary."""
        self._dict = dict(*args, **kwargs)
        self._lock = threading.RLock()

    def __getitem__(self, key: str) -> Any:
        """Thread-safe get item."""
        with self._lock:
            return self._dict[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Thread-safe set item."""
        with self._lock:
            self._dict[key] = value

    def __delitem__(self, key: str) -> None:
        """Thread-safe delete item."""
        with self._lock:
            del self._dict[key]

    def __contains__(self, key: str) -> bool:
        """Thread-safe contains check."""
        with self._lock:
            return key in self._dict

    def get(self, key: str, default: Any = None) -> Any:
        """Thread-safe get with default."""
        with self._lock:
            return self._dict.get(key, default)

    def update(self, other: dict) -> None:
        """Thread-safe update."""
        with self._lock:
            self._dict.update(other)

    def keys(self):
        """Thread-safe keys iterator (returns snapshot)."""
        with self._lock:
            return list(self._dict.keys())

    def values(self):
        """Thread-safe values iterator (returns snapshot)."""
        with self._lock:
            return list(self._dict.values())

    def items(self):
        """Thread-safe items iterator (returns snapshot)."""
        with self._lock:
            return list(self._dict.items())

    def copy(self) -> dict:
        """Thread-safe copy."""
        with self._lock:
            return self._dict.copy()

    def clear(self) -> None:
        """Thread-safe clear."""
        with self._lock:
            self._dict.clear()


class ThreadSafeList:
    """
    Thread-safe list wrapper.

    Provides thread-safe operations for list access in multi-tenant environments.
    """

    def __init__(self, *args):
        """Initialize thread-safe list."""
        self._list = list(*args)
        self._lock = threading.RLock()

    def __getitem__(self, index: int) -> Any:
        """Thread-safe get item."""
        with self._lock:
            return self._list[index]

    def __setitem__(self, index: int, value: Any) -> None:
        """Thread-safe set item."""
        with self._lock:
            self._list[index] = value

    def __len__(self) -> int:
        """Thread-safe length."""
        with self._lock:
            return len(self._list)

    def append(self, item: Any) -> None:
        """Thread-safe append."""
        with self._lock:
            self._list.append(item)

    def extend(self, items: list[Any]) -> None:
        """Thread-safe extend."""
        with self._lock:
            self._list.extend(items)

    def insert(self, index: int, item: Any) -> None:
        """Thread-safe insert."""
        with self._lock:
            self._list.insert(index, item)

    def remove(self, item: Any) -> None:
        """Thread-safe remove."""
        with self._lock:
            self._list.remove(item)

    def pop(self, index: int = -1) -> Any:
        """Thread-safe pop."""
        with self._lock:
            return self._list.pop(index)

    def clear(self) -> None:
        """Thread-safe clear."""
        with self._lock:
            self._list.clear()

    def copy(self) -> list:
        """Thread-safe copy."""
        with self._lock:
            return self._list.copy()


def synchronized(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for thread-safe function execution.

    Usage:
        @synchronized
        def my_function():
            # Thread-safe code
            pass
    """
    func.__lock__ = threading.RLock()

    @wraps(func)
    def wrapper(*args, **kwargs):
        with func.__lock__:
            return func(*args, **kwargs)

    return wrapper


class SessionLocalStorage:
    """
    Thread-local storage for session-based state isolation.

    Provides per-session state isolation in multi-tenant environments.
    """

    def __init__(self):
        """Initialize session-local storage."""
        self._local = threading.local()

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from thread-local storage.

        Args:
            key: Storage key
            default: Default value if key not found

        Returns:
            Stored value or default
        """
        storage = getattr(self._local, 'storage', None)
        if storage is None:
            return default
        return storage.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set value in thread-local storage.

        Args:
            key: Storage key
            value: Value to store
        """
        if not hasattr(self._local, 'storage'):
            self._local.storage = {}
        self._local.storage[key] = value

    def clear(self) -> None:
        """Clear thread-local storage."""
        if hasattr(self._local, 'storage'):
            self._local.storage.clear()

    def get_all(self) -> dict:
        """
        Get all thread-local storage.

        Returns:
            Dictionary of all stored values
        """
        storage = getattr(self._local, 'storage', None)
        if storage is None:
            return {}
        return storage.copy()

