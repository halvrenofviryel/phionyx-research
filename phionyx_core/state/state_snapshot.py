"""
State Snapshot - Serialize/Deserialize EchoState2
===================================================

Serialization and deserialization utilities for EchoState2 and AuxState.
"""

from __future__ import annotations

import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from phionyx_core.state.echo_state_2 import EchoState2
from phionyx_core.state.aux_state import AuxState


class StateSnapshot:
    """
    State snapshot utilities for serialization/deserialization.

    Provides:
    - JSON serialization/deserialization
    - File I/O
    - Version management
    """

    VERSION = "2.0"  # EchoState2 version

    @staticmethod
    def serialize(
        echo_state2: EchoState2,
        aux_state: Optional[AuxState] = None,
        include_derived: bool = True
    ) -> Dict[str, Any]:
        """
        Serialize EchoState2 (+ AuxState) to dictionary.

        Args:
            echo_state2: EchoState2 instance
            aux_state: Optional AuxState instance
            include_derived: Include derived metrics (phi, stability, resonance)

        Returns:
            Dictionary representation
        """
        snapshot = {
            "version": StateSnapshot.VERSION,
            "echo_state2": echo_state2.to_dict(),
            "timestamp": datetime.now().isoformat()
        }

        # Add derived metrics if requested
        if include_derived:
            snapshot["derived_metrics"] = {
                "phi": echo_state2.phi,
                "stability": echo_state2.stability,
                "resonance": echo_state2.resonance
            }

        # Add aux state if provided
        if aux_state:
            snapshot["aux_state"] = aux_state.to_dict()

        return snapshot

    @staticmethod
    def deserialize(data: Dict[str, Any]) -> tuple[EchoState2, Optional[AuxState]]:
        """
        Deserialize dictionary to EchoState2 (+ AuxState).

        Args:
            data: Dictionary representation

        Returns:
            Tuple of (EchoState2, Optional[AuxState])
        """
        version = data.get("version", "1.0")

        if version != StateSnapshot.VERSION:
            raise ValueError(f"Unsupported version: {version}. Expected: {StateSnapshot.VERSION}")

        # Deserialize EchoState2
        echo_state2 = EchoState2.from_dict(data["echo_state2"])

        # Deserialize AuxState if present
        aux_state = None
        if "aux_state" in data:
            aux_state = AuxState.from_dict(data["aux_state"])

        return echo_state2, aux_state

    @staticmethod
    def to_json(
        echo_state2: EchoState2,
        aux_state: Optional[AuxState] = None,
        include_derived: bool = True,
        indent: Optional[int] = 2
    ) -> str:
        """
        Serialize to JSON string.

        Args:
            echo_state2: EchoState2 instance
            aux_state: Optional AuxState instance
            include_derived: Include derived metrics
            indent: JSON indentation (None for compact)

        Returns:
            JSON string
        """
        snapshot = StateSnapshot.serialize(echo_state2, aux_state, include_derived)
        return json.dumps(snapshot, indent=indent, ensure_ascii=False)

    @staticmethod
    def from_json(json_str: str) -> tuple[EchoState2, Optional[AuxState]]:
        """
        Deserialize from JSON string.

        Args:
            json_str: JSON string

        Returns:
            Tuple of (EchoState2, Optional[AuxState])
        """
        data = json.loads(json_str)
        return StateSnapshot.deserialize(data)

    @staticmethod
    def save_to_file(
        file_path: str | Path,
        echo_state2: EchoState2,
        aux_state: Optional[AuxState] = None,
        include_derived: bool = True
    ) -> None:
        """
        Save state to file.

        Args:
            file_path: File path
            echo_state2: EchoState2 instance
            aux_state: Optional AuxState instance
            include_derived: Include derived metrics
        """
        file_path = Path(file_path)
        json_str = StateSnapshot.to_json(echo_state2, aux_state, include_derived)
        file_path.write_text(json_str, encoding='utf-8')

    @staticmethod
    def load_from_file(file_path: str | Path) -> tuple[EchoState2, Optional[AuxState]]:
        """
        Load state from file.

        Args:
            file_path: File path

        Returns:
            Tuple of (EchoState2, Optional[AuxState])
        """
        file_path = Path(file_path)
        json_str = file_path.read_text(encoding='utf-8')
        return StateSnapshot.from_json(json_str)

    @staticmethod
    def create_snapshot(
        echo_state2: EchoState2,
        aux_state: Optional[AuxState] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a complete snapshot with metadata.

        Args:
            echo_state2: EchoState2 instance
            aux_state: Optional AuxState instance
            metadata: Optional additional metadata

        Returns:
            Complete snapshot dictionary
        """
        snapshot = StateSnapshot.serialize(echo_state2, aux_state, include_derived=True)

        # Add metadata
        if metadata:
            snapshot["metadata"] = metadata

        return snapshot

