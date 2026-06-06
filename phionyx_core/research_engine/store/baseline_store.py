"""Baseline store — manages current best metrics snapshot."""
import json
from pathlib import Path
from typing import Any


class BaselineStore:
    """Stores the current baseline metrics.

    The baseline is overwritten whenever a candidate is kept.
    This file represents the current "best known" state.
    """

    def __init__(self, data_dir: str = "data/research_engine"):
        self._dir = Path(data_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._file = self._dir / "baseline.json"

    def save(self, snapshot: dict) -> None:
        """Save baseline snapshot (overwrites previous)."""
        with open(self._file, "w") as f:
            json.dump(snapshot, f, indent=2, default=str)

    def load(self) -> dict | None:
        """Load current baseline. Returns None if no baseline exists."""
        if not self._file.exists():
            return None
        with open(self._file) as f:
            return json.load(f)

    def exists(self) -> bool:
        """Check if a baseline exists."""
        return self._file.exists()

    def get_cqs(self) -> float | None:
        """Get current baseline CQS."""
        baseline = self.load()
        if baseline is None:
            return None
        metrics = baseline.get("metrics", {})
        return metrics.get("cqs")

    def get_surface_value(self, param_name: str) -> Any | None:
        """Get a specific parameter value from the baseline."""
        baseline = self.load()
        if baseline is None:
            return None
        return baseline.get("surface_values", {}).get(param_name)
