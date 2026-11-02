"""Verify the prior -03 experiment without creating or changing files there."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
OLD = ROOT.with_name("decision-receipts-03")


def check(*, all_local: bool = False) -> int:
    """Check tracked files everywhere; include ignored environment/cache on request."""
    name = "frozen-03-all-files.json" if all_local else "frozen-03-tracked.json"
    recorded = json.loads((ROOT / "evidence" / name).read_text())
    base = OLD if all_local else REPO
    for relative, expected in recorded.items():
        file = base / relative
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"frozen -03 file missing or changed: {relative}")
    if all_local:
        actual = {str(f.relative_to(OLD)) for f in OLD.rglob("*") if f.is_file()}
        if actual != set(recorded):
            raise RuntimeError(f"frozen -03 file inventory changed: {actual ^ set(recorded)}")
    return len(recorded)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all-local", action="store_true")
    count = check(all_local=parser.parse_args().all_local)
    print(f"PASS: {count} frozen -03 files byte-identical")
