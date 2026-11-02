"""Verify exact Git inventories and separation of the local approval units."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def check(with_local_approval_units=False):
    review = json.loads((ROOT / "docs/publication_review.json").read_text())
    assert review["approval_granted"] is False
    assert review["publication_status"] == "UNPUBLISHED"
    assert not any(review["external_actions"].values())
    units = review["approval_units"]
    assert all(u["approval_granted"] is False for u in units.values())
    u1 = units["U1_research_lab"]
    content = u1["commit"]
    assert content == review["reviewed_content_commit"]
    assert git("rev-parse", content + "^").decode().strip() == u1["parent"]
    assert git("rev-parse", content + "^{tree}").decode().strip() == u1["tree"]
    assert (
        git(
            "rev-list",
            "--reverse",
            review["public_source_base_commit"] + ".." + content,
        )
        .decode()
        .splitlines()
        == u1["commits_since_public_base"]
    )
    checked = {}
    inventories = [("U1", u1["files"])]
    if with_local_approval_units:
        inventories.append(("U2", units["U2_outreach"]["files"]))
    else:
        checked["U2"] = "METADATA_ONLY; local I commit bytes not checked"
    for name, rows in inventories:
        assert len({r["path"] for r in rows}) == len(rows)
        for row in rows:
            data = git("show", row["commit"] + ":" + row["path"])
            assert hashlib.sha256(data).hexdigest() == row["sha256"], row["path"]
            assert len(data) == row["bytes"]
        checked[name] = len(rows)
    actual_paths = set(
        git("diff", "--name-only", review["public_source_base_commit"], content)
        .decode()
        .splitlines()
    )
    review_paths = {
        "docs/PUBLICATION_REVIEW.md",
        "docs/publication_review.json",
        "docs/PUBLICATION_PR_DRAFT.md",
    }
    assert {r["path"] for r in u1["files"]} == actual_paths - review_paths
    assert all(r["commit"] == content for r in u1["files"])
    for commit in u1["commits_since_public_base"]:
        paths = git("ls-tree", "-r", "--name-only", commit).decode().splitlines()
        assert not any(p.startswith("docs/outreach/") for p in paths), commit
        assert not any(
            p.startswith("integrations/scitt-claim-boundaries/") for p in paths
        )
        assert not any(
            p.startswith(
                "standards/ietf/ai-evaluation-claim-preservation/candidate/01/"
            )
            for p in paths
        )
    u2 = units["U2_outreach"]
    if u2["commit"] and with_local_approval_units:
        assert (
            subprocess.run(
                ["git", "merge-base", "--is-ancestor", u2["commit"], content], cwd=ROOT
            ).returncode
            == 1
        )
        assert u2["not_ancestor_of_U1"] is True
        assert all(r["path"].startswith("docs/outreach/2026-11/") for r in u2["files"])
        manifest = json.loads(
            git("show", u2["commit"] + ":docs/outreach/2026-11/outreach_manifest.json")
        )
        assert manifest["approval_granted"] is False
        for entry in manifest["entries"]:
            assert entry["delivery_recommendation"] == "HOLD" and not entry["sent"]
            if entry["file"]:
                data = git("show", u2["commit"] + ":" + entry["path"])
                assert hashlib.sha256(data).hexdigest() == entry["sha256"]
                body = data.decode().split("## Message\n\n", 1)[1]
                assert 100 <= len(body.split()) <= 180 and body.count("?") <= 1
                assert "<PUBLIC_ARTIFACT_URL_REQUIRED_BEFORE_SEND>" in body
    for row in review["review_metadata_files"]:
        assert (
            hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest()
            == row["sha256"]
        )
    validation = review["validation"]
    assert (
        hashlib.sha256(git("show", content + ":" + validation["record"])).hexdigest()
        == validation["sha256"]
    )
    update = json.loads(
        git("show", content + ":docs/standards-lab-evidence/update_references.json")
    )
    assert units["U3_AIREP_D_F"]["D_files"] == update["D"]["artifacts"]
    assert units["U3_AIREP_D_F"]["F_files"] == update["F"]["artifacts"]
    assert units["U4_H2_CP01"]["files"] == update["H2"]["artifacts"]
    return {
        "status": "PASS",
        "content_commit": content,
        "inventoried_git_files_checked": checked,
        "U1_commits_without_outreach_DF_code_or_H2_candidate": len(
            u1["commits_since_public_base"]
        ),
        "U2_not_ancestor_of_U1": True
        if u2["commit"] and with_local_approval_units
        else "NOT_CHECKED_LOCAL_ONLY",
        "approval_granted": False,
        "external_actions": 0,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--with-local-approval-units",
        action="store_true",
        help="Additionally inspect local-only I commit bytes and ancestry; not required for a U1-only checkout",
    )
    args = parser.parse_args()
    print(json.dumps(check(args.with_local_approval_units), indent=2))
