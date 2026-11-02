"""Deterministically run supplied vectors; expected outcomes are not evaluator inputs."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from appraise import OUTCOMES, appraise

ROOT = Path(__file__).resolve().parents[1]


def run() -> dict:
    """Produce results without consulting scenario-only ground truth or expectations."""
    fixtures = json.loads((ROOT / "vectors/completeness_vectors.json").read_text())
    results = [
        {"id": v["id"], **appraise(v["input"], fixtures["replay_at"])} for v in fixtures["vectors"]
    ]
    counts = Counter(r["result"] for r in results)
    return {
        "profile": fixtures["profile"],
        "replay_at": fixtures["replay_at"],
        "vector_count": len(results),
        "outcome_counts": {name: counts[name] for name in OUTCOMES},
        "results": results,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
