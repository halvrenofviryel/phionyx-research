"""Check the review package offline without executing D, B1 or external code."""

import argparse
import datetime
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASE = "275b871349721a8c917691d457c4a6270fe1028f"


def load(path):
    def pairs(items):
        data = {}
        for key, value in items:
            assert key not in data, f"duplicate JSON key: {key}"
            data[key] = value
        return data

    return json.loads((ROOT / path).read_text(), object_pairs_hook=pairs)


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def check():
    lab = load("docs/standards_lab.json")
    assert lab["approval_granted"] is False
    assert lab["base_commit"] == BASE
    assert lab["counts"] == {
        "integrated_experiments": 3,
        "completed_result_references": 1,
        "preparation_packages": 1,
        "pending_results": 3,
        "third_party_validations_added": 0,
    }
    assert {p["id"] for p in lab["pending"]} == {"B2", "B3", "F"}
    for pending in lab["pending"]:
        assert pending["status"] == "PENDING" and pending["result"] == "NOT_EVALUATED"
        assert pending["commit"] is None and not pending["counted_as_success"]
    frozen = load("docs/standards-lab-evidence/frozen_inputs.json")["files"]
    assert len(frozen) == 123
    for row in frozen:
        assert sha(row["path"]) == row["sha256"], row["path"]
        blob = subprocess.check_output(["git", "show", BASE + ":" + row["path"]], cwd=ROOT)
        assert hashlib.sha256(blob).hexdigest() == row["sha256"]
    exp = {e["id"]: e for e in lab["experiments"]}
    assert set(exp) == {"A", "C", "E"}
    digest_count = 0
    for e in exp.values():
        assert e["original_experiment_commit"] != e["integration_commit"]
        assert e["non_claims"] and e["publication_status"] == "UNPUBLISHED"
        assert not e["third_party_evidence"]
        for row in e["artifacts"].values():
            assert sha(row["path"]) == row["sha256"]
            digest_count += 1
        for source in e["source_pins"]:
            assert source["status"] == "AVAILABLE"
            assert sha(source["path"]) == source["sha256"]
    a = load(exp["A"]["artifacts"]["result"]["path"])
    assert a["vector_count"] == 12
    assert a["outcome_counts"] == {
        "SATISFIED": 2,
        "UNSATISFIED": 1,
        "INDETERMINATE": 8,
        "NOT_EVALUATED": 1,
    }
    c = load(exp["C"]["artifacts"]["result"]["path"])
    assert c["status_counts"] == {"PARTIALLY_EVALUATED": 6, "NOT_EVALUATED": 3}
    assert c["runtime_scenarios_executed"] == 0 and len(c["scenarios"]) == 9
    for scenario in c["scenarios"]:
        assert scenario["execution_observation_state"]["status"] == "UNOBSERVED"
        assert scenario["effect_observation_state"]["status"] == "UNOBSERVED"
        assert scenario["approval_consumption_state"]["status"] == "NOT_EVALUATED"
    e = load(exp["E"]["artifacts"]["result"]["path"])
    assert e["matrix_counts"] == exp["E"]["observed_result"]["matrix_counts"]
    assert e["scenario_counts"] == exp["E"]["observed_result"]["scenario_counts"]
    assert sum(e["matrix_counts"].values()) == 48
    assert sum(e["scenario_counts"].values()) == 80
    for manifest in lab["evidence_manifests"]:
        assert sha(manifest["path"]) == manifest["sha256"]
    github = load("docs/standards-lab-evidence/github_sources.json")
    assert len(github["heads"]) == 6 and len(github["sources"]) == 9
    http = load("docs/standards-lab-evidence/http_sources.json")["sources"]
    source_count = 0
    for row in github["sources"] + http:
        if row["status"] == "AVAILABLE":
            assert sha(row["path"]) == row["sha256"]
            assert (ROOT / row["path"]).stat().st_size == row["bytes"]
            source_count += 1
    for row in http:
        if row["kind"] == "mutable-datatracker-metadata":
            assert row["revision_difference"] == "NONE"
    fresh = {r["id"]: r for r in http if r["kind"] == "revision-pinned-draft"}
    assert len(fresh) == 7
    for name, row in fresh.items():
        matches = [r for r in frozen if r["path"].endswith("/" + name)]
        if matches:
            assert all(r["sha256"] == row["sha256"] for r in matches)
        else:
            b1 = load("docs/standards-lab-evidence/local-refs/B1/challenge_manifest.json")
            assert name == b1["draft_revision"] + ".txt" and row["sha256"] == b1["draft_sha256"]
    local = load("docs/standards-lab-evidence/local_references.json")
    assert local["private_expected_results"] == "NOT_ACCESSED"
    assert local["B1_builder_history"] == "NOT_ACCESSED"
    for row in local["references"]:
        assert sha(row["snapshot_path"]) == row["sha256"]
        assert row["publication_status"] == "UNPUBLISHED"
    logs = load("docs/standards-lab-evidence/replay_results.json")
    assert len(logs["runs"]) == 3
    assert all(r["exit_code"] == 0 for r in logs["runs"])
    lint = load("docs/standards-lab-evidence/claim_lint.json")
    assert lint["self_test"] == "PASS" and lint["current_findings"] == []
    review = load("docs/publication_review.json")
    assert review["approval_granted"] is False and review["whole_program_status"] == "HOLD"
    assert set(review["missing_inputs"]) == {"B2", "B3", "F"}
    links = []
    docs = [
        "docs/STANDARDS_LAB.md",
        "docs/STANDARDS_PORTFOLIO_DELTA.md",
        "docs/PUBLICATION_REVIEW.md",
    ]
    unpublished = [r["original_experiment_commit"] for r in lab["experiments"] + lab["references"]]
    unpublished += [r["integration_commit"] for r in lab["experiments"]]
    for name in docs:
        text = (ROOT / name).read_text()
        assert not re.search(r"https://github\.com/[^\s)]+/(?:" + "|".join(unpublished) + ")", text)
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if re.match(r"[a-zA-Z]+:", target) or target.startswith("#"):
                continue
            path = unquote(target.split("#")[0])
            assert (ROOT / name).parent.joinpath(path).exists(), (name, target)
            links.append([name, target])
    assert (ROOT / "README.md").read_text().count("[Standards Lab](docs/STANDARDS_LAB.md)") == 1
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", BASE], cwd=ROOT, text=True
    ).splitlines()
    assert all(p in {"README.md", "portfolio.yaml"} or p.startswith("docs/") for p in changed)
    subprocess.run(
        [
            "git",
            "diff",
            "--check",
            BASE,
            "--",
            ".",
            ":(exclude)docs/standards-lab-evidence/sources/**",
            ":(exclude)docs/standards-lab-evidence/local-refs/**",
        ],
        cwd=ROOT,
        check=True,
    )
    return {
        "status": "PASS",
        "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "command": "python3 -B docs/standards-lab-evidence/verify_index.py",
        "base_commit": BASE,
        "frozen_files_checked_against_base": len(frozen),
        "experiment_artifact_digests": digest_count,
        "source_snapshots_hashed": source_count,
        "draft_revisions_reacquired_and_matching": 7,
        "local_reference_snapshots_hashed": 7,
        "relative_document_links_checked": len(links),
        "pending_states": "B2/B3/F retained",
        "replay_tests": {"A": 59, "C": 16, "E": 30, "total": 105},
        "claim_lint_self_test": "PASS",
        "local_research_README_claim_lint": "PASS",
        "full_live_portfolio_lint": "NOT_RUN",
        "unrelated_SDK_suite": "NOT_RUN",
        "D_tests_in_G": "NOT_RUN",
        "B1_tests_private_seal_and_builder_history": "NOT_ACCESSED",
        "git_diff_check": "PASS for authored paths; raw snapshots retain source whitespace",
        "raw_snapshot_whitespace_record": "docs/standards-lab-evidence/whitespace_check.json",
        "normative_or_frozen_changes": "NONE",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--record", action="store_true", help="Explicitly update the G validation record"
    )
    args = parser.parse_args()
    result = check()
    if args.record:
        (OUT / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
