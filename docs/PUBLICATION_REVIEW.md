# Publication review — local approval units

**READY_FOR_USER_REVIEW; `approval_granted=false`; UNPUBLISHED.** The first proposed
publication is the bounded phionyx-research **S0/A/C03/C04/E + Standards Lab** package.
C04 is integrated and reproduced; H1 is a scoped NO-GO reference. B2/B3
remain HOLD because enforced isolation and comparison results are absent.

The exact content commit, parent chain, file sizes and SHA-256 inventory are in
[publication_review.json](publication_review.json). Its enclosing metadata commit
is resolved with `git log -1 --format=%H -- docs/publication_review.json` rather than
self-embedded. This review does not grant or request publication approval.

## Separate approval units

| Unit | Concrete scope and destination | Review recommendation | Publication state |
|---|---|---|---|
| **U1 — research Lab** | `halvrenofviryel/phionyx-research`: unchanged S0/A/C03/E prerequisites; Lab index and evidence; bounded root README and portfolio corrections; verified 55-file C04 addendum | READY_FOR_USER_REVIEW; first scoped publication candidate | HOLD until explicit approval of exact content and destination |
| **U2 — I outreach** | Separate local branch `codex/standards-lab-outreach-review`; each proposed message has its own file, destination, digest, evidence and non-claims | Three drafts prepared after the G freeze; exact separate I commit and file hashes are inventoried | HOLD; no public result URL or send approval. AUDIT is NO_OUTREACH_NOW: C04 adds no new bug or technical question |
| **U3 — AIREP D/F** | `halvrenofviryel/ai-runtime-evidence-protocol`; D `0130fcf8e7d70a0f9c4f977957e5de76ca8ef689`, F `84fe0aa9f29034aa6b873c0e83d689dc821bb398`, exact 7/20 changed-file inventories | READY_FOR_USER_REVIEW as a separate implementation candidate | HOLD outside U1; no D/F code copied into research |
| **U4 — H2 CP-01** | Separate candidate at `9e4524a1f4312c25b88af9444a7740662104b09a`; 26 files including XML/TXT/HTML/patch/paragraph map | READY_FOR_USER_REVIEW as a separate unpublished ID candidate | HOLD for separate ID approval; no H2 files merged or submitted |

The final I review commit is `234107060379375607acda06b42a2ebb342247e7`:
three message bodies of **132 / 134 / 139 words**, with at most one technical
question each. AgentProto and the public E note are editorial SEND-CANDIDATE;
all delivery is HOLD. AUDIT is NO_OUTREACH_NOW / HOLD. SCITT and GitHub issue
messages were not drafted because no new substantive question or defect exists.
The I matrix and all nine files are separately hashed in U2; no public result URL
or remote draft is asserted.

The first publication branch must contain **no I outreach files or I commit in its
ancestry**. Use the exact U1 commit and parent inventory, never an arbitrary current
HEAD. D/F report snapshots in Lab are attributed references; U3 implementation
publication is a separate decision. H1 is a separate completed scoped NO-GO reference at
`57ab6d0f186f42f6a6788bb7b64b59bcae602424`; zero proposed/normative changes and no
patch. Its B3-dependent interoperability gate is not complete.

## Human-readable change review

| Area | Before | After |
|---|---|---|
| Lab references | F missing; no H2 inventory | F completed same-user-controlled local demo, all SCITT axes NOT_EVALUATED; H2 separate informative candidate with exact artifact inventory |
| Revision freshness | Earlier acquisition found decision-receipts -03 | Later coordinator observation and exact -04 byte/hash check recorded; frozen C03 remains revision-specific; C04 reproduced, AUDIT NO_OUTREACH_NOW / HOLD |
| Missing work | B2/B3/F pending | B2/B3 still absent with enforced isolation NOT_ESTABLISHED; C04 complete and H1 scoped NO-GO; F no longer pending |
| C04 addendum | No -04 implementation result | Original `ecaff138be0fd833848b6f27267e555e6b31e7f6` integrated as `23f6b9dea1da6d229ce0acf646822d23d3f5c497`; 13 tests and 33 exact outputs in G |
| G index/evidence | Original A/C/E replay and D/B1 references | Updated generator, offline checks, F archive ledger inspection, H2 XML/paragraph checks; original experiment bytes and logs retained |
| Initial README/registry changes | Generic/legacy AIREP and signing descriptions | One Lab link; bounded AIREP/RGE/signing descriptions; only `v0.2` added to portfolio format versions; final duplicate “hash chain” wording and Documentation signing qualification aligned |
| Publication scope | One general local documentation review | Four separately inventoried approval units; first U1 scope excludes outreach ancestry and D/F/H2 implementations |

Review commands from this clone:

A local [PR title and exact multiline body](PUBLICATION_PR_DRAFT.md) is supplied
for review; no PR exists. The JSON holds the content hash; the final response
identifies the enclosing metadata commit.

```sh
git diff --stat 69bc8cfd282e9a0a45e34b1fcf6106b1ab618f9d <U1_CONTENT_COMMIT>
git diff ef35030b823c37bc373e0718ace59c394dad2944 <U1_CONTENT_COMMIT> -- docs/STANDARDS_LAB.md docs/standards-lab-evidence/build_index.py
python3 -B docs/standards-lab-evidence/verify_index.py
python3 -B docs/standards-lab-evidence/verify_review.py
```

The default review command checks U1 and explicitly reports U2 as METADATA_ONLY.
Only the coordination clone's `--with-local-approval-units` mode reads I Git
objects and checks their ancestry. A U1-only checkout does not require I objects
or the non-ancestor original C04 commit. Source references remain metadata there.

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

[C04 replay](standards-lab-evidence/c04_replay.json) adds **13 passing tests** and
**33 byte-identical outputs with no normalization**. F1/F2/F4 exit 2, the other
seven exit 0; four negative controls exit 2 and two positive controls exit 0.
F10 consumption remains NOT_EVALUATED, runtime execution NOT_EVALUATED and effects
UNOBSERVED. No new defect or technical question was found. All 55 imported files
match the original C04 commit; all 56 C03 tracked files remain unchanged.

[H1 inspection](standards-lab-evidence/h1_reference.json) checks 26 committed files,
25 manifest hashes, 12 source pins and eight report/run snapshots. Only five
report/metadata snapshots are copied. This confirms the attributed NO-GO review's
integrity; G does not claim an independent normative review.

A's positive results depend on stipulated exhaustive-index and synthetic party/control,
scope and time premises. C03 has six partial and three unevaluated scenarios, with
all execution/effect axes **UNOBSERVED**. E keeps its 48 requirement×route cells
separate from 80 scenario×route observations; SER Ed25519/COSE/SCITT verification is
NOT_EVALUATED. B1 private answers and builder history were not accessed. Same-UID
permissions do not establish B2 blindness or an independent evidence root.

No independent third-party validation, full IETF conformance, adoption, endorsement,
event truth, actual-population completeness or safety certification is established.
No push, PR/issue, release/hosting, external message, submission, new task or automation
was performed. Every approval flag remains false.
