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
        "integrated_experiments": 4,
        "completed_result_references": 2,
        "separate_editorial_candidates": 1,
        "completed_scoped_review_references": 1,
        "preparation_packages": 1,
        "pending_results": 2,
        "third_party_validations_added": 0,
    }
    assert {p["id"] for p in lab["pending"]} == {"B2", "B3"}
    for pending in lab["pending"]:
        assert pending["status"] == "PENDING" and pending["result"] == "NOT_EVALUATED"
        assert pending["commit"] is None and not pending["counted_as_success"]
    frozen = load("docs/standards-lab-evidence/frozen_inputs.json")["files"]
    assert len(frozen) == 123
    for row in frozen:
        assert sha(row["path"]) == row["sha256"], row["path"]
        blob = subprocess.check_output(
            ["git", "show", BASE + ":" + row["path"]], cwd=ROOT
        )
        assert hashlib.sha256(blob).hexdigest() == row["sha256"]
    exp = {e["id"]: e for e in lab["experiments"]}
    assert set(exp) == {"A", "C", "C04", "E"}
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
    c04 = load(exp["C04"]["artifacts"]["result"]["path"])
    assert len(c04["vectors"]) == 10 and len(c04["controls"]) == 6
    assert {r["id"]: r["measured_cli"]["exit_code"] for r in c04["vectors"]} == {
        "F1": 2,
        "F2": 2,
        "F3": 0,
        "F4": 2,
        "F5": 0,
        "F6": 0,
        "F7": 0,
        "F8": 0,
        "F9": 0,
        "F10": 0,
    }
    assert all(r["signature_verified"] for r in c04["vectors"])
    assert all(
        r["full_draft_procedure_execution"] == "NOT_EVALUATED" for r in c04["vectors"]
    )
    assert (
        next(r for r in c04["vectors"] if r["id"] == "F10")["consumption_enforcement"]
        == "NOT_EVALUATED"
    )
    assert (
        c04["runtime_execution"] == "NOT_EVALUATED"
        and c04["effect_observation"] == "UNOBSERVED"
    )
    c04_inventory = load("docs/standards-lab-evidence/c04_integration.json")
    assert len(c04_inventory["files"]) == 55
    for row in c04_inventory["files"]:
        assert sha(row["path"]) == row["sha256"]
        raw = subprocess.check_output(
            ["git", "show", c04_inventory["integration_commit"] + ":" + row["path"]],
            cwd=ROOT,
        )
        assert hashlib.sha256(raw).hexdigest() == row["sha256"]
    replay04 = load("docs/standards-lab-evidence/c04_replay.json")
    assert replay04["status"] == "PASS" and replay04["tests_passed"] == 13
    assert (
        replay04["byte_identical_artifacts"] == 33
        and replay04["normalization"] == "NONE"
    )
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
            b1 = load(
                "docs/standards-lab-evidence/local-refs/B1/challenge_manifest.json"
            )
            assert (
                name == b1["draft_revision"] + ".txt"
                and row["sha256"] == b1["draft_sha256"]
            )
    revision = load("docs/standards-lab-evidence/audit04_discovery.json")
    assert sha(revision["path"]) == revision["expected_sha256"] == revision["sha256"]
    assert (
        revision["C04_experiment"] == "PENDING"
        and revision["C04_tests_in_G"] == "NOT_RUN"
    )
    assert exp["C"]["revision_update"]["historical_discovery"] == revision
    assert exp["C"]["revision_update"]["current_addendum_status"] == "COMPLETE_LOCAL"
    local = load("docs/standards-lab-evidence/local_references.json")
    assert local["private_expected_results"] == "NOT_ACCESSED"
    assert local["B1_builder_history"] == "NOT_ACCESSED"
    for row in local["references"]:
        assert sha(row["snapshot_path"]) == row["sha256"]
        assert row["publication_status"] == "UNPUBLISHED"
    update = load("docs/standards-lab-evidence/update_references.json")
    refs = {row["id"]: row for row in lab["references"]}
    assert set(refs) == {"D", "B1", "F", "H2", "H1"}
    h1 = load("docs/standards-lab-evidence/h1_reference.json")
    assert refs["H1"] == h1
    assert h1["observed_result"]["decision"] == "NO_GO_ON_AVAILABLE_EVIDENCE"
    assert (
        h1["observed_result"]["normative_changes"] == 0
        and h1["observed_result"]["patch"] is None
    )
    assert h1["observed_result"]["B3_dependent_gate"] == "NOT_COMPLETE"
    for row in h1["snapshots"]:
        assert sha(row["snapshot_path"]) == row["sha256"]
    assert refs["F"]["status"] == "COMPLETE_LOCAL_DEMO_REFERENCE_ONLY"
    assert (
        refs["F"]["observed_result"][
            "SCITT_signature_registration_identity_verification"
        ]
        == "NOT_EVALUATED"
    )
    assert (
        refs["F"]["original_experiment_commit"]
        == "84fe0aa9f29034aa6b873c0e83d689dc821bb398"
    )
    assert refs["F"]["parent_commit"] == refs["D"]["original_experiment_commit"]
    assert update["F"]["archive_members_verified"] == 138
    assert update["F"]["tests_rerun_in_G"] is False
    for row in update["F"]["snapshots"]:
        assert sha(row["snapshot_path"]) == row["sha256"]
    assert (
        refs["H2"]["original_experiment_commit"]
        == "9e4524a1f4312c25b88af9444a7740662104b09a"
    )
    assert refs["H2"]["observed_result"]["normative_changes"] == 0
    assert refs["H2"]["candidate_files_copied_to_G"] is False
    assert update["H2"]["BCP14_elements_unchanged"] is True
    assert len(refs["H2"]["artifacts"]) == 26
    assert update["B2_B3"]["enforced_isolation"] == "NOT_ESTABLISHED"
    assert not (ROOT / "integrations/scitt-claim-boundaries").exists()
    assert not (
        ROOT / "standards/ietf/ai-evaluation-claim-preservation/candidate/01"
    ).exists()
    # A derived index must agree with its builder, excluding the generation clock.
    import runpy

    rebuilt = runpy.run_path(str(OUT / "build_index.py"))["build"]()
    assert {k: v for k, v in lab.items() if k != "generated_at_utc"} == {
        k: v for k, v in rebuilt.items() if k != "generated_at_utc"
    }
    logs = load("docs/standards-lab-evidence/replay_results.json")
    assert len(logs["runs"]) == 3
    assert all(r["exit_code"] == 0 for r in logs["runs"])
    lint = load("docs/standards-lab-evidence/claim_lint.json")
    assert lint["self_test"] == "PASS" and lint["current_findings"] == []
    review = load("docs/publication_review.json")
    assert (
        review["approval_granted"] is False and review["whole_program_status"] == "HOLD"
    )
    assert set(review["missing_inputs"]) == {"B2", "B3"}
    links = []
    docs = [
        "docs/STANDARDS_LAB.md",
        "docs/STANDARDS_PORTFOLIO_DELTA.md",
        "docs/PUBLICATION_REVIEW.md",
        "docs/PUBLICATION_PR_DRAFT.md",
        "docs/PUBLICATION_STATUS.md",
        "docs/standards-lab-evidence/README.md",
    ]
    unpublished = [
        r["original_experiment_commit"] for r in lab["experiments"] + lab["references"]
    ]
    unpublished += [r["integration_commit"] for r in lab["experiments"]]
    for name in docs:
        text = (ROOT / name).read_text()
        assert not re.search(
            r"https://github\.com/[^\s)]+/(?:" + "|".join(unpublished) + ")", text
        )
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if re.match(r"[a-zA-Z]+:", target) or target.startswith("#"):
                continue
            path = unquote(target.split("#")[0])
            assert (ROOT / name).parent.joinpath(path).exists(), (name, target)
            links.append([name, target])
    assert (ROOT / "README.md").read_text().count(
        "[Standards Lab](docs/STANDARDS_LAB.md)"
    ) == 1
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", BASE], cwd=ROOT, text=True
    ).splitlines()
    candidate_manifest_path = "docs/PREPUBLICATION_FILE_MANIFEST.json"
    if (ROOT / candidate_manifest_path).exists():
        candidate_manifest = load(candidate_manifest_path)
        assert candidate_manifest["schema"] == "phionyx-prepublication-file-manifest-v1"
        assert candidate_manifest["historical_lab_base"] == BASE
        manifest_files = candidate_manifest["files"]
        assert [row["path"] for row in manifest_files] == sorted(
            row["path"] for row in manifest_files
        )
        assert len({row["path"] for row in manifest_files}) == len(manifest_files)
        for row in manifest_files:
            path = ROOT / row["path"]
            assert path.is_file(), row["path"]
            assert path.stat().st_size == row["bytes"], row["path"]
            assert sha(row["path"]) == row["sha256"], row["path"]
        assert set(changed) == {
            candidate_manifest_path,
            *(row["path"] for row in manifest_files),
        }
    else:
        assert all(
            p in {"README.md", "portfolio.yaml"}
            or p.startswith("docs/")
            or p in {r["path"] for r in c04_inventory["files"]}
            for p in changed
        )
    diff_check = [
        "git",
        "diff",
        "--check",
        BASE,
        "--",
        ".",
        ":(exclude)docs/standards-lab-evidence/sources/**",
        ":(exclude)docs/standards-lab-evidence/local-refs/**",
        ":(exclude)experiments/ietf/audit/decision-receipts-04/sources/**",
        ":(exclude)experiments/ietf/audit/decision-receipts-04/evidence/**",
    ]
    if candidate_manifest.exists():
        # These directories preserve byte-exact upstream licence/METADATA files
        # and review diffs. Original whitespace is covered by the exact candidate
        # manifest and the packet's own MANIFEST.json rather than normalized.
        diff_check.extend(
            [
                ":(exclude)docs/external-replication/**",
                ":(exclude)reports/external-replication/**",
            ]
        )
    subprocess.run(
        diff_check,
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
        "prior_draft_revisions_reacquired_and_matching": 7,
        "new_revision_bytes_verified": "decision-receipts-04 exact bytes verified; C04 separately reproduced",
        "local_reference_snapshots_hashed": 16,
        "F_archive_member_check": "138 hashes verified by collect_update_refs.py; runtime not rerun",
        "H2_artifact_check": "26 exact-commit files, 13 paragraph anchors and 12 normative sections checked; rendering not rerun",
        "relative_document_links_checked": len(links),
        "pending_states": "B2/B3 retained with enforced isolation NOT_ESTABLISHED; C04 complete, H1 scoped NO-GO; AUDIT NO_OUTREACH_NOW / HOLD",
        "prior_replay_tests": {"A": 59, "C": 16, "E": 30, "total": 105},
        "new_C04_tests_reproduced_in_G": 13,
        "C04_byte_identical_artifacts": 33,
        "C04_exact_committed_files_verified": 55,
        "H1_integrity_check": "26 exact-commit files, 25 manifest hashes, 12 source pins and 8 report/run snapshots; no normative rereview",
        "A_C03_E_tests_rerun_in_update": 0,
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
        "--record",
        action="store_true",
        help="Explicitly update the G validation record",
    )
    args = parser.parse_args()
    result = check()
    if args.record:
        (OUT / "update_validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
