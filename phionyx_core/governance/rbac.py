"""
RBAC — Role-Based Access Control (v4 §6.1)
==============================================

Module-level permission matrix for the 14 v4 modules.
Each port method call is checked against RBAC before execution.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """Permission types."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"


class Role(str, Enum):
    """System roles."""
    PERCEPTION = "perception_engine"
    WORLD_MODEL = "world_model"
    KNOWLEDGE = "knowledge_base"
    MEMORY = "memory_store"
    ATTENTION = "attention_controller"
    INTELLIGENCE = "intelligence_core"
    GOAL_MANAGER = "goal_manager"
    SELF_MODEL = "self_model"
    METACOGNITION = "metacognition"
    CONSCIOUSNESS = "consciousness_integrator"
    ETHICS = "ethics_engine"
    EXECUTOR = "action_executor"
    LEARNING = "learning_engine"
    DISCOVERY = "open_ended_discovery"
    ADMIN = "admin"


# Default permission matrix (v4 §6.1)
# Format: {module: {target_module: {permissions}}}
DEFAULT_PERMISSION_MATRIX: dict[str, dict[str, set[str]]] = {
    "perception_engine": {
        "world_model": {"read", "write"},
        "memory_store": {"read"},
        "attention_controller": {"write"},
    },
    "world_model": {
        "memory_store": {"read"},
        "knowledge_base": {"read"},
    },
    "knowledge_base": {
        "memory_store": {"read", "write"},
    },
    "memory_store": {
        "knowledge_base": {"read"},
    },
    "attention_controller": {
        "consciousness_integrator": {"write"},
        "perception_engine": {"read"},
    },
    "intelligence_core": {
        "world_model": {"read"},
        "memory_store": {"read"},
        "knowledge_base": {"read"},
        "goal_manager": {"read", "write"},
        "ethics_engine": {"execute"},
    },
    "goal_manager": {
        "intelligence_core": {"read"},
        "ethics_engine": {"execute"},
        "self_model": {"read"},
    },
    "self_model": {
        "metacognition": {"read", "write"},
        "world_model": {"read"},
    },
    "metacognition": {
        "self_model": {"read"},
        "intelligence_core": {"read"},
    },
    "consciousness_integrator": {
        "attention_controller": {"read"},
        "world_model": {"read"},
        "perception_engine": {"read"},
    },
    "ethics_engine": {
        "world_model": {"read"},
        "goal_manager": {"read", "write"},
        "action_executor": {"execute"},
        "intelligence_core": {"read"},
    },
    "action_executor": {
        "ethics_engine": {"execute"},
        "world_model": {"read", "write"},
    },
    "learning_engine": {
        "memory_store": {"read", "write"},
        "knowledge_base": {"read", "write"},
        "self_model": {"read", "write"},
    },
    "open_ended_discovery": {
        "knowledge_base": {"read"},
        "memory_store": {"read"},
    },
    "admin": {
        # Admin has all permissions
    },
}


@dataclass
class RBACManager:
    """
    RBAC permission manager.

    Checks caller module permissions before port method invocation.
    """
    permission_matrix: dict[str, dict[str, set[str]]] = field(
        default_factory=lambda: dict(DEFAULT_PERMISSION_MATRIX)
    )
    audit_log: list = field(default_factory=list)
    max_audit_size: int = 10000

    def check_permission(
        self,
        caller_module: str,
        target_module: str,
        permission: str,
    ) -> bool:
        """
        Check if caller has permission on target.

        Args:
            caller_module: Module requesting access
            target_module: Module being accessed
            permission: Permission type (read/write/execute)

        Returns:
            True if permitted, False otherwise
        """
        # Admin has all permissions
        if caller_module == "admin":
            self._audit("ALLOW", caller_module, target_module, permission)
            return True

        # Same module always allowed
        if caller_module == target_module:
            return True

        # Check matrix
        caller_perms = self.permission_matrix.get(caller_module, {})
        target_perms = caller_perms.get(target_module, set())
        allowed = permission in target_perms

        status = "ALLOW" if allowed else "DENY"
        self._audit(status, caller_module, target_module, permission)

        if not allowed:
            logger.warning(
                f"RBAC DENY: {caller_module} → {target_module}.{permission}"
            )

        return allowed

    def grant(
        self,
        caller_module: str,
        target_module: str,
        permissions: set[str],
    ) -> None:
        """Grant permissions to a module."""
        if caller_module not in self.permission_matrix:
            self.permission_matrix[caller_module] = {}
        if target_module not in self.permission_matrix[caller_module]:
            self.permission_matrix[caller_module][target_module] = set()
        self.permission_matrix[caller_module][target_module].update(permissions)

    def revoke(
        self,
        caller_module: str,
        target_module: str,
        permissions: set[str] | None = None,
    ) -> None:
        """Revoke permissions from a module."""
        if caller_module in self.permission_matrix:
            if permissions is None:
                self.permission_matrix[caller_module].pop(target_module, None)
            elif target_module in self.permission_matrix[caller_module]:
                self.permission_matrix[caller_module][target_module] -= permissions

    def _audit(self, status: str, caller: str, target: str, perm: str) -> None:
        """Log RBAC decision."""
        self.audit_log.append({
            "status": status,
            "caller": caller,
            "target": target,
            "permission": perm,
        })
        if len(self.audit_log) > self.max_audit_size:
            self.audit_log = self.audit_log[-self.max_audit_size:]
