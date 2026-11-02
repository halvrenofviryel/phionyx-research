"""Inventory immutable local review units; never publish or create a remote object."""

import argparse
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLIC_BASE = "69bc8cfd282e9a0a45e34b1fcf6106b1ab618f9d"
PREPARATION_BASE = "275b871349721a8c917691d457c4a6270fe1028f"
REVIEW_PATHS = {
    "docs/publication_review.json",
    "docs/PUBLICATION_REVIEW.md",
    "docs/PUBLICATION_PR_DRAFT.md",
}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def blob(commit, path):
    return git("show", commit + ":" + path)


def inventory(commit, paths):
    result = []
    for path in sorted(paths):
        data = blob(commit, path)
        result.append(
            {
                "path": path,
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
                "commit": commit,
            }
        )
    return result


def changed(base, commit):
    return git("diff", "--name-only", base, commit).decode().splitlines()


def read(commit, path):
    return json.loads(blob(commit, path))


def seal(g_commit, i_commit):
    g_commit = git("rev-parse", g_commit).decode().strip()
    lab = read(g_commit, "docs/standards_lab.json")
    update = read(g_commit, "docs/standards-lab-evidence/update_references.json")
    initial = read(g_commit, "docs/standards-lab-evidence/initial_state.json")
    assert not lab["approval_granted"]
    assert not any(
        p.startswith("docs/outreach/")
        for p in git("ls-tree", "-r", "--name-only", g_commit).decode().splitlines()
    )
    g_paths = [p for p in changed(PREPARATION_BASE, g_commit) if p not in REVIEW_PATHS]
    prerequisites = changed(PUBLIC_BASE, PREPARATION_BASE)
    g_files = inventory(g_commit, g_paths)
    prerequisite_files = inventory(g_commit, prerequisites)
    u1_files = inventory(g_commit, sorted(set(g_paths + prerequisites)))
    i_unit = {
        "status": "NOT_PREPARED",
        "publication_recommendation": "HOLD",
        "approval_granted": False,
        "files": [],
        "commit": None,
    }
    if i_commit:
        i_commit = git("rev-parse", i_commit).decode().strip()
        paths = (
            git("ls-tree", "-r", "--name-only", i_commit, "--", "docs/outreach/2026-11")
            .decode()
            .splitlines()
        )
        i_unit = {
            "status": "READY_FOR_USER_REVIEW",
            "publication_recommendation": "HOLD",
            "approval_granted": False,
            "commit": i_commit,
            "branch": "codex/standards-lab-outreach-review",
            "files": inventory(i_commit, paths),
            "reason": "Editorial review only; each destination requires separate approval and real public artifact URL. AUDIT is NO_OUTREACH_NOW / HOLD: C04 adds no new bug or technical question.",
            "not_ancestor_of_U1": subprocess.run(
                ["git", "merge-base", "--is-ancestor", i_commit, g_commit],
                cwd=ROOT,
                check=False,
            ).returncode
            == 1,
        }
        assert i_unit["not_ancestor_of_U1"]
    units = {
        "U1_research_lab": {
            "status": "READY_FOR_USER_REVIEW",
            "approval_granted": False,
            "publication_recommendation": "FIRST_SCOPED_CANDIDATE_AFTER_EXPLICIT_APPROVAL",
            "repository": "halvrenofviryel/phionyx-research",
            "commit": g_commit,
            "tree": git("rev-parse", g_commit + "^{tree}").decode().strip(),
            "parent": git("rev-parse", g_commit + "^").decode().strip(),
            "commits_since_public_base": git(
                "rev-list", "--reverse", PUBLIC_BASE + ".." + g_commit
            )
            .decode()
            .splitlines(),
            "files": u1_files,
            "scope": "Only S0/A/C03/C04/E, Standards Lab and bounded README/portfolio corrections; D/F reports are references, no D/F implementation or H2 candidate files.",
            "selection_rule": "Use the exact U1 commit/branch, never the outreach branch or an arbitrary current HEAD. Review metadata is recorded separately below; no remote action is authorized.",
        },
        "U2_outreach": i_unit,
        "U3_AIREP_D_F": {
            "status": "READY_FOR_USER_REVIEW",
            "publication_recommendation": "HOLD_SEPARATE_SCOPE",
            "approval_granted": False,
            "repository": update["F"]["repository"],
            "checkout": update["F"]["local_checkout"],
            "base_commit": "075aff5610731736405951ecf3b7c4bfc3cc0f07",
            "commits": [update["D"]["commit"], update["F"]["commit"]],
            "D_files": update["D"]["artifacts"],
            "F_files": update["F"]["artifacts"],
            "validation": "G verified exact report/commit/archive bytes; 15 integration, 73 v0.2 and 56/56 final beta checks are original F reports, not G reruns. SCITT signature/registration/identity NOT_EVALUATED.",
        },
        "U4_H2_CP01": {
            "status": "READY_FOR_USER_REVIEW",
            "publication_recommendation": "HOLD_SEPARATE_ID_APPROVAL",
            "approval_granted": False,
            "commit": update["H2"]["commit"],
            "checkout": update["H2"]["local_checkout"],
            "files": update["H2"]["artifacts"],
            "validation": "26 exact-commit files, 13 paragraph anchors, 12 unchanged normative sections and BCP14 elements checked; three informative groups, zero normative changes. No candidate files merged into G, no rendering rerun or submission.",
        },
    }
    validation_path = "docs/standards-lab-evidence/update_validation.json"
    result = {
        "schema": "local-publication-review-2",
        "recorded_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "approval_granted": False,
        "approval_requested_in_G": False,
        "recommendation": "READY_FOR_USER_REVIEW",
        "publication_status": "UNPUBLISHED",
        "whole_program_status": "HOLD",
        "reviewed_content_commit": g_commit,
        "reviewed_content_tree": units["U1_research_lab"]["tree"],
        "preparation_base_commit": PREPARATION_BASE,
        "public_source_base_commit": PUBLIC_BASE,
        "review_metadata_commit": "Resolve enclosing metadata commit with git log -1 --format=%H -- docs/publication_review.json; not self-embedded.",
        "destination": {
            "repository": "halvrenofviryel/phionyx-research",
            "publication_performed": False,
            "proposed_branch": "codex/standards-lab-publication-candidate",
            "target_branch": "main (proposed; explicit user approval still required; no PR created).",
        },
        "approval_units": units,
        "G_changed_files": g_files,
        "prerequisite_integration_mapping": initial["integration_mapping"],
        "prerequisite_files_since_public_base": prerequisite_files,
        "review_metadata_files": [
            {
                "path": p,
                "sha256": hashlib.sha256((ROOT / p).read_bytes()).hexdigest(),
                "bytes": (ROOT / p).stat().st_size,
            }
            for p in sorted(REVIEW_PATHS)
            if p != "docs/publication_review.json" and (ROOT / p).exists()
        ],
        "self_inventory_boundary": "This JSON has no self-hash. Its exact bytes are identified by the enclosing metadata commit. Human review and PR drafts are hashed above.",
        "validation": {
            "record": validation_path,
            "sha256": hashlib.sha256(blob(g_commit, validation_path)).hexdigest(),
            "prior_A_C_E_tests": {"A": 59, "C03": 16, "E": 30, "total": 105},
            "A_C_E_runtime_reruns_in_update": 0,
            "F_archive_members_verified": 138,
            "H2_exact_commit_files_verified": 26,
            "C04_tests_reproduced_in_G": 13,
            "C04_byte_identical_artifacts": 33,
            "C04_exact_commit_files_verified": 55,
            "H1_exact_commit_files_verified": 26,
            "frozen_files_unchanged": 123,
            "D_F_runtime_in_G": "NOT_RUN",
            "B1_private_and_builder_history": "NOT_ACCESSED",
        },
        "missing_inputs": [r["id"] for r in lab["pending"]],
        "C04_integration": read(
            g_commit, "docs/standards-lab-evidence/c04_integration.json"
        ),
        "H1_reference": read(g_commit, "docs/standards-lab-evidence/h1_reference.json"),
        "non_claims": [
            "A positives depend on synthetic exhaustive-index and party/control/scope/time premises.",
            "C03: six partial and three unevaluated scenarios; execution/effect all UNOBSERVED. Decision-receipts -04 is a separate assessment.",
            "E: 48 requirement-route cells and 80 scenario-route observations are separate; SER Ed25519/COSE/SCITT NOT_EVALUATED.",
            "C04: F1/F2/F4 exit 2, other seven exit 0; 13 tests, 33 exact outputs. F10 consumption NOT_EVALUATED; no runtime/effect or new bug/ambiguity.",
            "H1: NO_GO_ON_AVAILABLE_EVIDENCE, zero proposed/normative changes, no patch; B3-dependent gate not complete.",
            "D is author-side regression; F is a same-user-controlled local demo, not SCITT compatibility/conformance.",
            "B1 is preparation; B2/B3 enforced isolation NOT_ESTABLISHED. H2 is unpublished and informative only.",
            "No independent third-party validation, full IETF conformance, adoption, endorsement, same-version external AIREP interop, event truth, population completeness or safety certification.",
        ],
        "hold_scopes": [
            "Whole-program completion",
            "All external messages and Internet-Draft submissions",
            "D/F and H2 publication through U1",
            "Cross-repository and Zenodo writes",
        ],
        "external_actions": {
            k: False
            for k in [
                "push_any_remote",
                "pull_request_or_issue",
                "release_or_hosting",
                "email_list_comment",
                "internet_draft_submission",
                "new_tasks_started",
                "new_automations",
            ]
        },
        "publication_precondition": "Explicit approval of the concrete unit, destination, exact commit/hash and validation. READY_FOR_USER_REVIEW and SEND-CANDIDATE grant no approval.",
    }
    (ROOT / "docs/publication_review.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "G_commit": g_commit,
                "G_files": len(g_files),
                "U1_files": len(u1_files),
                "I_commit": i_commit,
                "approval_granted": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--g-commit", required=True)
    parser.add_argument("--i-commit")
    args = parser.parse_args()
    seal(args.g_commit, args.i_commit)
