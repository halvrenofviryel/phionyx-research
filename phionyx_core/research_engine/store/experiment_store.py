"""Experiment store — append-only JSONL storage for experiment records."""
import json
from pathlib import Path
from typing import List


class ExperimentStore:
    """Append-only JSONL store for experiment records.

    Each line is a complete JSON object representing one experiment.
    This file is never committed to git (it's the full history including
    failures, like Karpathy's results.tsv).
    """

    def __init__(self, data_dir: str = "data/research_engine"):
        self._dir = Path(data_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._file = self._dir / "experiments.jsonl"

    def append(self, record: dict) -> None:
        """Append an experiment record."""
        with open(self._file, "a") as f:
            f.write(json.dumps(record, default=str) + "\n")

    def get_all(self) -> List[dict]:
        """Get all experiment records."""
        if not self._file.exists():
            return []
        records = []
        with open(self._file) as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

    def get_by_session(self, session_id: str) -> List[dict]:
        """Get experiments for a specific session."""
        return [r for r in self.get_all() if r.get("session_id") == session_id]

    def get_by_surface(self, surface_file: str) -> List[dict]:
        """Get experiments for a specific surface."""
        return [r for r in self.get_all() if r.get("surface_file") == surface_file]

    def get_by_status(self, status: str) -> List[dict]:
        """Get experiments with a specific status."""
        return [r for r in self.get_all() if r.get("status") == status]

    def get_tried_values(self, surface_file: str, param_name: str) -> set:
        """Get all values that have been tried for a parameter."""
        values = set()
        for record in self.get_by_surface(surface_file):
            h = record.get("hypothesis", {})
            if h.get("parameter_name") == param_name:
                values.add(h.get("new_value"))
        return values

    def count(self) -> int:
        """Count total experiments."""
        if not self._file.exists():
            return 0
        with open(self._file) as f:
            return sum(1 for line in f if line.strip())
