# K5 self-service packet validation

**LOCAL_PACKAGE_CHECKS_COMPLETED.** The final packet was reproduced using only
its bundled source/dependencies and caller-provided system runtimes, in a fresh
Linux bubblewrap sandbox with no network or host home mount. This is an
AUTHOR_SIDE_REFERENCE validation, not external reproduction or interoperability.
Publication/outreach was not performed. External evidence is NOT_EVALUATED.

The measured implementation commit is
`bec6b34c55d5a1f3e898997475539c9d54c91580`, based on fetched public main
`652e008d18805a1c69492a688e621df91f143287`. This report is committed separately;
it does not change the tested packet. Final packet MANIFEST.json SHA-256:
`6fcd887d4fbc72d2ccbb7426dc85f2e24eafbfaa853f895f8a085711b6bf6fdc`.

| Check | Actual result |
|---|---|
| K5 boundary/template tests | 8/8, no skips |
| Frozen K2 harness | 28/28, no skips |
| Frozen K3 runtime | 13/13, no skips |
| K2 reference producer/consumer and Node parity | Completed; native INCOMPLETE, 37 SATISFIED + 1 NOT_EVALUATED |
| K2 negative controls | Eight bounded reference controls met; no external adapter supplied |
| K3 actual file steps | normal 4; pre-start stop 0; in-action stop 1; unreachable receiver 4; ignored stop 4; disabled effect observer null |
| K3 cleanup | All six workers exited; none alive or forcibly terminated |
| Fresh D explain vs saved runtime view | Exact JSON equality |
| D stronger claims in all six views | enforcement_observed and relying_party_claim_support remain null native status + explanatory NOT_EVALUATED |
| Package inputs | 172 files hash-checked; source bundle and complete dependency archives included |
| Frozen source state | K2 ea1f39a6 and K3 76ecce0b cloned from bundle; no source edits; D0130fcf8 included unchanged |

The complete host-side validation command was:

```sh
python3 -B docs/external-replication/validate_offline.py \
  --node /path/to/existing/node-20.19.6 \
  --out /tmp/k5-clean-validation-02
```

The actual mount arguments are retained in
`validation-02-sandbox-command.json`. Inside the isolated namespace, the exact
one-command self-service execution was:

```sh
/usr/bin/python3 -B /packet/run.py --experiment all --out /work/result
```

The namespace used `--unshare-all --clearenv --new-session --die-with-parent`.
Read-only inputs were `/usr`, the selected Node executable, and the standalone
packet at `/packet`. Fresh scratch was `/work`; `/tmp`, `/proc` and `/dev` were
new sandbox mounts. No parent checkout, HOME, Codex state/history, credentials,
apps or expected-answer mount was supplied. Recorded mount/PID/user/network
namespace IDs differ from the host. The probe confirms `/home`, `/root`, `/run`,
`/var`, `/etc` are absent, and only the isolated loopback interface exists.
Measured runtimes were CPython 3.12.3, Node 20.19.6, Git 2.43.0, glibc 2.39.
There was no provider/model call, dependency download or API key read during replay.

The runner cloned both complete-history source refs, created fresh environments,
installed K3 from all 46 local hash-pinned wheels, and ran K2 from the release's
unchanged 9-wheel/5-tarball offline dependencies. All 13 child command exits were
zero. Their stdout/stderr, result records, raw event bytes, lifecycle artifacts,
native reports and own hashes are preserved in the evidence archives.

`validation-01` retains the initial successful packet run at
`93f85f307400cf98a949b77732cf4d3374dd336e` (7 package tests). The only subsequent
packet change aligned two external role labels with the written checklist,
recorded technical readiness, and added its boundary test; `validation-02`
tested that final commit afresh. Neither attempt failed or was omitted.

Review the packet and all preserved evidence without executing experiments:

```sh
python3 -B reports/external-replication/review_evidence.py
```

This checks the final packet manifest, both archive inventories and all 930
archived evidence files, per-run output hashes, namespace probes, unchanged
NOT_EVALUATED claims, and both complete publication-review diff hashes.
For full replay, use START_HERE or the optional clean sandbox validator.

**Ready:** K2 and D+K3 self-service reference experiments and publication-review
materials. **Pending/not packaged:** broader K1, A/B3/C/E. F is excluded; there
is no merged AIREP candidate. K2 and D+K3 remain separate exact refs. The D+K3
review scope includes D CLI, implementation, tests and measured reports, not
only the new LangGraph adapter.

The package supports one Linux x86_64/CPython 3.12 toolchain axis. K3 measures
cooperative pause at controlled boundaries, not preemptive cancellation, an
independent observer, resumption, arbitrary race latency, two-target coverage,
or general production runtime assurance. Actual observed events and file bytes
are distinct from author-specified trust/policy inputs and expected test counts.
The full v1 K2/K3 wish-list is not retrospectively claimed complete. Owner
approval to publish the exact packet and genuine outside evidence remain open.
