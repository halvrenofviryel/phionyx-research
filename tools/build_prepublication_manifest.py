#!/usr/bin/env python3
"""Build the exact file manifest used by the next-publication review."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = "275b871349721a8c917691d457c4a6270fe1028f"
OUTPUT = ROOT / "docs/PREPUBLICATION_FILE_MANIFEST.json"


def main() -> None:
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", BASE, "HEAD"], cwd=ROOT, text=True
    ).splitlines()
    rows = []
    for name in sorted(changed):
        if name == OUTPUT.relative_to(ROOT).as_posix():
            continue
        path = ROOT / name
        if not path.is_file():
            raise SystemExit(f"manifest supports files only: {name}")
        data = path.read_bytes()
        rows.append(
            {
                "path": name,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    record = {
        "schema": "phionyx-prepublication-file-manifest-v1",
        "generated": "2026-11-03",
        "historical_lab_base": BASE,
        "publication_performed": False,
        "approval_granted": False,
        "files": rows,
    }
    OUTPUT.write_text(json.dumps(record, indent=2, sort_keys=False) + "\n")
    print(f"WROTE {OUTPUT.relative_to(ROOT)}: {len(rows)} files")


if __name__ == "__main__":
    main()
