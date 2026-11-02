# Audit decision receipts -04: F1–F10 CLI probe

This follow-up freezes `draft-gruszka-audit-decision-receipts-04`, generates its
Appendix A.5 fixtures and measures unmodified `proofbundle==6.4.0`. It adds only
this directory; the committed -03 study and its local environment remain unchanged.

Start with [RESULTS.md](RESULTS.md), then [DELTA.md](DELTA.md) for the -03/-04
semantic comparison and [REPRODUCE.md](REPRODUCE.md) for a one-command rerun:

```sh
bash experiments/ietf/audit/decision-receipts-04/reproduce.sh
```

| Artifact | Purpose |
| --- | --- |
| [sources/manifest.json](sources/manifest.json) | Fresh exact URLs, UTC acquisition times, raw-byte SHA-256 pins |
| [run_record.json](run_record.json) | Initial status/fetch/base, package verification and test evidence |
| [probe.py](probe.py) | A.5 generator and real CLI runner; no full draft verifier or relying party |
| [cases/results.json](cases/results.json) | Separate author expectations and measured exits/stdout/stderr; exact inputs, roots and signatures |
| `cases/fixtures/`, `cases/inputs/` | Exact payloads, envelopes, approval/action/effect/consumption fixture bytes |
| [tests/test_probe04.py](tests/test_probe04.py) | Thirteen deterministic tests and four negative/two positive controls |
| [check_frozen.py](check_frozen.py) | Read-only comparison of the previous -03 tree with captured hashes |

The previous nine scenarios are not repeated. All seven original base payloads
and signatures are checked against -04 A.3. Two bases serve as positive controls
for this runner. SCITT A.4 is documented only as a source delta. No newer draft
revision is substituted for -04, and no publication or outreach is performed.

IETF vector attribution and license notification appear in `probe.py`. Original
draft notices are retained. The reused -03 source artifacts retain their recorded
notices and package license; this follow-up does not relicense them.
