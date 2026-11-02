"""Hash exact H1 review artifacts and copy only report/metadata snapshots."""

import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE = Path(
    "/home/toygar/Documents/ChatGPT/AACDE/standards-reentry/2026-11-02/h1-acder-evidence-gate/phionyx-research"
)
COMMIT = "57ab6d0f186f42f6a6788bb7b64b59bcae602424"
PREFIX = "research/standards-reentry/2026-11-02/h1/"


def git(*args):
    return subprocess.check_output(
        ["git", "-c", "safe.directory=" + str(SOURCE), "-C", str(SOURCE), *args]
    )


def sha(data):
    return hashlib.sha256(data).hexdigest()


def collect():
    assert git("rev-parse", "HEAD").decode().strip() == COMMIT
    assert git("status", "--porcelain=v1") == b""
    paths = (
        git("ls-tree", "-r", "--name-only", COMMIT, "--", PREFIX).decode().splitlines()
    )
    assert len(paths) == 26
    data = {}
    inventory = []
    for path in paths:
        raw = git("show", COMMIT + ":" + path)
        assert raw == (SOURCE / path).read_bytes()
        data[path[len(PREFIX) :]] = raw
        inventory.append(
            {
                "path": path,
                "local_path": str(SOURCE / path),
                "commit": COMMIT,
                "sha256": sha(raw),
                "bytes": len(raw),
            }
        )
    sums = data["ARTIFACT_SHA256SUMS"].decode().splitlines()
    assert len(sums) == 25
    for line in sums:
        expected, name = line.split("  ", 1)
        assert sha(data[name]) == expected
    pins = json.loads(data["SOURCE_PINS.json"])
    sources = [s for doc in pins["documents"] for s in doc["sources"]] + [
        pins["referenced_by"]
    ]
    assert len(sources) == 12
    for row in sources:
        assert sha(data[row["path"]]) == row["sha256"]
        assert len(data[row["path"]]) == row["bytes"]
    ledger = json.loads(data["EVIDENCE_LEDGER.json"])
    count = 0
    for evidence in ledger["evidence"]:
        for row in evidence["files"]:
            raw = data[row["snapshot_path"]]
            assert sha(raw) == row["sha256"] and len(raw) == row["bytes"]
            local = ROOT / row["source_path"]
            if evidence["label"] == "F":
                local = OUT / "local-refs/F" / Path(row["source_path"]).name
            assert local.read_bytes() == raw
            count += 1
    assert count == 8 and ledger["private_expected_outputs_read"] is False
    run = json.loads(data["run_record.json"])
    assert run["decision"] == "NO_GO_ON_AVAILABLE_EVIDENCE"
    assert run["proposed_change_count"] == run["normative_change_count"] == 0
    assert run["patch"] is None and not run["publication_approval_granted"]
    snapshots = []
    for name in [
        "ACDER_03_NO_GO.md",
        "SOURCE_PINS.json",
        "EVIDENCE_LEDGER.json",
        "run_record.json",
        "ARTIFACT_SHA256SUMS",
    ]:
        dest = OUT / "local-refs/H1" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data[name])
        snapshots.append(
            {
                "snapshot_path": str(dest.relative_to(ROOT)),
                "source_path": PREFIX + name,
                "sha256": sha(data[name]),
                "bytes": len(data[name]),
            }
        )
    assert git("status", "--porcelain=v1") == b""
    result = {
        "id": "H1",
        "status": "COMPLETE_SCOPED_NO_GO_REFERENCE_ONLY",
        "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "repository": "halvrenofviryel/phionyx-research",
        "local_checkout": str(SOURCE),
        "original_experiment_commit": COMMIT,
        "integration_commit": None,
        "publication_status": "UNPUBLISHED",
        "approval_granted": False,
        "evidence_class": "AUTHOR_SIDE_EVIDENCE_GATE_REVIEW",
        "third_party_evidence": False,
        "observed_result": {
            "decision": run["decision"],
            "proposed_changes": 0,
            "normative_changes": 0,
            "patch": None,
            "B3_dependent_gate": "NOT_COMPLETE",
            "G_exact_files_hashed": 26,
            "G_ledger_hashes_checked": 25,
            "G_source_pin_hashes_checked": 12,
            "G_evidence_snapshot_hashes_checked": 8,
        },
        "scope": "G checks exact committed bytes and attributed decision only; no independent normative review or runtime rerun.",
        "non_claims": [
            "Scoped NO-GO does not mean ACDER-02 is defect-free or B3-dependent interoperability review is complete.",
            "B2/B3 absent; enforced isolation not established. No private answers or builder history read.",
            "No ACDER patch, normative change, draft submission, adoption or independent external validation.",
        ],
        "artifacts": inventory,
        "snapshots": snapshots,
    }
    (OUT / "h1_reference.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": "PASS",
                "exact_files": 26,
                "manifest_hashes": 25,
                "public_pins": 12,
                "report_snapshots_compared": 8,
                "copied_report_metadata_files": 5,
                "decision": run["decision"],
            }
        )
    )


if __name__ == "__main__":
    collect()
