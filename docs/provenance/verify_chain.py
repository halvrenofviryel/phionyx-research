#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independently verify the continuity of the published authoring gate transcript.

This script re-checks the append-only hash chain in
``architecture_md_authoring_chain.jsonl`` — the redacted, signed gate transcript
produced while ``ARCHITECTURE.md`` was authored *through* the Phionyx runtime.

What this proves
----------------
* The transcript is an **append-only chain**: each record's ``previous_hash``
  equals the prior record's ``current_hash``. A single altered or reordered
  record breaks the chain and this script exits non-zero.
* The chain **head** matches the value cited in ``README.md`` / the architecture
  doc's provenance colophon.

What this does NOT prove (stated plainly — see README.md §"Honest split")
-------------------------------------------------------------------------
* **Authenticity.** The signatures here are the MCP boundary's *demo* HMAC
  (``demo-hmac:...``), not the core Ed25519 signer; the signing key and the full
  decision envelopes live in the private development monorepo. This script checks
  *continuity*, not signature authenticity.
* **That the chain commits to ARCHITECTURE.md's specific bytes.** The underlying
  per-turn envelopes (which bind the gate's inputs/outputs) are internal. The
  externally reproducible surface is the public package + CI + AIREP conformance
  (README.md §"What is publicly verifiable today").

Usage
-----
    python3 verify_chain.py [path/to/architecture_md_authoring_chain.jsonl]

Exit code 0 = continuous chain, head matches. 1 = broken/mismatch.
No third-party dependencies (Python 3.8+ stdlib only).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

EXPECTED_HEAD = "sha256:2997f4d64eb19786523c07847b6975a8cb4407467f40e4cb3c77c495fca9c629"


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else Path(__file__).with_name(
        "architecture_md_authoring_chain.jsonl"
    )
    if not path.exists():
        print(f"FAIL: transcript not found: {path}", file=sys.stderr)
        return 1

    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if not records:
        print("FAIL: empty transcript", file=sys.stderr)
        return 1

    ok = True
    for i in range(1, len(records)):
        prev_current = records[i - 1]["current_hash"]
        this_previous = records[i]["previous_hash"]
        if this_previous != prev_current:
            ok = False
            print(
                f"FAIL: continuity break at turn {records[i].get('turn_index')}: "
                f"previous_hash != prior current_hash",
                file=sys.stderr,
            )

    head = records[-1]["current_hash"]
    head_ok = head == EXPECTED_HEAD

    print(f"records         : {len(records)}")
    print(f"continuity      : {'OK (append-only chain intact)' if ok else 'BROKEN'}")
    print(f"head            : {head}")
    print(f"head matches doc: {'OK' if head_ok else f'MISMATCH (expected {EXPECTED_HEAD})'}")
    print(
        "note            : this verifies CONTINUITY only — not signature authenticity "
        "(demo-hmac) nor the internal envelopes. See README.md."
    )
    return 0 if (ok and head_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
