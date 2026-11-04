#!/usr/bin/env python3
"""Rebuild the sealed PR #108 review manifest from its candidate commit."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = "275b871349721a8c917691d457c4a6270fe1028f"
SEALED_CANDIDATE = "7010b6d699f82a8719ed1d7269f5bfdb07089238"
OUTPUT = ROOT / "docs/PREPUBLICATION_FILE_MANIFEST.json"


def git_bytes(path: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{SEALED_CANDIDATE}:{path}"], cwd=ROOT
    )


def main() -> None:
    changed = set(
        subprocess.check_output(
            ["git", "diff", "--name-only", BASE, SEALED_CANDIDATE, "--"],
            cwd=ROOT,
            text=True,
        ).splitlines()
    )
    rows = []
    for name in sorted(changed):
        if name == OUTPUT.relative_to(ROOT).as_posix():
            continue
        data = git_bytes(name)
        rows.append(
            {
                "path": name,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    record = {
        "schema": "phionyx-prepublication-file-manifest-v2",
        "generated": "2026-11-03",
        "historical_lab_base": BASE,
        "lifecycle_state": "PUBLIC_PR_READY_FOR_REVIEW",
        "publication_performed": True,
        "publication_scope": "PUBLIC_BRANCH_AND_PR_ONLY",
        "approval_granted": True,
        "approval_scope": "PUBLIC_PUSH_PR_AND_PREMERGE_PREPARATION",
        "merge_approval_granted": False,
        "pull_request": {
            "number": 108,
            "url": "https://github.com/halvrenofviryel/phionyx-research/pull/108",
            "branch": "codex/prepublication-k1-k5",
            "initial_public_head": "a10a2fc83cf2d9a075d7ff26d67b50205c0bb174",
        },
        "files": rows,
    }
    OUTPUT.write_text(json.dumps(record, indent=2, sort_keys=False) + "\n")
    print(f"WROTE {OUTPUT.relative_to(ROOT)}: {len(rows)} files")


if __name__ == "__main__":
    main()
