#!/usr/bin/env python3
"""Verify the bounded 2026-11-03 local publication candidate."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = "652e008d18805a1c69492a688e621df91f143287"
K5_TESTED = "bec6b34c55d5a1f3e898997475539c9d54c91580"
K5_FINAL = "92c17a237bcc73c3ac69dbb879e1f358c705a739"
K1_FINAL = "a7afc505ece2948966b510aefe595f13403c0232"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> None:
    required = [
        "docs/CONTROL_EVIDENCE_RESEARCH.md",
        "docs/EXTERNAL_IMPACT_LEDGER.md",
        "docs/external_impact_ledger.json",
        "docs/PREPUBLICATION_REVIEW_2026-11-03.md",
        "docs/PUBLICATION_PR_DRAFT_2026-11-03.md",
        "docs/external-replication/START_HERE.md",
        "experiments/ietf/acder02-control-benchmark/README.md",
        "experiments/ietf/acder02-control-benchmark/RESULTS.md",
    ]
    missing = [path for path in required if not (ROOT / path).is_file()]
    assert not missing, f"missing required files: {missing}"

    assert subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE, "HEAD"], cwd=ROOT
    ).returncode == 0
    for source in (K5_TESTED, K5_FINAL):
        assert subprocess.run(
            ["git", "merge-base", "--is-ancestor", source, "HEAD"], cwd=ROOT
        ).returncode == 0, f"source commit not retained: {source}"

    packet_diff = git(
        "diff", "--name-only", K5_TESTED, K5_FINAL, "--", "docs/external-replication"
    ).splitlines()
    assert packet_diff == [], f"tested packet changed: {packet_diff}"
    current_packet_diff = git(
        "diff", "--name-only", K5_FINAL, "HEAD", "--",
        "docs/external-replication", "reports/external-replication"
    ).splitlines()
    assert current_packet_diff == [], f"frozen K5 packet/report changed: {current_packet_diff}"

    k1_diff = git(
        "diff", "--name-only", K1_FINAL, "HEAD", "--",
        "experiments/ietf/acder02-control-benchmark"
    ).splitlines()
    assert k1_diff == ["experiments/ietf/acder02-control-benchmark/README.md"], (
        f"unexpected change to frozen K1 subtree: {k1_diff}"
    )

    ledger = json.loads((ROOT / "docs/external_impact_ledger.json").read_text())
    assert ledger["publication_status"] == "PREPUBLICATION_LOCAL_CANDIDATE"
    assert ledger["aggregate"]["same_version_external_interoperability"] == "NOT_ESTABLISHED"
    assert ledger["aggregate"]["external_reproduction_of_k1_k2_k3"] == "NOT_EVALUATED"
    assert all(not entry["adoption"] for entry in ledger["entries"])

    review = (ROOT / "docs/PREPUBLICATION_REVIEW_2026-11-03.md").read_text()
    assert "READY_FOR_OWNER_REVIEW / UNPUBLISHED" in review
    assert "require explicit owner approval" in review

    landing = (ROOT / "docs/CONTROL_EVIDENCE_RESEARCH.md").read_text()
    for phrase in (
        "do not establish independent validation",
        "same-version external interoperability",
    ):
        assert phrase in landing, f"landing page lost boundary: {phrase}"

    authored_surfaces = [
        "README.md",
        "docs/CONTROL_EVIDENCE_RESEARCH.md",
        "docs/EXTERNAL_IMPACT_LEDGER.md",
        "docs/PREPUBLICATION_REVIEW_2026-11-03.md",
        "docs/PUBLICATION_PR_DRAFT_2026-11-03.md",
        "docs/PUBLICATION_STATUS.md",
        "docs/STANDARDS_LAB.md",
        "docs/external_impact_ledger.json",
        "experiments/ietf/acder02-control-benchmark/README.md",
        "tools/build_prepublication_manifest.py",
        "tools/verify_prepublication_candidate.py",
    ]
    subprocess.run(
        ["git", "diff", "--check", K5_FINAL, "HEAD", "--", *authored_surfaces],
        cwd=ROOT,
        check=True,
    )

    tracked = set(git("ls-files").splitlines())
    for path in required:
        assert path in tracked, f"required file is not tracked: {path}"

    print(
        "PREPUBLICATION_CANDIDATE_OK: required files, source ancestry, "
        "packet identity, approval boundary and external-impact states verified"
    )


if __name__ == "__main__":
    main()
