# Local results — 2026-11-02

**15/15 integration tests and 73/73 existing v0.2 tests passed.** The unchanged
beta check completed **56/56 commands** in an authorized local process after
the sandbox attempt failed on Node subprocess restrictions. `make demo-test`
(2 tests), `make demo` and all three integration scenarios completed successfully.
These are first-party regression results, not independent interoperability or
IETF/SCITT conformance evidence.

Base: `0130fcf8e7d70a0f9c4f977957e5de76ca8ef689` (task D).
Branch: `codex/airep-scitt-claim-boundary-demo`.
Runtime: Python 3.12.3, Node v20.19.6; cryptography 48.0.0 and jsonschema 4.25.1
from the repository's vendored, hash-checked dependency bundles.

## Observations

| Scenario | Native AIREP result | Separate, unevaluated inputs |
| --- | --- | --- |
| assumed-registered | Issuer dispatch `SATISFIED`; receiver and execution reports `MISSING`; summary `INCOMPLETE` | Valid SCITT signing/registration only a fixture premise |
| uncheckable-measurement | Identical native explain view to assumed-registered | `UNCHECKABLE`, unavailable observation and null source preserved exactly |
| composed-reports | Receiver, execution outcome, effect binding and TOCTOU predicates `SATISFIED`; summary `INCOMPLETE` | Enforcement sidecar and partial AEE projection supplied, `NOT_EVALUATED` |

Enforcement, relying-party claim support and intended-target coverage remain
`NOT_EVALUATED` in every scenario. The first two scenarios have no Execution
report and no native Effect check; no effect status is fabricated. All SCITT
signature, registration/receipt and identity verification stays `NOT_EVALUATED`.
Only AIREP test-key authentication and the local payload's raw-byte checksum are
actually checked. None establishes event truth, effect causation, authorization,
complete history or real-world observer independence.

The integration tests compare every field of text/JSON output with the existing
CLI, including qualifications and source references. Negative controls cover a
bad signature, missing bindings, a signed failed execution despite a supplied
effect, removed effect, false external verification assertions, unavailable and
unrecognized measurement states, altered payload bytes, and sidecars that cannot
fill missing AIREP stages. No test gate was weakened to obtain passing results.

## Test record and reproduction

The retained sandbox beta run passed 47/56 commands. Commands 22–26, 47, 48, 54
and 55 failed; the standalone v0.2 and `make demo` checks also encountered the
Node subprocess restriction. A minimal Node `spawnSync` probe returned `EPERM`.
The unchanged beta suite then passed 56/56 with authorized process access;
`make demo` also passed on retry. Both successful and failed logs are retained.
The new integration tests and demo passed inside the sandbox.

The successful beta run includes 124 frozen v0.1 pytest cases, 73 v0.2 tests,
19 lighteval tests and 6 hermes tests, plus existing parity, negative-proof,
schema, documentation and quickstart gates. The optional
`--with-v01-typescript` registry job was not run. The existing documented
Unicode-native directory-name branch remains `NOT MEASURED` on this Node
runtime, as reported by the unchanged interop selftest; it is not silently
counted as new coverage.

Run the demo and test commands in [README.md](README.md).
[run_record.json](run_record.json) records the baseline, exact input hashes,
source pins, command summaries, output hashes and preserved Git tree IDs.
[evidence.tar.gz](evidence.tar.gz) contains:

- `demo/`: all three full text and JSON reports;
- `validation/`: integration, standalone v0.2, presentation and demo logs,
  including the initial failures;
- `make-demo-authorized/`: the successful `make demo` retry;
- `beta-sandbox/` and `beta-authorized/`: all 56 command logs, command/exit
  manifests, source-basis manifests and parity results for each run;
- `source-discovery/`: the exact raw Datatracker metadata used to discover
  Capsule `-01` and Agent Execution Evidence `-02`.

For example, inspect the archived outputs in a new local directory:

```sh
mkdir /tmp/airep-scitt-recorded-evidence
tar -xzf integrations/scitt-claim-boundaries/evidence.tar.gz -C /tmp/airep-scitt-recorded-evidence
```

Archive entries and the archive itself have SHA-256 digests in `run_record.json`.
Only selected logs and public fixture outputs are archived; generated key files
and full standards text are excluded. Raw standards response hashes and retrieval
times are in [SOURCE_PINS.json](SOURCE_PINS.json). Future exact-URL retrieval
must compare those hashes before treating the bytes as the same source basis.

The starting checkout was clean at `075aff5610731736405951ecf3b7c4bfc3cc0f07`.
`git fetch --all --prune` succeeded, then the new branch was created directly
from D; main was not rebased or reset. The frozen v0.1 tree, all v0.2 normative
material, existing tools/tests/examples and source checkouts were preserved.
Changes are confined to this integration directory. No push, PR, issue,
release, hosting, message or Internet-Draft submission was performed.
