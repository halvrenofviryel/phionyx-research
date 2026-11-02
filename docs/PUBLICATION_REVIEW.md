# Publication review — local candidate only

**Recommendation: READY_FOR_USER_REVIEW for the A/C/E Standards Lab documentation
package. `approval_granted=false`. Publication is not authorized.** The complete
B2/B3/F-dependent program remains **HOLD**; those missing results do not block
review of the bounded A/C/E index. This task does not request or record approval.

Reviewed content commit: `0d19ae374cb8348db1d062d460c010d841ad6f06` (UNPUBLISHED).

The machine-readable [publication_review.json](publication_review.json) is the exact
file/digest/commit inventory. It records the reviewed content commit separately
from the later commit carrying this review metadata. No commit hash is embedded
in its own content. The final task response supplies the enclosing review commit;
locally it is also `git log -1 --format=%H -- docs/publication_review.json`.

## Proposed destination and concrete scope

Only after a new explicit user approval of the target and exact commit: the
`halvrenofviryel/phionyx-research` GitHub repository, documentation under `docs/`,
the root `README.md` and `portfolio.yaml`, and the unchanged prerequisite S0/A/C/E
content listed below. `codex/standards-lab-consolidation` is the local review branch;
no remote branch, PR, release, website, announcement or submission is created here.
These are proposed destinations, not accessible public evidence for this package.

| Candidate content | What would become visible | Recommendation |
|---|---|---|
| [STANDARDS_LAB.md](STANDARDS_LAB.md), [standards_lab.json](standards_lab.json) | Three reproducible local experiments, original/integration provenance, source/run digests, D/B1 references and honest pending states | READY_FOR_USER_REVIEW |
| [STANDARDS_PORTFOLIO_DELTA.md](STANDARDS_PORTFOLIO_DELTA.md) | Six-repository audit, 10 finding groups, scoped publication checks and exact cross-repository patch plans | READY_FOR_USER_REVIEW; plans do not authorize those edits |
| [README.md](../README.md), [portfolio.yaml](../portfolio.yaml) | One prominent Lab link; bounded AIREP/RGE/version/signing corrections; v0.2 format identifier added with no stronger validation flag | READY_FOR_USER_REVIEW |
| [standards-lab-evidence/](standards-lab-evidence/) | Raw public-source snapshots and retrieval limitations, byte-preservation inventory, A/C/E replay logs, metadata-only D/B1 snapshots, reproducible index/integrity helpers | READY_FOR_USER_REVIEW; retains original source notices, no relicensing inferred |
| [PUBLICATION_REVIEW.md](PUBLICATION_REVIEW.md), [publication_review.json](publication_review.json) | Review scope, exact content commit, hashes, non-claims and missing inputs | READY_FOR_USER_REVIEW; approval remains false |
| B2/B3/F results, a combined interop or whole-program success claim | No completed frozen inputs available | HOLD |
| D implementation and B1 full solver/builder package | Not integrated here; only explicitly attributed public metadata snapshots are in G | HOLD for any publication through this G package; requires separate concrete review |
| Cross-repository/Zenodo patches, I-stage communications, IETF draft changes | Plans only; no candidate outbound message required | HOLD; outside this task |

Prerequisite unpublished integration commits (already present before G) are
`5478e8b107552468e440d9f709c18fd780502293` (S0),
`95139b50ddd6263f7845537879250eca3994a77d` (A),
`36b1214b72acafd784dcbd7b17cc6d2eb3de93dc` (C), and
`275b871349721a8c917691d457c4a6270fe1028f` (E / preparation base).
Their original experiment commits are separately recorded in the Lab. A future
publication review must include these ancestors because the new index's relative
links depend on their contents. The exact proposed committed-path inventory is in
the JSON; it excludes venvs, wheel caches, regenerated outputs and private B1 data.

## Diff and validation

G adds the index, delta, review and supporting provenance files. The root README
adds one Lab entry and narrows outdated/unconditional claims without rewriting
the project narrative. The registry only adds `v0.2` to format identifiers. No
runtime implementation, original experiment artifact, published draft, normative
schema, frozen AIREP v0.1 content or AIREP EXTERNAL_EVIDENCE entry is changed.

[Validation](standards-lab-evidence/validation.json) and
[replay logs](standards-lab-evidence/replay_results.json) record:

- A: **59 tests**, 12 vectors, frozen output byte-identical.
- C: **16 tests**, hash-locked offline install, 7 CLI vectors and **20 byte-identical
  artifacts**. These are API/CLI observations, not executed runtime scenarios.
- E: **30 tests**, JSON/Markdown outputs match, 48 requirement×route cells and
  80 scenario×route observations remain separate.
- 123 S0/A/C/E frozen files match both the preparation-base bytes and source
  worktree comparison; source/run-record hashes, pending states and local links
  are mechanically checked. The existing local claim-lint self-test and research
  README check pass. This is **105 experiment tests**, not a full SDK or portfolio CI pass.

The full staged whitespace check reports only unchanged raw-source formatting
([record](standards-lab-evidence/whitespace_check.json)); authored-path whitespace
checks pass. Raw source bytes were preserved rather than normalized.

D is report/commit-byte inspection only, not a G rerun. B1 public metadata is
hashed only; private expected results, builder history and full tests are not
accessed. The full live-portfolio lint, unrelated runtime suites and full external
implementations were not run. One raw GitHub release-metadata GET returned 403;
connector text confirmed the release status but is not claimed as raw HTTP bytes.

## Claims that must travel with any approved publication

A's positive verdicts depend on synthetic exhaustive-index and party-control
premises. C has 6 partial and 3 unevaluated scenarios; **every execution/effect
axis is UNOBSERVED**. E's matrix judgments are bounded semantic observations;
SER cryptographic/COSE/SCITT verification is **NOT_EVALUATED**. D is first-party
regression, B1 is preparation, and B2/B3/F are **PENDING**. No internal Codex run
is third-party independent evidence or IETF conformance. There is no new
same-version external AIREP producer/consumer result, complete deployment
population, event-truth proof, safety certification, WG adoption or endorsement.

No push to any remote, PR/issue, release/hosting, email/list/comment or
Internet-Draft submission occurred. A subsequent approval must identify the exact
content, destination, commit and validation state; this document grants none.
