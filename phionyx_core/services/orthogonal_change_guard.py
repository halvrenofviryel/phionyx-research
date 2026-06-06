"""
Orthogonal Change Guard
=======================

Faz 3.1: Kalan Özellikler

Kod dışı etki / değişiklik kontrolü.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import re


@dataclass
class OrthogonalChange:
    """Orthogonal change detection."""
    type: str  # "file_modification", "dependency_change", "config_change", "side_effect"
    description: str
    affected_files: List[str]
    severity: str  # "low", "medium", "high", "critical"
    suggestion: str


class OrthogonalChangeGuard:
    """
    Full-featured Orthogonal Change Guard.

    Provides:
    - Side effect detection
    - File modification tracking
    - Dependency change detection
    - Configuration change detection
    """

    def __init__(self):
        """Initialize orthogonal change guard."""
        self.detected_changes: List[OrthogonalChange] = []
        self.file_registry: Set[str] = set()

    def check_orthogonal_changes(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[OrthogonalChange]:
        """
        Check for orthogonal changes (side effects).

        Args:
            code: Code string to analyze
            context: Additional context (optional)

        Returns:
            List of OrthogonalChange
        """
        changes = []

        # 1. Check for file modifications
        file_changes = self._detect_file_modifications(code)
        changes.extend(file_changes)

        # 2. Check for dependency changes
        dep_changes = self._detect_dependency_changes(code)
        changes.extend(dep_changes)

        # 3. Check for configuration changes
        config_changes = self._detect_config_changes(code)
        changes.extend(config_changes)

        # 4. Check for side effects
        side_effects = self._detect_side_effects(code)
        changes.extend(side_effects)

        self.detected_changes.extend(changes)
        return changes

    def _detect_file_modifications(self, code: str) -> List[OrthogonalChange]:
        """Detect file modification operations."""
        changes = []

        # Look for file operations
        file_operations = [
            (r'open\s*\([^)]+["\']w', "file_modification", "File write operation detected"),
            (r'open\s*\([^)]+["\']a', "file_modification", "File append operation detected"),
            (r'\.write\s*\(', "file_modification", "File write method detected"),
            (r'\.writelines\s*\(', "file_modification", "File writelines method detected"),
            (r'os\.remove\s*\(', "file_modification", "File removal operation detected"),
            (r'os\.unlink\s*\(', "file_modification", "File unlink operation detected"),
            (r'shutil\.', "file_modification", "File system operation detected"),
        ]

        for pattern, change_type, description in file_operations:
            if re.search(pattern, code, re.IGNORECASE):
                changes.append(OrthogonalChange(
                    type=change_type,
                    description=description,
                    affected_files=[],
                    severity="high",
                    suggestion="Review file operations to ensure they don't affect unrelated files"
                ))

        return changes

    def _detect_dependency_changes(self, code: str) -> List[OrthogonalChange]:
        """Detect dependency changes."""
        changes = []

        # Look for import additions/removals
        import_pattern = r'(?:^|\n)\s*(?:import|from)\s+(\w+)'
        imports = re.findall(import_pattern, code, re.MULTILINE)

        if imports:
            changes.append(OrthogonalChange(
                type="dependency_change",
                description=f"New dependencies detected: {', '.join(imports)}",
                affected_files=[],
                severity="medium",
                suggestion="Review dependency changes and update requirements.txt if needed"
            ))

        return changes

    def _detect_config_changes(self, code: str) -> List[OrthogonalChange]:
        """Detect configuration changes."""
        changes = []

        # Look for configuration modifications
        config_patterns = [
            (r'\.env\s*=', "config_change", "Environment variable modification"),
            (r'config\[', "config_change", "Configuration dictionary modification"),
            (r'settings\.', "config_change", "Settings modification"),
        ]

        for pattern, change_type, description in config_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                changes.append(OrthogonalChange(
                    type=change_type,
                    description=description,
                    affected_files=[],
                    severity="medium",
                    suggestion="Review configuration changes to ensure they don't affect other components"
                ))

        return changes

    def _detect_side_effects(self, code: str) -> List[OrthogonalChange]:
        """Detect side effects."""
        changes = []

        # Look for global variable modifications
        if re.search(r'global\s+\w+', code):
            changes.append(OrthogonalChange(
                type="side_effect",
                description="Global variable modification detected",
                affected_files=[],
                severity="high",
                suggestion="Review global variable usage - consider using function parameters instead"
            ))

        # Look for system calls
        if re.search(r'(?:os\.system|subprocess\.)', code):
            changes.append(OrthogonalChange(
                type="side_effect",
                description="System call detected",
                affected_files=[],
                severity="critical",
                suggestion="Review system calls - ensure they don't have unintended side effects"
            ))

        return changes


__all__ = [
    'OrthogonalChangeGuard',
    'OrthogonalChange',
]

