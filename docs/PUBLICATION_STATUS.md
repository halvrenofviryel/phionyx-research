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

In this historical U1 record, B2/B3 remained pending. They were subsequently
completed locally; their reveal and log-bearing publication unit still requires a
separate decision. No private answer reveal, release, hosting, external outreach
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

## Public PR #108 — merged — 3 November 2026

The owner approved the exact K1 plus K2/D/K3/K5 unit and its disclosures for a
public branch and pull request. Initial public head
`a10a2fc83cf2d9a075d7ff26d67b50205c0bb174` was pushed to
`codex/prepublication-k1-k5`, and
[PR #108](https://github.com/halvrenofviryel/phionyx-research/pull/108) was opened
against `main` as a draft. After the merge-preparation fixes and successful CI,
the PR was marked ready for review and merged at `2026-11-03T19:47:05Z`.
Merge commit
[`54682cfd312dc8c7935e926539811cfc29ea6568`](https://github.com/halvrenofviryel/phionyx-research/commit/54682cfd312dc8c7935e926539811cfc29ea6568)
has the previous public `main` and exact reviewed head
`7010b6d699f82a8719ed1d7269f5bfdb07089238` as parents. The merge-triggered CI,
claim-language gate and research-artifact integrity workflow all passed. The live
PR is the authority for the event and checks.

The public merge does not establish external reproduction, adoption, standards
endorsement or any stronger technical claim. It does not authorize the separate
B2/B3 publication unit, H2 submission, outreach or release. The
[prepublication review](PREPUBLICATION_REVIEW_2026-11-03.md) is retained as the
historical approval snapshot; its pre-merge flags are not current lifecycle
state. Dedicated release/DOI and external communication remain separate gates.
