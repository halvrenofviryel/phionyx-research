# G evidence records

This directory supports the [Standards Lab](../STANDARDS_LAB.md) and
[portfolio delta](../STANDARDS_PORTFOLIO_DELTA.md). It is documentation provenance,
not a new normative evidence schema.

- `initial_state.json`: fixed preparation HEAD, clean initial tree, original to
  integration mapping, fetch outcome and no-publication policy.
- `frozen_inputs.json`: 123 unchanged S0/A/C/E file hashes; original worktree
  byte comparison at collection, plus exact preparation-commit checks during validation.
- `github_sources.json`: six public heads and nine exact-commit files; connector
  base64 decoded without text normalization, Git blob SHA-1 cross-check and raw-file SHA-256.
- `http_sources.json`: seven exact draft revisions plus mutable metadata/reference
  snapshots, raw response-byte digests and access times. `http_sources.sandbox-failure.json`
  and `repository_heads.json` retain failed sandbox attempts. UNKNOWN is not success.
- `sources/`: unmodified acquired public bytes. These retain their original
  provenance and rights; placement here grants no new license. IETF draft notices
  remain intact. Repository snapshots may contain historical claims under review;
  they are evidence of what was written, not G's endorsement of those claims.
- `release_connector.json`: recovery of release-status information via the GitHub
  connector after raw REST rate limiting. This is connector text, not raw HTTP bytes.
- `local_references.json`, `local-refs/`: metadata/report snapshots only. D is tied
  to exact Git blobs; B1's commit is attributed to the coordinator and no builder
  history is read. Snapshot-internal relative paths retain their original repository
  context; the Lab supplies usable links to the copied reports.
- `replay_results.json`: G's A/C/E replay logs; original run records stay under
  each experiment. D/B1 were not executed.
- `whitespace_check.json`: source-only whitespace diagnostics retained without
  normalizing immutable raw snapshots; authored paths pass the scoped check.
- `reference_check.json`, `claim_lint.json`, `validation.json`: bounded reference-row,
  local wording and integrity checks, with explicit exclusions.

From the repository root, this default check is offline and does not rewrite the
recorded validation or any experiment output:

```sh
python3 -B docs/standards-lab-evidence/verify_index.py
```

`verify_index.py --record` explicitly updates only G's validation report.
`build_index.py` was used to generate the index from declared experiment metadata
and observed files. `acquire_sources.py` performs public HTTPS GET requests into this
G directory; it is a collection tool, **not** part of offline reproduction. Re-running
collection or index generation changes timestamps and can change snapshots/digests;
such a change requires a new review and does not amend the original experiments.

Local hashes and timestamps are inspectable custody records, not independent
time witnesses. No external evidence role or source independence is inferred from
successful hashing, parsing, tests or separate Codex tasks.
