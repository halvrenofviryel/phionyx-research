#!/usr/bin/env python3
"""Verify the bounded public draft-PR candidate and its frozen evidence."""

from __future__ import annotations

import hashlib
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
        "docs/PUBLICATION_STATUS.md",
        "docs/PREPUBLICATION_FILE_MANIFEST.json",
        "docs/external-replication/START_HERE.md",
        "experiments/ietf/acder02-control-benchmark/README.md",
        "experiments/ietf/acder02-control-benchmark/RESULTS.md",
        ".gitattributes",
        ".github/workflows/research-artifacts.yml",
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
    assert ledger["schema"] == "phionyx-external-impact-ledger-v3"
    assert ledger["publication_status"] == "PUBLIC_DRAFT_PR_OPEN"
    assert ledger["publication_event"] == {
        "repository": "halvrenofviryel/phionyx-research",
        "branch": "codex/prepublication-k1-k5",
        "initial_public_head": "a10a2fc83cf2d9a075d7ff26d67b50205c0bb174",
        "pull_request": 108,
        "url": "https://github.com/halvrenofviryel/phionyx-research/pull/108",
        "merge_performed": False,
        "release_performed": False,
        "outreach_performed": False,
        "standards_submission_performed": False,
    }
    assert ledger["k6_status"] == "INITIAL_LEDGER_COMPLETE_MONITORING_OPEN"
    assert ledger["aggregate"]["same_version_external_interoperability"] == "NOT_ESTABLISHED"
    assert ledger["aggregate"]["external_reproduction_of_k1_k2_k3"] == "NOT_EVALUATED"
    assert all(not entry["adoption"] for entry in ledger["entries"])
    assert ledger["reassessment"] == {
        "T1_reproducible_original_result": "MET_LOCAL",
        "T2_same_version_external_interoperability": "NOT_MET",
        "T3_real_runtime_evidence": "MET_BOUNDED_LOCAL",
        "T4_substantive_external_uptake": "NOT_MET_FOR_CURRENT_PACKET",
        "global_top10_reassessment": "HOLD_NO_SUPPORTED_RANKING_CLAIM",
    }

    review = (ROOT / "docs/PREPUBLICATION_REVIEW_2026-11-03.md").read_text()
    review_words = " ".join(review.split())
    assert "HISTORICAL PREPUBLICATION SNAPSHOT" in review
    assert "PR #108" in review
    assert "did not authorize merge" in review_words

    status = (ROOT / "docs/PUBLICATION_STATUS.md").read_text()
    assert "Public draft PR #108" in status
    assert "a10a2fc83cf2d9a075d7ff26d67b50205c0bb174" in status
    assert "do not authorize" in status

    landing = (ROOT / "docs/CONTROL_EVIDENCE_RESEARCH.md").read_text()
    for phrase in (
        "do not establish independent validation",
        "same-version external interoperability",
    ):
        assert phrase in landing, f"landing page lost boundary: {phrase}"
    assert "Merge, release, outreach and standards submission" in landing

    manifest_path = ROOT / "docs/PREPUBLICATION_FILE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["schema"] == "phionyx-prepublication-file-manifest-v2"
    assert manifest["lifecycle_state"] == "PUBLIC_DRAFT_PR_OPEN"
    assert manifest["publication_scope"] == "PUBLIC_BRANCH_AND_DRAFT_PR_ONLY"
    assert manifest["approval_scope"] == "PUBLIC_PUSH_AND_DRAFT_PR_ONLY"
    assert manifest["merge_approval_granted"] is False
    assert manifest["pull_request"]["number"] == 108

    manifest_name = manifest_path.relative_to(ROOT).as_posix()
    changed = set(git("diff", "--name-only", manifest["historical_lab_base"], "--").splitlines())
    changed.update(git("ls-files", "--others", "--exclude-standard").splitlines())
    changed.discard(manifest_name)
    rows = {row["path"]: row for row in manifest["files"]}
    assert set(rows) == changed, "manifest paths differ from the exact candidate diff"
    for name, row in rows.items():
        data = (ROOT / name).read_bytes()
        assert row["bytes"] == len(data), f"manifest byte count differs: {name}"
        assert row["sha256"] == hashlib.sha256(data).hexdigest(), (
            f"manifest hash differs: {name}"
        )

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
        ".gitattributes",
        ".github/workflows/research-artifacts.yml",
    ]
    subprocess.run(
        ["git", "diff", "--check", K5_FINAL, "--", *authored_surfaces],
        cwd=ROOT,
        check=True,
    )

    tracked = set(git("ls-files").splitlines())
    for path in required:
        assert path in tracked, f"required file is not tracked: {path}"

    print(
        "PUBLIC_DRAFT_PR_CANDIDATE_OK: required files, source ancestry, exact "
        "manifest, packet identity, approval scope and impact states verified"
    )


if __name__ == "__main__":
    main()
