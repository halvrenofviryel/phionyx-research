"""Build the local G index from explicit experiment records; no external writes."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = Path(__file__).resolve().parent


def read(path):
    return json.loads((ROOT / path).read_text())


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def artifact(path):
    return {"path": path, "sha256": digest(path)}


def build():
    initial = read("docs/standards-lab-evidence/initial_state.json")
    mapping = {r["task"]: r for r in initial["integration_mapping"]}
    paths = {
        "A": "experiments/ietf/agentproto/verifier-evidence-03",
        "C": "experiments/ietf/audit/decision-receipts-03",
        "E": "experiments/ietf/claim-preservation/ser04",
    }
    http = read("docs/standards-lab-evidence/http_sources.json")["sources"]
    source_map = {r["id"]: r for r in http}
    definitions = [
        {
            "id": "A",
            "name": "Draft-text completeness appraisal",
            "external_targets": ["draft-he-agentproto-verifier-evidence-03"],
            "why_tested": "Keep supplied-record validity separate from independently appraised domain completeness (CMP-1/CMP-2).",
            "reproduction_command": "python3 experiments/ietf/agentproto/verifier-evidence-03/reproduce.py",
            "prerequisites": "Python 3.10+ and pytest; evaluator is stdlib-only; offline replay.",
            "evidence_class": "INDEPENDENTLY_DEVELOPED_FROM_TEXT_INTERNAL_RUN",
            "class_boundary": "Independent of linked implementation code per original methodology; same controlled task environment, not an external independent evidence root.",
            "observed_result": {
                "vectors": 12,
                "SATISFIED": 2,
                "UNSATISFIED": 1,
                "INDETERMINATE": 8,
                "NOT_EVALUATED": 1,
                "tests_passed_in_G": 59,
                "replay": "BYTE_IDENTICAL",
            },
            "non_claims": [
                "Positive cases depend on a stipulated finite exhaustive counterparty index, synthetic authority/control/input-selection/scope/time facts; those facts are not externally authenticated.",
                "No event truth, actual-population completeness, signature validation, author-code interoperability, full draft or EXR-1/CMP-2 exercise conformance, third-party validation, or IETF endorsement.",
                "Local precommitment digests and timestamps are not externally witnessed chronology.",
            ],
            "source_manifest": "sources/manifest.json",
            "result": "results.json",
        },
        {
            "id": "C",
            "name": "Released decision-receipt API/CLI probe",
            "external_targets": [
                "draft-gruszka-audit-decision-receipts-03",
                "draft-gruszka-signed-evaluation-receipts-04",
            ],
            "external_implementation": {
                "repository": "b7n0de/proofbundle",
                "version": "6.4.0",
                "commit": "699545521ec5ef479bb84e61fe7461fc79ed558c",
                "wheel_sha256": "72153d160c2f78647095f029c0946dbfd64a15e006a233a5abc78a3071eebf94",
                "preview_commit": "8bb289c8b41d32c54734155fc00756231093bc2a",
                "preview_runtime": "NOT_EVALUATED",
            },
            "why_tested": "Separate receipt validity, approval consumption, set audit, execution and effect observations in the released implementation.",
            "reproduction_command": "bash experiments/ietf/audit/decision-receipts-03/reproduce.sh",
            "prerequisites": "CPython 3.12, venv/pip, Linux x86_64 compatible locked wheels; uses local cache or hash-checked HTTPS PyPI download in a fresh checkout.",
            "evidence_class": "INTERNAL_PROBE_OF_EXTERNAL_RELEASE",
            "class_boundary": "External package authorship does not make this internal synthetic probe third-party validation of AIREP or ACDER.",
            "observed_result": {
                "scenarios": 9,
                "PARTIALLY_EVALUATED": 6,
                "NOT_EVALUATED": 3,
                "execution_observation_all": "UNOBSERVED",
                "effect_observation_all": "UNOBSERVED",
                "approval_consumption_all": "NOT_EVALUATED",
                "set_audit_section_3_5_all": "NOT_EVALUATED",
                "runtime_executions_observed": 0,
                "cli_vectors": 7,
                "tests_passed_in_G": 16,
                "byte_identical_artifacts": 20,
            },
            "non_claims": [
                "No end-to-end runtime scenario, approval consumption/rotation/re-allow behavior, actual execution or effect, full population, full draft conformance, or independent operator measured.",
                "Legacy execution_proven describes digest presence, not event truth; supplied min/max sequence completeness is not population completeness.",
                "Two outcome receipts do not prove two executions; evaluation evidence does not turn DENY into authorization.",
                "Only verified_origin report tokens are normalized after API/policy calls; initial unmodified capture and first failed cross-process replay remain archived.",
            ],
            "source_manifest": "sources/manifest.json",
            "result": "cases/scenario_results.json",
        },
        {
            "id": "E",
            "name": "Claim preservation across SER and selected representations",
            "external_targets": [
                "draft-abak-ai-evaluation-claim-preservation-00",
                "draft-gruszka-signed-evaluation-receipts-04",
                "draft-gruszka-evaluation-receipt-mappings-04",
                "draft-watts-eqr-conformance-05",
            ],
            "external_fixture_commit": "a339424e07fd58fa261d8ca3f41af5de4dcbf751",
            "why_tested": "Measure which claim distinctions survive direct SER, DSSE, digest-only and digest-resolved representations.",
            "reproduction_command": "python3 experiments/ietf/claim-preservation/ser04/src/run.py --check",
            "prerequisites": "Python 3.10+ standard library; offline replay.",
            "evidence_class": "AUTHOR_SIDE_NON_NORMATIVE_MAPPING_EXPERIMENT",
            "class_boundary": "Same-author local semantic experiment; EQR-05 is context only, not an implemented conformance target.",
            "observed_result": {
                "requirement_route_cells": 48,
                "matrix_counts": {
                    "PRESERVED": 17,
                    "QUALIFIED_LOSS": 10,
                    "UNESTABLISHED": 17,
                    "NOT_APPLICABLE": 4,
                },
                "scenario_route_observations": 80,
                "scenario_counts": {
                    "PRESERVED": 34,
                    "QUALIFIED_LOSS": 17,
                    "UNESTABLISHED": 13,
                    "NOT_APPLICABLE": 16,
                },
                "tests_passed_in_G": 30,
                "replay": "BYTE_IDENTICAL",
                "SER_Ed25519_selected_key_COSE_SCITT_verification": "NOT_EVALUATED",
            },
            "non_claims": [
                "The 48 bounded requirement-by-route cells are distinct from 80 scenario-by-route observations; PRESERVED does not implement every clause and NOT_APPLICABLE is not success.",
                "No full CP/SER conformance, independent interoperability, real evaluator/model execution, criteria chronology, complete populations, trusted identity, safety, authorization, or endorsement.",
                "No SER Ed25519/selected-key, COSE or SCITT verification; local HMAC test carrier is a separate synthetic check.",
                "All 66 reconstructed receipt byte strings match the pinned public vectors; proofbundle code and its 66 verification verdicts were not executed.",
            ],
            "source_manifest": "SOURCE_PINS.json",
            "result": "results.json",
        },
    ]
    for exp in definitions:
        path = paths[exp["id"]]
        exp.update(
            status="COMPLETE_LOCAL",
            publication_status="UNPUBLISHED",
            repository="halvrenofviryel/phionyx-research",
            original_experiment_commit=mapping[exp["id"]]["original_commit"],
            integration_commit=mapping[exp["id"]]["integration_commit"],
            path=path,
            third_party_evidence=False,
            report_path=path + "/RESULTS.md",
            readme_path=path + "/README.md",
        )
        exp["source_pins"] = [source_map[t + ".txt"] for t in exp["external_targets"]]
        exp["artifacts"] = {
            "run_record": artifact(path + "/run_record.json"),
            "source_manifest": artifact(path + "/" + exp.pop("source_manifest")),
            "result": artifact(path + "/" + exp.pop("result")),
            "report": artifact(path + "/RESULTS.md"),
        }
    local = read("docs/standards-lab-evidence/local_references.json")["references"]
    d = [r for r in local if r["task"] == "D"]
    b1 = [r for r in local if r["task"] == "B1"]
    refs = [
        {
            "id": "D",
            "status": "COMPLETE_LOCAL_REFERENCE_ONLY",
            "publication_status": "UNPUBLISHED",
            "repository": d[0]["repository"],
            "original_experiment_commit": d[0]["original_commit"],
            "integration_commit": None,
            "local_checkout": "/home/toygar/.codex/worktrees/a4cd/ai-runtime-evidence-protocol",
            "external_target": {
                "wire_version": "0.2",
                "implementation_version": "0.2.0-beta.1",
                "source_commit": "075aff5610731736405951ecf3b7c4bfc3cc0f07",
            },
            "why_tested": "Expose native lifecycle evidence and absent enforcement/coverage distinctions without stronger claims.",
            "reproduction_command": "python3 scripts/check_beta.py --out .reproduced/g-explain-check",
            "reproduction_scope": "Run in a disposable copy of the exact D commit with its documented Python/Node dependencies; G did not run this command or write in D.",
            "evidence_class": "AUTHOR_SIDE_REGRESSION",
            "third_party_evidence": False,
            "observed_result": "Original D validation reports 73 v0.2 tests and final 56/56 commands, 1919 historical files unchanged; first sandbox failure retained. G checked exact-commit report bytes only.",
            "non_claims": [
                "Enforcement, relying-party claim evaluation and intended-target coverage remain NOT_EVALUATED; signatures do not prove event truth.",
                "No schema, reconciliation semantics or frozen v0.1 change; not third-party or IETF evidence.",
            ],
            "artifacts": d,
        },
        {
            "id": "B1",
            "status": "SEALED_PREPARATION_ONLY",
            "publication_status": "UNPUBLISHED",
            "repository": b1[0]["repository"],
            "original_experiment_commit": b1[0]["original_commit"],
            "integration_commit": None,
            "local_checkout": "/home/toygar/Documents/ChatGPT/AACDE/standards-reentry/2026-11-02/b1-acder-sealed-challenge/phionyx-research",
            "external_target": "draft-abak-agent-control-delivery-evidence-02",
            "why_tested": "Prepare a bounded, sealed ACDER-02 challenge for a future isolated implementation.",
            "evidence_class": "AUTHOR_SIDE_CHALLENGE_PREPARATION",
            "third_party_evidence": False,
            "observed_result": "Public manifest lists 14 cases / 15 declared profile runs; sealed commitment exists; solver and reveal comparison absent.",
            "commitment_sha256": "804c65c50dea4064f5e3d411c469a0089bb0ca9a061713c23793b572868193f8",
            "reproduction_command": None,
            "reproduction_status": "NOT_EVALUATED; G hashes public metadata only and does not run builder/private tests.",
            "non_claims": [
                "No B2 execution or B3 comparison, no established blindness, no third-party independence, no full draft conformance or event truth.",
                "Same-UID file permissions do not establish isolation. Original commit attributed to coordinator; builder history and private expected results were not accessed.",
            ],
            "artifacts": b1,
        },
    ]
    pending = [
        {
            "id": name,
            "status": "PENDING",
            "result": "NOT_EVALUATED",
            "commit": None,
            "reason": reason,
            "counted_as_success": False,
        }
        for name, reason in [
            (
                "B2",
                "No isolated solver implementation/output supplied; access boundary not established.",
            ),
            (
                "B3",
                "No frozen solver/reveal comparison supplied; B1 seal is not a comparison result.",
            ),
            (
                "F",
                "Separate task in progress at handoff; no frozen exact-commit compatibility result supplied.",
            ),
        ]
    ]
    return {
        "schema": "local-standards-lab-index-1",
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": "Non-normative local documentation index; not a protocol schema or certification.",
        "approval_granted": False,
        "publication_status": "UNPUBLISHED",
        "base_commit": initial["base_commit"],
        "integration_mapping": initial["integration_mapping"],
        "counts": {
            "integrated_experiments": 3,
            "completed_result_references": 1,
            "preparation_packages": 1,
            "pending_results": 3,
            "third_party_validations_added": 0,
        },
        "experiments": definitions,
        "references": refs,
        "pending": pending,
        "evidence_manifests": [
            artifact("docs/standards-lab-evidence/" + p)
            for p in [
                "initial_state.json",
                "frozen_inputs.json",
                "github_sources.json",
                "http_sources.json",
                "local_references.json",
                "replay_results.json",
            ]
        ],
        "non_claims": [
            "Internal Codex runs are not independent third-party evidence or IETF conformance.",
            "AIREP EXTERNAL_EVIDENCE.md was read under its existing external-artifact/maintainer-reproduction methodology, not modified.",
            "No same-version external AIREP producer/consumer interoperability is established by this index.",
            "No push, PR, issue, release, hosting, message or Internet-Draft submission is authorized or performed.",
        ],
    }


if __name__ == "__main__":
    (ROOT / "docs/standards_lab.json").write_text(json.dumps(build(), indent=2) + "\n")
