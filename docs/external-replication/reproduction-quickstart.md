# One-command offline reproduction

Use the whole distributed `external-replication` directory, including `bundles/`,
`licenses/`, manifests and source pins. A copy of this directory is sufficient;
the surrounding Phionyx checkout and the author's home directories are not
required. No link to an unpublished commit is used to fetch source.

## Supported toolchain

- Linux x86_64 with glibc 2.34 or later; measured on Ubuntu 24.04/glibc 2.39.
- CPython 3.12 with `venv` and `ensurepip`; measured patch 3.12.3. The runner rejects
  another Python minor version or OS/architecture.
- Node **20.19.6** on PATH; the runner checks this exact version. Node is required
  for K2 parity and is not silently skipped.
- Git; measured 2.43.0. Exact frozen release archive hashes detect source/archive
  disagreement. Python, Git, Node, libc and the OS are caller-provided system
  prerequisites, not silently downloaded by the packet.
- Approximately 1 GB free scratch space. No GPU, Docker, API key, account, network,
  private library, expected-answer file or credential manager is required.

The packet carries 46 K3 wheels plus the frozen K2 release's nine Python wheels
and five Node tarballs. Their exact versions, hashes, embedded notices and source
provenance are in [DEPENDENCY_ARTIFACTS.json](DEPENDENCY_ARTIFACTS.json). Wheels
target the stated Linux/CPython axis; unsupported systems must not discard hash
checks and call that an identical replay.

## Commands

```sh
python3 run.py --check-package
python3 run.py --experiment k2 --out /tmp/airep-k2-rerun
python3 run.py --experiment k3 --out /tmp/airep-k3-rerun
# Or run both with a single command:
python3 run.py --experiment all --out /tmp/airep-all-rerun
```

The runner verifies packet hashes, clones the exact bundled ref, creates fresh
environments and uses only local dependency artifacts. Child processes receive a
fresh HOME/TMPDIR and an explicit environment without inherited credentials,
proxy settings, user pip/Git configuration, or user site-packages. It does not
modify the distributed packet or original frozen sources.

K2 executes 28 harness tests and the pinned beta.1 measurement with five
authenticated reports, Python/Node equality and eight negative controls. Its
reference reconciliation is still **INCOMPLETE** (37 SATISFIED and one
NOT_EVALUATED), and external roles are still not supplied. Malformed consumer
projection is ADAPTER_ERROR; an absent/null projection is NOT_COMPARABLE.

K3 executes 13 tests and six real runtime scenarios. Expected observed file
steps are normal=4, pre-start pause=0, in-action pause=1, unreachable receiver=4,
disabled handler=4; disabled effect observation remains null/MISSING. It also
checks a fresh D CLI view against the saved result. See
[K3_TRACEABILITY.md](K3_TRACEABILITY.md) for the exact claim boundary.

## Inspect the output

`run_record.json` records source pins, actual tool versions, commands, cwd, exits,
stdout/stderr hashes, experiment summaries, and every generated evidence file
hash. `run_record.sha256` covers that record. Detailed raw evidence is under
`results/k2/` and `results/k3/`; commands are under `logs/`. `work/` contains the
disposable checked-out sources and environments. Remove your chosen output
directory after inspection if you do not need it; the runner does not erase it.

The final wrapper status `LOCAL_PACKAGE_CHECKS_COMPLETED` means the bounded
reference checks completed. It does not replace native FAILURE, MISSING,
INDETERMINATE, UNKNOWN or NOT_EVALUATED with success. Failed installation,
wrong Node version, missing files, hash mismatch, nonzero command exit, missing
tests, or unexpected observations cause a nonzero runner exit and a retained
failure record where execution had started.

Fresh keys, timestamps, process IDs and LangGraph interrupt IDs vary. Compare
the documented observations and native summaries; do not expect identical whole
output-file hashes across fresh runs. Each run records its own exact bytes.

## External implementation path

After a K2 run, its source is at `OUTPUT/work/airep-k2/`. The frozen
`interop/same-version/v0.2.0-beta.1/ADAPTER_CONTRACT.md` describes optional local
producer/consumer executables and `--producer-adapter`/`--consumer-adapter`.
The new implementation may use its own language and native result format;
importing the author's verifier is not required. Run those commands with a new
output directory and preserve their logs. External adapters are explicitly
chosen programs, not sandboxed plugins. Submit source/license/toolchain and role
evidence with the blank template; do not classify local test doubles as external.

The hash-only `--check-package` mode does not run dependency or experiment code.
No command requires a historical absolute path appearing in preserved source
logs. Those locations are provenance, not replay inputs.
