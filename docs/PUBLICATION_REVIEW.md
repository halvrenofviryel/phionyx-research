# Publication review — local approval units

**READY_FOR_USER_REVIEW; `approval_granted=false`; UNPUBLISHED.** The first proposed
publication is the bounded phionyx-research S0/A/C03/E + Standards Lab package,
with C04 added only after its separate result is supplied and verified. B2/B3
remain HOLD because enforced isolation and comparison results are absent.

The exact content commit, parent chain, file sizes and SHA-256 inventory are in
[publication_review.json](publication_review.json). Its enclosing metadata commit
is resolved with `git log -1 --format=%H -- docs/publication_review.json` rather than
self-embedded. This review does not grant or request publication approval.

## Separate approval units

| Unit | Concrete scope and destination | Review recommendation | Publication state |
|---|---|---|---|
| **U1 — research Lab** | `halvrenofviryel/phionyx-research`: unchanged S0/A/C03/E prerequisites; Lab index and evidence; bounded root README and portfolio corrections; separately verified C04 addendum when supplied | READY_FOR_USER_REVIEW; first scoped publication candidate | HOLD until explicit approval of exact content and destination |
| **U2 — I outreach** | Separate local branch `codex/standards-lab-outreach-review`; each proposed message has its own file, destination, digest, evidence and non-claims | Draft preparation follows the G freeze; final inventory identifies its separate commit | HOLD; no public result URL or send approval. AUDIT additionally awaits C04 |
| **U3 — AIREP D/F** | `halvrenofviryel/ai-runtime-evidence-protocol`; D `0130fcf8e7d70a0f9c4f977957e5de76ca8ef689`, F `84fe0aa9f29034aa6b873c0e83d689dc821bb398`, exact 7/20 changed-file inventories | READY_FOR_USER_REVIEW as a separate implementation candidate | HOLD outside U1; no D/F code copied into research |
| **U4 — H2 CP-01** | Separate candidate at `9e4524a1f4312c25b88af9444a7740662104b09a`; 26 files including XML/TXT/HTML/patch/paragraph map | READY_FOR_USER_REVIEW as a separate unpublished ID candidate | HOLD for separate ID approval; no H2 files merged or submitted |

The first publication branch must contain **no I outreach files or I commit in its
ancestry**. Use the exact U1 commit and parent inventory, never an arbitrary current
HEAD. D/F report snapshots in Lab are attributed references; U3 implementation
publication is a separate decision. H1 is a separate pending source/result reference;
the coordinator's provisional scoped NO-GO is not a completed G measurement.

## Human-readable change review

| Area | Before | After |
|---|---|---|
| Lab references | F missing; no H2 inventory | F completed same-user-controlled local demo, all SCITT axes NOT_EVALUATED; H2 separate informative candidate with exact artifact inventory |
| Revision freshness | Earlier acquisition found decision-receipts -03 | Later coordinator observation and exact -04 byte/hash check recorded; frozen C03 is explicitly revision-specific; C04 pending, AUDIT HOLD |
| Missing work | B2/B3/F pending | B2/B3 still absent with enforced isolation NOT_ESTABLISHED; C04 and H1 awaiting separate results; F no longer pending |
| G index/evidence | Original A/C/E replay and D/B1 references | Updated generator, offline checks, F archive ledger inspection, H2 XML/paragraph checks; original experiment bytes and logs retained |
| Initial README/registry changes | Generic/legacy AIREP and signing descriptions | One Lab link; bounded AIREP/RGE/signing descriptions; only `v0.2` added to portfolio format versions |
| Publication scope | One general local documentation review | Four separately inventoried approval units; first U1 scope excludes outreach ancestry and D/F/H2 implementations |

Review commands from this clone:

```sh
git diff --stat 69bc8cfd282e9a0a45e34b1fcf6106b1ab618f9d <U1_CONTENT_COMMIT>
git diff ef35030b823c37bc373e0718ace59c394dad2944 <U1_CONTENT_COMMIT> -- docs/STANDARDS_LAB.md docs/standards-lab-evidence/build_index.py
python3 -B docs/standards-lab-evidence/verify_index.py
```

Replace the explicit commit placeholder from the JSON; it is not a public artifact
URL. Exact prerequisite original/integration commits are retained in the Lab and JSON.

## Validation and limits

The original [replay record](standards-lab-evidence/replay_results.json) retains
**A 59 + C03 16 + E 30 = 105 passing tests** and byte-identical outputs. Those suites
were not redundantly rerun for this documentation update. The
[update checks](standards-lab-evidence/update_validation.json) verify the generated
index, source/run digests, local links, pending states and **123 unchanged frozen
S0/A/C/E files**. Authored whitespace checks pass; immutable source whitespace is
retained with its original [record](standards-lab-evidence/whitespace_check.json).

[Exact F/H2 inspection](standards-lab-evidence/update_references.json) verifies F's
20 committed files and all 138 archive-member hashes, including three archived
scenario ledgers. F reports 15 integration tests, 73 v0.2 tests and final 56/56 beta
commands; **G did not rerun those tests**. SCITT signature, registration and identity
verification remain **NOT_EVALUATED**. H2's 26 files and 13 paragraph anchors match;
12 normative sections and BCP14 elements are unchanged: **three informative groups,
zero normative changes**. G did not rerender H2 or copy its candidate files.

A positive results depend on stipulated exhaustive-index and synthetic party/control,
scope and time premises. C03 has six partial and three unevaluated scenarios, with
all execution/effect axes **UNOBSERVED**. E keeps its 48 requirement×route cells
separate from 80 scenario×route observations; SER Ed25519/COSE/SCITT verification is
NOT_EVALUATED. B1 private answers and builder history were not accessed. Same-UID
permissions do not establish B2 blindness or an independent evidence root.

No independent third-party validation, full IETF conformance, adoption, endorsement,
event truth, actual-population completeness or safety certification is established.
No push, PR/issue, release/hosting, external message, submission, new task or automation
was performed. Every approval flag remains false.
