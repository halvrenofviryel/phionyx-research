"""Verify exact local F/H2 artifacts without running or modifying either source repo."""

import datetime
import hashlib
import io
import json
import subprocess
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
F_ROOT = Path("/home/toygar/.codex/worktrees/dd94/ai-runtime-evidence-protocol")
F_COMMIT = "84fe0aa9f29034aa6b873c0e83d689dc821bb398"
D_COMMIT = "0130fcf8e7d70a0f9c4f977957e5de76ca8ef689"
F_PREFIX = "integrations/scitt-claim-boundaries/"
H_ROOT = Path(
    "/home/toygar/Documents/ChatGPT/AACDE/standards-reentry/2026-11-02/h2-claim-preservation-candidate/phionyx-research"
)
H_COMMIT = "9e4524a1f4312c25b88af9444a7740662104b09a"
H_PREFIX = "standards/ietf/ai-evaluation-claim-preservation/candidate/01/"


def git(root, *args):
    return subprocess.check_output(
        ["git", "-c", "safe.directory=" + str(root), "-C", str(root), *args]
    )


def sha(data):
    return hashlib.sha256(data).hexdigest()


def blob(root, commit, path):
    data = git(root, "show", commit + ":" + path)
    assert data == (root / path).read_bytes(), path
    return data


def inventory(root, commit, paths):
    return [
        {
            "path": p,
            "local_path": str(root / p),
            "sha256": sha(blob(root, commit, p)),
            "bytes": len(blob(root, commit, p)),
            "commit": commit,
            "verified_against_exact_git_blob": True,
        }
        for p in paths
    ]


def normalized_element(element):
    return (
        element.tag,
        sorted(element.attrib.items()),
        " ".join((element.text or "").split()),
        [normalized_element(child) for child in element],
        " ".join((element.tail or "").split()),
    )


def collect():
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    states = {}
    for name, root, commit in [("F", F_ROOT, F_COMMIT), ("H2", H_ROOT, H_COMMIT)]:
        states[name] = {
            "head": git(root, "rev-parse", "HEAD").decode().strip(),
            "status_porcelain": git(root, "status", "--porcelain=v1").decode(),
        }
        assert states[name]["head"] == commit and states[name]["status_porcelain"] == ""
    assert git(F_ROOT, "rev-parse", F_COMMIT + "^").decode().strip() == D_COMMIT
    f_paths = (
        git(F_ROOT, "diff", "--name-only", D_COMMIT, F_COMMIT).decode().splitlines()
    )
    assert all(p.startswith(F_PREFIX) for p in f_paths)
    f_inventory = inventory(F_ROOT, F_COMMIT, f_paths)
    run = json.loads(blob(F_ROOT, F_COMMIT, F_PREFIX + "run_record.json"))
    for item in run["review_input_manifest"]:
        assert sha(blob(F_ROOT, F_COMMIT, item["path"])) == item["sha256"]
    pins = blob(F_ROOT, F_COMMIT, F_PREFIX + "SOURCE_PINS.json")
    assert sha(pins) == run["source_pins"]["sha256"]
    archive = blob(F_ROOT, F_COMMIT, F_PREFIX + "evidence.tar.gz")
    assert (
        sha(archive) == run["archive"]["sha256"]
        and len(archive) == run["archive"]["byte_length"]
    )
    archived_scenarios = []
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        members = tar.getmembers()
        assert all(
            m.isfile() and not m.name.startswith("/") and ".." not in Path(m.name).parts
            for m in members
        )
        assert len({m.name for m in members}) == len(members)
        expected = {r["path"]: r for r in run["archive"]["entries"]}
        assert set(expected) == {m.name for m in members}
        for member in members:
            data = tar.extractfile(member).read()
            assert sha(data) == expected[member.name]["sha256"]
            assert len(data) == expected[member.name]["byte_length"]
            if member.name.startswith("demo/") and member.name.endswith(".json"):
                result = json.loads(data)
                assert result["fixture_premise"]["performed_verification"] is False
                assert all(
                    v == "NOT_EVALUATED"
                    for v in result["external_evaluations"].values()
                )
                archived_scenarios.append(
                    {
                        "path": member.name,
                        "sha256": sha(data),
                        "scenario": result["scenario"],
                        "external_evaluations": result["external_evaluations"],
                        "fixture_premise_performed_verification": False,
                    }
                )
        for beta in run["beta_runs"]:
            assert (
                sha(tar.extractfile(beta["archived_results"]).read())
                == beta["results_sha256"]
            )
    assert len(archived_scenarios) == run["scenario_count"] == 3
    assert (
        run["test_counts"]["new_integration"] == 15
        and run["test_counts"]["existing_v02"] == 73
    )
    assert [(r["label"], r["passed"], r["commands"]) for r in run["beta_runs"]] == [
        ("sandbox", 47, 56),
        ("authorized", 56, 56),
    ]
    f_snapshots = []
    for name in ["README.md", "RESULTS.md", "run_record.json", "SOURCE_PINS.json"]:
        data = blob(F_ROOT, F_COMMIT, F_PREFIX + name)
        dest = OUT / "local-refs" / "F" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        f_snapshots.append(
            {
                "path": F_PREFIX + name,
                "local_path": str(F_ROOT / F_PREFIX / name),
                "snapshot_path": str(dest.relative_to(ROOT)),
                "sha256": sha(data),
                "bytes": len(data),
            }
        )
    # H2 bytes stay exclusively in H2: only newly computed metadata is written to G.
    h_paths = (
        git(H_ROOT, "ls-tree", "-r", "--name-only", H_COMMIT, "--", H_PREFIX)
        .decode()
        .splitlines()
    )
    h_inventory = inventory(H_ROOT, H_COMMIT, h_paths)
    for line in (
        blob(H_ROOT, H_COMMIT, H_PREFIX + "ARTIFACT_SHA256SUMS").decode().splitlines()
    ):
        digest, name = line.split("  ", 1)
        assert sha(blob(H_ROOT, H_COMMIT, H_PREFIX + name)) == digest
    paragraphs = json.loads(
        blob(H_ROOT, H_COMMIT, H_PREFIX + "PARAGRAPH_EVIDENCE.json")
    )
    assert paragraphs["paragraph_count"] == len(paragraphs["paragraphs"]) == 13
    assert paragraphs["normative_change_count"] == 0
    assert all(row["normative_change"] is False for row in paragraphs["paragraphs"])
    assert {r["change_group"] for r in paragraphs["paragraphs"]} == {
        "administrative",
        "C1",
        "C2",
        "C3",
    }
    old = ET.fromstring(
        blob(
            H_ROOT,
            H_COMMIT,
            H_PREFIX + "sources/draft-abak-ai-evaluation-claim-preservation-00.xml",
        )
    )
    new = ET.fromstring(
        blob(
            H_ROOT,
            H_COMMIT,
            H_PREFIX + "draft-abak-ai-evaluation-claim-preservation-01.xml",
        )
    )
    for i in range(1, 13):
        before = old.find(f".//section[@anchor='cp{i}']")
        after = new.find(f".//section[@anchor='cp{i}']")
        assert before is not None and after is not None
        assert normalized_element(before) == normalized_element(after), i
    assert [normalized_element(e) for e in old.findall(".//bcp14")] == [
        normalized_element(e) for e in new.findall(".//bcp14")
    ]
    for row in paragraphs["paragraphs"]:
        found = new.find(f".//t[@anchor='{row['anchor']}']")
        assert found is not None
        expected = ET.fromstring("<t>" + row["xml"] + "</t>")
        found.attrib.clear()
        found.tail = None
        assert normalized_element(found) == normalized_element(expected), row["id"]
    d_paths = (
        git(F_ROOT, "diff", "--name-only", D_COMMIT + "^", D_COMMIT)
        .decode()
        .splitlines()
    )
    # D is an ancestor; hash its exact committed content without assuming current F bytes are identical.
    d_inventory = [
        {
            "path": p,
            "commit": D_COMMIT,
            "sha256": sha(git(F_ROOT, "show", D_COMMIT + ":" + p)),
            "bytes": len(git(F_ROOT, "show", D_COMMIT + ":" + p)),
        }
        for p in d_paths
    ]
    for name, root in [("F", F_ROOT), ("H2", H_ROOT)]:
        assert (
            states[name]["status_porcelain"]
            == git(root, "status", "--porcelain=v1").decode()
        )
    return {
        "schema": "g-local-reference-update-1",
        "checked_at_utc": now,
        "approval_granted": False,
        "update_base_commit": "ef35030b823c37bc373e0718ace59c394dad2944",
        "performed_checks": "Exact commit/worktree bytes, SHA-256, complete archive-member inventory, archived JSON boundaries, H2 checksum ledger/paragraph map/XML checks. No demo, integration tests, CI or rendering rerun.",
        "source_worktrees_before_and_after": states,
        "F": {
            "repository": "halvrenofviryel/ai-runtime-evidence-protocol",
            "local_checkout": str(F_ROOT),
            "commit": F_COMMIT,
            "parent_commit": D_COMMIT,
            "publication_status": "UNPUBLISHED",
            "status": "COMPLETE_LOCAL_DEMO_REFERENCE_ONLY",
            "evidence_class": "SAME_USER_CONTROLLED_LOCAL_SYNTHETIC_DEMO",
            "artifacts": f_inventory,
            "snapshots": f_snapshots,
            "archive_sha256": sha(archive),
            "archive_members_verified": len(members),
            "archived_scenarios": archived_scenarios,
            "reported_tests": {"integration": 15, "v02": 73, "final_beta_commands": 56},
            "tests_rerun_in_G": False,
            "SCITT_signature_registration_identity_verification": "NOT_EVALUATED",
            "non_claims": [
                "Not a SCITT compatibility, interoperability or conformance result.",
                "Local synthetic scenarios and test-key AIREP checks do not establish event truth, real independent observers or a complete history.",
            ],
        },
        "D": {
            "repository": "halvrenofviryel/ai-runtime-evidence-protocol",
            "commit": D_COMMIT,
            "artifacts": d_inventory,
        },
        "H2": {
            "repository": "halvrenofviryel/phionyx-research",
            "local_checkout": str(H_ROOT),
            "commit": H_COMMIT,
            "publication_status": "UNPUBLISHED",
            "status": "COMPLETE_LOCAL_CANDIDATE_REFERENCE_ONLY",
            "user_approval_required": True,
            "candidate_directory": H_PREFIX,
            "artifacts": h_inventory,
            "informative_change_groups": 3,
            "normative_changes": 0,
            "paragraphs": 13,
            "normative_sections_compared": 12,
            "BCP14_elements_unchanged": True,
            "paragraph_xml_mapping": "MATCH",
            "rendering_rerun_in_G": False,
            "candidate_files_copied_to_G": False,
            "non_claims": [
                "Local CP-01 candidate only; not submitted, not public evidence of adoption.",
                "No normative change or new conformance finding; E 48 cells and 80 observations remain separate.",
            ],
        },
        "B2_B3": {
            "status": "PENDING",
            "enforced_isolation": "NOT_ESTABLISHED",
            "private_answers_or_builder_context": "NOT_ACCESSED",
        },
        "source_code_copied_to_research": False,
        "A_C_E_tests_rerun_in_update": False,
    }


if __name__ == "__main__":
    result = collect()
    (OUT / "update_references.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "F_files": len(result["F"]["artifacts"]),
                "F_archive_members": result["F"]["archive_members_verified"],
                "H2_files": len(result["H2"]["artifacts"]),
                "H2_normative_sections": 12,
                "status": "PASS",
            },
            indent=2,
        )
    )
