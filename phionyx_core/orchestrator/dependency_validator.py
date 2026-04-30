"""
Block Dependency Validator
==========================

Validates block execution order against dependency graph.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DependencyValidator:
    """
    Validates block execution order against dependency graph.
    """

    def __init__(self, dependencies_file: Path | None = None):
        """
        Initialize validator.

        Args:
            dependencies_file: Path to block_dependencies.json (default: auto-detect)
        """
        if dependencies_file is None:
            # Auto-detect dependencies file
            current_dir = Path(__file__).parent
            dependencies_file = current_dir / 'block_dependencies.json'

        self.dependencies_file = dependencies_file
        self.dependencies: dict[str, dict] = {}
        self.metadata_producers: dict[str, list[str]] = {}

        self._load_dependencies()

    def _load_dependencies(self) -> None:
        """Load dependency graph from JSON file."""
        try:
            with open(self.dependencies_file, encoding='utf-8') as f:
                data = json.load(f)
                self.dependencies = data.get('dependencies', {})
                self.metadata_producers = data.get('metadata_producers', {})
            logger.debug(f"Loaded dependency graph: {len(self.dependencies)} blocks")
        except FileNotFoundError:
            logger.warning(f"Dependency file not found: {self.dependencies_file}. Validation disabled.")
            self.dependencies = {}
            self.metadata_producers = {}
        except Exception as e:
            logger.error(f"Failed to load dependency graph: {e}")
            self.dependencies = {}
            self.metadata_producers = {}

    def validate_execution_order(self, block_order: list[str]) -> tuple[bool, list[str]]:
        """
        Validate block execution order against dependency graph.

        Args:
            block_order: List of block IDs in execution order

        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        if not self.dependencies:
            # No dependency graph loaded, skip validation
            return True, []

        violations = []
        executed_blocks: set[str] = set()

        for block_id in block_order:
            if block_id not in self.dependencies:
                # Block not in dependency graph, skip
                continue

            block_deps = self.dependencies[block_id].get('dependencies', [])

            # Check if all dependencies have been executed
            missing_deps = [dep for dep in block_deps if dep not in executed_blocks]

            if missing_deps:
                violations.append(
                    f"Block '{block_id}' requires dependencies that haven't been executed: {missing_deps}"
                )

            executed_blocks.add(block_id)

        return len(violations) == 0, violations

    def get_block_dependencies(self, block_id: str) -> list[str]:
        """
        Get list of block IDs that must execute before this block.

        Args:
            block_id: Block ID

        Returns:
            List of dependency block IDs
        """
        if block_id not in self.dependencies:
            return []

        return self.dependencies[block_id].get('dependencies', [])

    def get_metadata_producers(self, metadata_key: str) -> list[str]:
        """
        Get list of block IDs that produce a specific metadata key.

        Args:
            metadata_key: Metadata key name

        Returns:
            List of producer block IDs
        """
        return self.metadata_producers.get(metadata_key, [])

    def get_block_writes(self, block_id: str) -> set[str]:
        """
        Get set of metadata keys that this block writes to.

        Args:
            block_id: Block ID

        Returns:
            Set of metadata keys that block writes
        """
        if block_id not in self.dependencies:
            return set()

        writes = self.dependencies[block_id].get('writes', [])
        return set(writes) if writes else set()

    def get_block_reads(self, block_id: str) -> set[str]:
        """
        Get set of metadata keys that this block reads from.

        Args:
            block_id: Block ID

        Returns:
            Set of metadata keys that block reads
        """
        if block_id not in self.dependencies:
            return set()

        reads = self.dependencies[block_id].get('reads', [])
        return set(reads) if reads else set()

