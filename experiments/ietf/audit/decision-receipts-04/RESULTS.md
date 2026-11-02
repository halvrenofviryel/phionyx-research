# Results: exact -04 F1–F10 against released proofbundle 6.4.0

**Measured CLI exits are F1=2, F2=2, F3=0, F4=2, F5=0, F6=0, F7=0, F8=0,
F9=0, F10=0.** These reproduce the author's reported three rejections and seven
acceptances. Thirteen tests pass. Four additional negative controls exit 2,
and two positive controls exit 0. Separate processes produce identical output
bytes without report normalization.

The draft's expected rejection and the actual CLI result are separate fields in
[cases/results.json](cases/results.json). This experiment does not execute a
complete implementation of the draft procedure. In particular, **F10 consumption
enforcement is NOT_EVALUATED**: the released receipt CLI has no such hook. No
local array lookup is reported as enforcement, and acceptance is not classified
as a new bug or a violation by a purported full draft verifier.

```sh
bash experiments/ietf/audit/decision-receipts-04/reproduce.sh
```

## Exact pins

| Input | Pin |
| --- | --- |
| [Primary -04 draft](https://www.ietf.org/archive/id/draft-gruszka-audit-decision-receipts-04.txt) | SHA-256 `f5065d91493fb15a4995f85ffd1a71911d01bc9c8b063b1938521e1bfc05c826` |
| [Comparison -03 draft](https://www.ietf.org/archive/id/draft-gruszka-audit-decision-receipts-03.txt) | SHA-256 `c0aae84b82108a3bd40cbbbee33df13c760b5c2e943a205e9efca4c623438245` |
| [Released package](https://pypi.org/project/proofbundle/6.4.0/) | `proofbundle==6.4.0`; wheel SHA-256 `72153d160c2f78647095f029c0946dbfd64a15e006a233a5abc78a3071eebf94` |
| Local base / frozen -03 result | `02a44a812699f853ea65fffa21320e7cc8ddb6c7` |
| Runtime | CPython 3.12.3; exact transitive versions and wheel hashes in `requirements.lock` |

[Source manifest](sources/manifest.json) gives the independently measured UTC
access times and exact URLs. [Package pin](evidence/package-pin.json) records
the reused isolated interpreter and all 80 installed Python module hashes, each
matching the unmodified wheel. The wheel was rehashed against fresh versioned
PyPI metadata. Existing -03 files were not edited.

## Ten measured vectors

All ten signatures verify under the expected public test key. The eight new
payload lengths, roots and signatures exactly match -04 A.5. F4 and F5 preserve
the frozen V1-good/V2-good envelope bytes unchanged. The ap2 and c1 bytes match
their published lengths and SHA-256 values. Each record includes expected input
filenames/hashes, exact CLI arguments, raw stdout/stderr and exit code.

| Vector | Author-specified first failing check | Actual exit | Measured scope |
| --- | --- | ---: | --- |
| F1 | §3.2 step 7: agent=null | 2 | Signature valid; object constraint rejected |
| F2 | §3.2 step 7: non-Z validFrom | 2 | Signature valid; timestamp field rejected |
| F3 | §3.2 step 8: expected gate-1 versus claimed gate-2 | 0 | Command verifies the pinned key but supplies no decision-maker identity policy |
| F4 | §3.2 step 9: T=expiresAt | 2 | Strict expiry boundary rejected |
| F5 | §3.2 step 10: supplied a1 versus receipt's a2 digest | 0 | Command supplies no action bytes |
| F6 | §3.4 step 5: wrong expected executor | 0 | Outcome command checks inequality with maker ID, not expected executor identity |
| F7 | §3.4 step 6: effect bytes supplied, effectDigest absent | 0 | Command supplies no effect bytes; refused is itself an allowed outcome status |
| F8 | §3.4 step 7: performedAt before decidedAt | 0 | Command receives a decision root, not the complete decision/time context |
| F9 | §3.3 Case 1: expiresAt exceeds ap.validUntil | 0 | Receipt expiry passes; command receives no approval record and does not check its earlier expiry |
| F10 | §4 relying-party refusal after receipt verification passes | 0 | Receipt CLI acceptance measured; consumption enforcement NOT_EVALUATED |

F7's stated procedure is §3.4 with e3 as supplied effect bytes, so absence of
effectDigest is the stated failure even though status is refused. F9's
expiresAt/validUntil inconsistency exists independently of the chosen T; at
09:16 the approval is also expired while the receipt remains fresh. These are
the draft's explicit distinctions, not unexplained acceptance anomalies.

## New field-rule controls

| Control | Result |
| --- | --- |
| Duplicate top-level payload member, identical values | CLI exit 2; duplicate JSON key error |
| Duplicate nested signature keyid member, identical values | CLI exit 2; duplicate JSON key error |
| Signed rawInputsIncluded="false" | CLI exit 2; valid signature, boolean type rejected |
| Signed rawInputsIncluded=0 | CLI exit 2; valid signature, boolean type rejected |
| Unchanged V1-good and V3-good | CLI exit 0 for both positive controls |

Duplicate envelopes reach the CLI as raw bytes; they are not pre-parsed by the
harness. This matters because parsing into a dict would discard the duplicated
name. Tests also verify the seven unchanged A.3 base payloads/signatures, source
pins, installed package hashes and preservation of the old study.

## Limits and ambiguity assessment

No unresolved ambiguity affecting these ten vector definitions was found in
the acquired -04 text. No technical question is proposed from these results.
The missing command inputs explain a scope difference already stated in A.5.
`ok=True` and exit 0 do not implement every expected-input or consumption check.
No full §3.8 conformance claim follows from four negative controls.

No relying party, approval store, live execution, effect observer, Agent Guard
preview, SCITT/COSE verifier or transparency service was run. A.4 is source/delta
only. There are no claims of once-only execution, genuine human approval,
operational independence, event truth or population completeness. Internal test
results are not independent third-party evidence. The -03 nine-scenario study
was not rerun or rewritten. No newer revision was substituted, and no public
push, PR, issue, message, email or submission was made.
