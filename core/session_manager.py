"""
Session management abstraction - Framework-agnostic.

Provides an abstract interface for session state management that can be
implemented by different frameworks (Streamlit, Chainlit, etc.).
"""

from typing import Any, Optional, Protocol
from abc import ABC, abstractmethod


class SessionManager(Protocol):
    """
    Protocol for session state management.
    
    This allows different frameworks to implement their own session managers
    while maintaining a consistent interface.
    """
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from session state."""
        ...
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in session state."""
        ...
    
    def has(self, key: str) -> bool:
        """Check if a key exists in session state."""
        ...


class BaseSessionManager:
    """
    Base implementation of session manager using a dictionary.
    
    Can be used for testing or as a fallback.
    """
    
    def __init__(self, initial_state: Optional[dict] = None):
        self._state = initial_state or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from session state."""
        return self._state.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in session state."""
        self._state[key] = value
    
    def has(self, key: str) -> bool:
        """Check if a key exists in session state."""
        return key in self._state
    
    def clear(self) -> None:
        """Clear all session state."""
        self._state.clear()

