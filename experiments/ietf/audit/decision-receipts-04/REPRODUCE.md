# Reproduce the -04 follow-up

From the isolated repository root:

```sh
bash experiments/ietf/audit/decision-receipts-04/reproduce.sh
```

Absolute command on the original machine:

```sh
bash /home/toygar/Documents/ChatGPT/AACDE/standards-reentry/2026-11-02/c-audit-decision-receipts/phionyx-research/experiments/ietf/audit/decision-receipts-04/reproduce.sh
```

The script sets `PYTHONDONTWRITEBYTECODE=1` and reuses the existing -03 venv
read-only when present. It never installs into or writes bytecode in that venv.
In a fresh checkout without it, the script creates a venv only under -04 and
installs the exact hash-locked dependencies. It reads the old wheel cache if
available; otherwise it downloads the locked wheels from PyPI. No source pin or
draft revision is refreshed during reproduction.

The lock is for CPython 3.12 / Linux x86_64 compatible with the pinned wheels;
the measured interpreter is 3.12.3. The complete repository checkout, including
the frozen -03 fixtures at base `02a44a812699f853ea65fffa21320e7cc8ddb6c7`, is
required. This avoids copying or modifying the old generator.

The command checks dependencies and all 56 tracked old files, runs 13 tests,
generates the new fixtures and results, then byte-compares every output with
`cases/`. Tests run the new generator/CLI in two separate processes. The CLI's
own JSON excludes process-local origin tokens, so this follow-up applies no
output normalization. All new output is under -04 `.reproduced/`.

F1–F10 are formed from the -04 definitions using the unchanged A.3 base payloads.
Generic public DSSE signing is intentional: F1 and F2 are signed negative
fixtures that a high-level producer validator could refuse to emit. No upstream
package code is patched. Expected draft results are author-specified metadata;
the runner executes only the real receipt CLI. F10 c1 is serialized and hashed,
never used as a fake runtime store.

To exercise a fresh -04 venv without modifying the -03 environment:

```sh
PROBE_USE_NEW_VENV=1 bash experiments/ietf/audit/decision-receipts-04/reproduce.sh
```

On the original machine, verify all 3,054 prior files, including ignored local
environments, cache and outputs, against the before-run snapshot:

```sh
PYTHONDONTWRITEBYTECODE=1 experiments/ietf/audit/decision-receipts-03/.venv/bin/python \
  experiments/ietf/audit/decision-receipts-04/check_frozen.py --all-local
```

That all-local check is intentionally separate: a fresh checkout lacks the old
ignored files. The default reproduction always checks the 56 committed files.
The original-run test logs and preservation checks are under `evidence/`.

Branch: `codex/audit-decision-receipts-probe`. Fixed base:
`02a44a812699f853ea65fffa21320e7cc8ddb6c7`. To identify the result commit:

```sh
git log -1 --format=%H -- experiments/ietf/audit/decision-receipts-04
```

The script performs no git mutation or external write. Fixture command strings
remain inert bytes, and the IETF test keys are never used for real receipts.
