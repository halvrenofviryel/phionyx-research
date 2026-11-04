#!/usr/bin/env python3
"""Verify the published control-evidence packet and its historical seals."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = "652e008d18805a1c69492a688e621df91f143287"
K5_TESTED = "bec6b34c55d5a1f3e898997475539c9d54c91580"
K5_FINAL = "92c17a237bcc73c3ac69dbb879e1f358c705a739"
SEALED_CANDIDATE = "7010b6d699f82a8719ed1d7269f5bfdb07089238"
PUBLICATION_MERGE = "54682cfd312dc8c7935e926539811cfc29ea6568"
RELEASE_MERGE = "a5956f6d575c431745f902a242b1a25262fed89d"
VERSION_DOI = "10.5281/zenodo.23960852"
CONCEPT_DOI = "10.5281/zenodo.23960851"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def git_bytes(revision: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)


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
        "studies/control-evidence-2026-11/README.md",
        "studies/control-evidence-2026-11/CITATION.cff",
        "studies/control-evidence-2026-11/CITATION.bib",
        "studies/control-evidence-2026-11/codemeta.json",
        "studies/control-evidence-2026-11/zenodo.json",
        "studies/control-evidence-2026-11/RELEASE_NOTES.md",
        "studies/control-evidence-2026-11/build_release.py",
        "studies/control-evidence-2026-11/verify_release.py",
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
    for source in (SEALED_CANDIDATE, PUBLICATION_MERGE, RELEASE_MERGE):
        assert subprocess.run(
            ["git", "merge-base", "--is-ancestor", source, "HEAD"], cwd=ROOT
        ).returncode == 0, f"publication commit not retained: {source}"

    packet_diff = git(
        "diff", "--name-only", K5_TESTED, K5_FINAL, "--", "docs/external-replication"
    ).splitlines()
    assert packet_diff == [], f"tested packet changed: {packet_diff}"
    current_packet_diff = git(
        "diff", "--name-only", K5_FINAL, "HEAD", "--",
        "docs/external-replication", "reports/external-replication"
    ).splitlines()
    assert current_packet_diff == [], f"frozen K5 packet/report changed: {current_packet_diff}"

    k1_root = ROOT / "experiments/ietf/acder02-control-benchmark"
    k1_manifest = json.loads((k1_root / "PACKAGE_MANIFEST.json").read_text())
    assert k1_manifest["schema"] == "acder-benchmark-final-package-v1"
    assert k1_manifest["file_count"] == len(k1_manifest["files"]) == 169
    for row in k1_manifest["files"]:
        data = (k1_root / row["path"]).read_bytes()
        assert row["bytes"] == len(data), f"K1 package byte count differs: {row['path']}"
        assert row["sha256"] == hashlib.sha256(data).hexdigest(), (
            f"K1 package hash differs: {row['path']}"
        )
    k1_pins = json.loads((k1_root / "SOURCE_PINS.json").read_text())
    assert k1_pins["base_commit"] == BASE
    assert (
        k1_root / "results/EXPECTED_SEMANTIC_SHA256"
    ).read_text().strip() == "f73be47c6b2e61411b4c18466e0bb7ed85fce06aa415dc7ef23b3b86a397aacb"

    ledger = json.loads((ROOT / "docs/external_impact_ledger.json").read_text())
    assert ledger["schema"] == "phionyx-external-impact-ledger-v3"
    assert ledger["publication_status"] == (
        "RELEASE_ZENODO_HUGGING_FACE_SUBSTACK_AND_PHIONYX_AI_PUBLISHED"
    )
    assert ledger["publication_event"] == {
        "repository": "halvrenofviryel/phionyx-research",
        "branch": "codex/prepublication-k1-k5",
        "initial_public_head": "a10a2fc83cf2d9a075d7ff26d67b50205c0bb174",
        "pull_request": 108,
        "url": "https://github.com/halvrenofviryel/phionyx-research/pull/108",
        "merge_performed": True,
        "merge_commit": PUBLICATION_MERGE,
        "merged_at": "2026-11-03T19:47:05Z",
        "release_performed": True,
        "release_tag": "control-evidence-study-v1.0.0",
        "release_commit": RELEASE_MERGE,
        "release_url": (
            "https://github.com/halvrenofviryel/phionyx-research/releases/tag/"
            "control-evidence-study-v1.0.0"
        ),
        "zenodo_record": "https://zenodo.org/records/23960852",
        "version_doi": VERSION_DOI,
        "concept_doi": CONCEPT_DOI,
        "outreach_performed": True,
        "hugging_face_article": {
            "published_at": "2026-11-04T19:28:58Z",
            "url": (
                "https://huggingface.co/blog/phionyx/"
                "when-an-ai-agent-says-stop-what-evidence-proves-th"
            ),
            "classification": "AUTHOR_SIDE_TECHNICAL_COMMUNICATION",
        },
        "substack_update": {
            "published_at": "2026-11-04T19:58:27Z",
            "url": (
                "https://phionyxresearch.substack.com/p/"
                "what-did-the-ai-decide-and-what-does"
            ),
            "classification": "DATED_AUTHOR_SIDE_CORRECTION",
        },
        "phionyx_ai_update": {
            "deployed_at": "2026-11-04T20:20:05Z",
            "research_url": "https://phionyx.ai/research",
            "publications_url": "https://phionyx.ai/publications",
            "pull_request": "https://github.com/halvrenofviryel/Viryel/pull/46",
            "merge_commit": "0e0c020706c59b2935e0e235169b6cfbc89174e6",
            "deployment_run": (
                "https://github.com/halvrenofviryel/Viryel/actions/runs/"
                "41905427702"
            ),
            "classification": "AUTHOR_SIDE_RESEARCH_DISCOVERY_PAGE",
        },
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
    assert "Public PR #108 — merged" in status
    assert "Public release and Zenodo deposit — completed" in status
    assert "a10a2fc83cf2d9a075d7ff26d67b50205c0bb174" in status
    assert PUBLICATION_MERGE in status
    assert RELEASE_MERGE in status
    assert VERSION_DOI in status

    landing = (ROOT / "docs/CONTROL_EVIDENCE_RESEARCH.md").read_text()
    for phrase in (
        "do not establish independent validation",
        "same-version external interoperability",
    ):
        assert phrase in landing, f"landing page lost boundary: {phrase}"
    assert VERSION_DOI in landing
    assert "Hugging Face Community Article" in landing
    assert "IETF\nsubmission remains a separate user-performed action" in landing

    manifest_path = ROOT / "docs/PREPUBLICATION_FILE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["schema"] == "phionyx-prepublication-file-manifest-v2"
    assert manifest["lifecycle_state"] == "PUBLIC_PR_READY_FOR_REVIEW"
    assert manifest["publication_scope"] == "PUBLIC_BRANCH_AND_PR_ONLY"
    assert manifest["approval_scope"] == "PUBLIC_PUSH_PR_AND_PREMERGE_PREPARATION"
    assert manifest["merge_approval_granted"] is False
    assert manifest["pull_request"]["number"] == 108

    manifest_name = manifest_path.relative_to(ROOT).as_posix()
    changed = set(
        git(
            "diff", "--name-only", manifest["historical_lab_base"],
            SEALED_CANDIDATE, "--"
        ).splitlines()
    )
    changed.discard(manifest_name)
    rows = {row["path"]: row for row in manifest["files"]}
    assert set(rows) == changed, "manifest paths differ from the exact candidate diff"
    for name, row in rows.items():
        data = git_bytes(SEALED_CANDIDATE, name)
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
        "studies/control-evidence-2026-11/README.md",
        "studies/control-evidence-2026-11/CITATION.cff",
        "studies/control-evidence-2026-11/CITATION.bib",
        "studies/control-evidence-2026-11/codemeta.json",
        "studies/control-evidence-2026-11/zenodo.json",
        "studies/control-evidence-2026-11/RELEASE_NOTES.md",
        "studies/control-evidence-2026-11/build_release.py",
        "studies/control-evidence-2026-11/verify_release.py",
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
        "PUBLISHED_CONTROL_EVIDENCE_PACKET_OK: required files, source ancestry, "
        "sealed PR manifest, frozen packet identity and current impact states verified"
    )


if __name__ == "__main__":
    main()
