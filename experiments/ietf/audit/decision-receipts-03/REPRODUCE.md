# Reproduce the fixed experiment

From the isolated repository root:

```sh
bash experiments/ietf/audit/decision-receipts-03/reproduce.sh
```

Or from any directory on the original machine:

```sh
bash /home/toygar/Documents/ChatGPT/AACDE/standards-reentry/2026-11-02/c-audit-decision-receipts/phionyx-research/experiments/ietf/audit/decision-receipts-03/reproduce.sh
```

The script resolves its repository location, creates/uses a local venv, installs
the hash-locked dependencies, runs `pip check` and 16 stdlib unittest tests,
regenerates API/CLI results, then byte-compares them with every recorded file in
`cases/`. The test suite additionally generates two separate result directories
in separate processes and compares them to each other. A failure exits nonzero. JSON nulls and
`NOT_EVALUATED` are preserved; successful tests do not imply successful runtime
authorization or execution.

The only report normalization replaces a non-null `verified_origin` value with
`<PROCESS_LOCAL_TOKEN:64-hex>` after every API/policy call has finished. Upstream
`errors.py` generates its HMAC key per process, and its CLI omits the token from
JSON. The initial direct API capture is preserved unchanged in
`evidence/api_results.original.json`; a test checks that its projection equals
the new output. No verdict, signature, digest, warning, null or receipt byte is
normalized. Neither the archived capture nor the projection is fed back to an
upstream policy verifier as an authenticated result. This first surfaced as a
failed cross-process reproduction and is recorded in `run_record.json`.

Prerequisites: CPython 3.12 with venv/pip, Linux x86_64 compatible with the pinned
cryptography/cffi wheels. The measured interpreter is 3.12.3. No project SDK or
development dependency installation is required. The lock records exact wheel
hashes for proofbundle, cryptography, cffi, pycparser and rfc8785; it is deliberately
platform-specific. Another platform needs a separately recorded artifact lock
and is not covered by this run.

The original local `.downloads/` contains the downloaded wheels and sdist and is
git-ignored. If that directory exists, the script installs with `--no-index` from
it; no network is needed. In a fresh checkout without that cache, it fetches
locked wheels from PyPI over HTTPS and enforces SHA-256 with `--require-hashes`.
The source manifest includes their exact artifact URLs and recorded byte hashes.
The sdist was acquired and hashed, but neither built nor installed. Immutable
draft/reference snapshots are committed; reproduction does not refresh them or
change the experiment's target revision.

To repeat installation in a fresh isolated venv while keeping the same cache:

```sh
PROBE_VENV="$PWD/experiments/ietf/audit/decision-receipts-03/.reproduced/clean-venv" \
  bash experiments/ietf/audit/decision-receipts-03/reproduce.sh
```

Generated outputs go to `.reproduced/current/`. The committed `cases/` and
`run_record.json` are never rewritten by reproduction. Initial acquisition times,
clean-tree evidence and fetch results belong to the original run.

Repository: `/home/toygar/Documents/ChatGPT/AACDE/standards-reentry/2026-11-02/c-audit-decision-receipts/phionyx-research`.
Branch: `codex/audit-decision-receipts-probe`.
Fixed base: `69bc8cfd282e9a0a45e34b1fcf6106b1ab618f9d`.
Read the result commit without a self-referential committed hash:

```sh
git log -1 --format=%H -- experiments/ietf/audit/decision-receipts-03
```

All fixture keys are public test keys. No fixture command is executed, no network
write is performed, and no git commit/push occurs in the reproduction script.
