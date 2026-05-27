---
name: state-grounding
description: How to ground state-fact assertions about external systems (repo visibility, deployment, PyPI, URL liveness) with authoritative checks in the same turn. Loaded when the assistant is about to write or commit a line that claims X is live / X is public / X is deployed / X has version V / branch X has commit Y. Codified 2026-05-26 after a deploy-topology drift incident.
---

# State assertions need grounding (codified 2026-05-26)

Before writing or committing any line that asserts a STATE FACT about external
systems — repo visibility, deployment method, infra status, file existence,
PyPI availability, URL liveness — run the AUTHORITATIVE check **in the same
turn**. Memory and prior context are *not* sufficient grounding.

| Phrase pattern | Required check |
|---|---|
| "X is public" / "X is private" | `gh repo view X --json visibility` |
| "X is deployed" / "X is live" | `curl -sI https://X` |
| "deploy uses Y" / "deploy via Z" | `Read` of `active_workload.md` + `project_infra_and_deployments.md` (memory hierarchy: active > most-recent > snapshot) |
| "file X exists at P" | `ls P` or `Read P` |
| "package X is on PyPI at v V" | `pip index versions X` or `curl https://pypi.org/pypi/X/json` |
| "test count is N" | re-run `pytest --collect-only` or check `CANONICAL_EVIDENCE_TABLE.md` |
| "branch X has commit Y" | `git log X --oneline \| head` |

**Memory hierarchy when claims conflict:** `active_workload.md` > most-recent
`Last verified:` date > `project_path_truth.md` / `project_repo_topology.md` >
older snapshots. If two memories disagree, the newer one wins AND the stale
memory must be updated in the same turn.

**Pre-publish checklist for any state assertion in public-facing copy
(paper, website, public mirror, X post, commit message that lands on `main`):**
- [ ] Authoritative check run this turn?
- [ ] Stale memory updated if discovered during check?
- [ ] Conditional phrasing ("if surfaced externally") avoided when artefact IS
      external?

Full rule + the 2026-05-26 incident that codified it:
`/home/toygar/.claude/projects/-mnt-data-claude-phionyx/memory/feedback_verify_state_before_asserting.md`.

A pre-`Edit|Write` hook (`tools/claude_code_mcp/check_state_claim_grounding.py`)
sniffs new content for the trigger phrases and warns if no matching grounding
tool call appears within the last 30 min. Informational mode until 2026-06-09;
strict-mode escalation after.
