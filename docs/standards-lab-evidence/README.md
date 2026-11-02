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
  each experiment. D/B1/F were not executed by G; the update retains those prior A/C/E logs.
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

## F/H2 update

`update_state.json` records the clean starting G review commit and fetch retry.
`update_references.json` records F's exact 20 changed files, 138 archive-member
hash checks and three archived JSON verification ledgers, plus H2's exact 26-file
inventory, 13 paragraph mappings and unchanged twelve normative sections/BCP14
elements. Only four F report/source snapshots are copied; no D/F code, archive
or H2 candidate files are copied. Source worktrees remain read-only.

`collect_update_refs.py` performs those read-only artifact checks and updates
the local metadata when explicitly run. It does not execute F or render H2.
The updated index checker records to `update_validation.json` only with `--record`;
`validation.json` and the A/C/E replay logs retain the original G verification.
B2/B3 remain pending, with enforced isolation NOT_ESTABLISHED.

`audit04_discovery.json` records the later coordinator notification and G's
exact-byte retrieval of decision-receipts -04. The supplied SHA-256 matched.
Earlier -03 metadata remains as historical evidence; C03 outputs are unchanged.
That record is the historical discovery snapshot. The later `c04_integration.json`
verifies all 55 exact committed addendum files; `c04_replay.json` records 13 passing
tests and 33 byte-identical outputs in G, without normalization. The old 105 tests
were not rerun. F10 consumption stays NOT_EVALUATED; no runtime execution/effect.
AUDIT is NO_OUTREACH_NOW / HOLD because no new bug or technical question arose.

`h1_reference.json` and `local-refs/H1/` contain a scoped NO-GO reference, not an
ACDER patch or complete B3-dependent gate. `collect_h1_ref.py` checks 26 committed
files, 25 manifest hashes, 12 source pins and eight report snapshots, copying only
five report/metadata files. Source checkouts remain read-only.

`seal_review.py` freezes exact commit/file inventories for four approval units;
`verify_review.py` checks those Git bytes and that U1's history excludes I outreach,
D/F implementation code and H2 candidate files. I remains on its separate local
branch; its optional ignored review copies are not publication content.

The default `python3 -B docs/standards-lab-evidence/verify_review.py` checks U1 and
labels U2 METADATA_ONLY. It does not require the intentionally unpublished I Git
objects. Add `--with-local-approval-units` only in the local coordination clone to
check I raw bytes and ancestry too. `verify_index.py` compares imported C04 bytes
with the reachable integration commit, not the non-ancestor source commit.
