# Standards Lab publication status

This record separates the published U1 package from its historical preparation
records. [PR #107](https://github.com/halvrenofviryel/phionyx-research/pull/107)
is the authority for the current open/draft/merged state, check results and merge
commit. Approval to merge is not itself a claim that the merge has completed.

## Recorded publication events — 2 November 2026

- The maintainer approved publication of U1 commit
  `1dc53d6ebc7f672ceaa176b06eee532e56d83a9d` to
  `codex/standards-lab-publication-candidate` and creation of a draft PR to `main`.
  That branch was pushed and PR #107 was created.
- The pre-merge review reproduced A/C03/C04/E from a fresh public clone: **118
  tests passed**. The original 259-file publication matched the approved size and
  SHA-256 inventory. The core CI passed on Python 3.10–3.13 and built the packages.
- The review identified a live-portfolio claim-lint mismatch and preparation-stage
  publication wording that needed historical labels. The maintainer explicitly
  authorized fixing both, publishing the corrections and then merging PR #107
  after successful checks. This does not authorize publication of other units.

## Approval units

| Unit | Publication and authorization scope |
|---|---|
| U1 — S0/A/C03/C04/E + Standards Lab | Published in PR #107; the two review corrections and merge are authorized. Consult the live PR for completion and the final commit. |
| U2 — outreach | HOLD; no messages sent or newly authorized. |
| U3 — AIREP D/F implementation | HOLD; only the attributed report snapshots are included in U1. |
| U4 — H2 CP-01 candidate | HOLD; no draft submission or candidate publication authorized. |

B2/B3 remain pending. No private answer reveal, release, hosting, external outreach
or Internet-Draft submission is authorized by the U1 merge instruction.

## Historical evidence and review corrections

[publication_review.json](publication_review.json),
[standards_lab.json](standards_lab.json) and the original experiment/evidence
records retain the state observed during preparation. Their false approval flags,
`UNPUBLISHED` labels and zero external actions are historical values. The
[original publication review](PUBLICATION_REVIEW.md) and
[original PR draft](PUBLICATION_PR_DRAFT.md) are explicitly labeled accordingly.

`verify_review.py` verifies the sealed JSON and original metadata bytes against
the published snapshot commit above. Current explanatory prose may change without
rewriting that evidence. `verify_index.py` also checks the current document links.

The AIREP registry exception covers the literal README heading “What has actually
been independently reproduced?”. It introduces version- and role-bounded results
in [AIREP EXTERNAL_EVIDENCE.md](https://github.com/halvrenofviryel/ai-runtime-evidence-protocol/blob/075aff5610731736405951ecf3b7c4bfc3cc0f07/EXTERNAL_EVIDENCE.md).
It does not enable `external_validation` or assert whole-protocol validation,
same-version v0.2 interoperability, conformance, adoption or endorsement. Other
independent-validation claims remain subject to the existing gate.

The 118 experiment tests were run separately during review; the existing core CI
does not automatically run those suites. C03 uses its documented post-evaluation
normalization of process-local origin tokens; C04 reproduces without normalization.

## Local next-publication candidate — 3 November 2026

K1 plus the K2/D/K3/K5 self-service packet have been combined in a local
prepublication branch with a bounded landing page, initial external-impact ledger,
disclosure review and PR draft. The candidate is **UNPUBLISHED** and requires a new,
explicit owner approval. It does not modify the historical U1 approval or authorize
U2/U3/U4, B2/B3, H2, outreach, release or Internet-Draft submission. See
[the current prepublication review](PREPUBLICATION_REVIEW_2026-11-03.md).
