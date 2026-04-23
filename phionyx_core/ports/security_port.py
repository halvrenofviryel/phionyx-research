"""
Security Port — v4 §6
========================

Port interface for security services (AD-2: port-adapter pattern).
"""

from abc import ABC, abstractmethod


class SecurityPort(ABC):
    """Abstract port for security operations."""

    @abstractmethod
    def check_permission(self, caller: str, target: str, permission: str) -> bool:
        """Check RBAC permission."""
        ...

    @abstractmethod
    def sign_data(self, data: str) -> str:
        """Sign data with Ed25519."""
        ...

    @abstractmethod
    def verify_signature(self, data: str, signature: str) -> bool:
        """Verify Ed25519 signature."""
        ...

    @abstractmethod
    def check_kill_switch(self) -> bool:
        """Check if system can proceed (kill switch not active)."""
        ...


class NullSecurityPort(SecurityPort):
    """Null implementation — all operations allowed, no signing."""

    def check_permission(self, caller: str, target: str, permission: str) -> bool:
        return True

    def sign_data(self, data: str) -> str:
        return ""

    def verify_signature(self, data: str, signature: str) -> bool:
        return True

    def check_kill_switch(self) -> bool:
        return True
