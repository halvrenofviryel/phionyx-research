# Standards Lab

Local, non-normative experiments with explicit evidence boundaries. This review package
contains **4 reproduced experiments (A/C03/C04/E)**, **2 completed result references (D/F)**,
**1 sealed preparation package (B1)**, **1 separate editorial candidate (H2)**,
**1 completed scoped review reference (H1)** and **2 pending results (B2/B3)**.
Counts and artifact digests are in [standards_lab.json](standards_lab.json);
[G replay records](standards-lab-evidence/replay_results.json) support the three replay
claims; the [C04 replay](standards-lab-evidence/c04_replay.json) separately supports the fourth. These are internal runs, not independent third-party validation, a population
success rate, IETF conformance or endorsement. Pending work contributes no success.

**U1 was published in [PR #107](https://github.com/halvrenofviryel/phionyx-research/pull/107).**
The [publication status](PUBLICATION_STATUS.md) records its approval scope and points
to the live merge state. The [publication review](PUBLICATION_REVIEW.md) and JSON
manifests retain their pre-publication state; their `approval_granted=false` and
`UNPUBLISHED` values are historical. Original source commit IDs remain provenance;
the integration commits are included in the published U1 history. U2/U3/U4 remain HOLD.

**Local next-publication candidate, 3 November 2026:** K1 and the K2/D/K3/K5
packet are staged together behind the bounded
[Control evidence research](CONTROL_EVIDENCE_RESEARCH.md) entry page. This
candidate is unpublished and adds no external validation, adoption or standards
status. Its [prepublication review](PREPUBLICATION_REVIEW_2026-11-03.md) is a
separate record; the historical `standards_lab.json` and U1 evidence remain
unchanged.

## K1, K2, K3 and K5: local next-publication candidate

| ID | Local evidence | Current boundary |
|---|---|---|
| **K1** | 24-case synthetic comparison, 12-case first holdout, frozen evaluator/scorer and one-command replay | Shared unsupported holdout subset: naive ACK 16/18, bounded evaluator 0/18; bounded recall 31/31; condition agreement 52/54. The naive rule is deliberately weak and analytical, not a product ranking. |
| **K2** | v0.2.0-beta.1 same-version reference harness, 28 tests and eight negative controls | Author-side reference behavior; native status INCOMPLETE with one NOT_EVALUATED item. No external producer or consumer supplied. |
| **K3** | Six pinned LangGraph 1.2.19 scenarios, 13 tests and raw-event-to-claim traceability | Controlled cooperative pause and local observations. No LLM, preemptive cancellation, durable resume, independent witness or production assurance. |
| **K5** | Self-contained source/dependency packet; two clean author-side runs and read-only evidence review | 172 packet inputs and 930 archived evidence files verified. External reproduction, independent implementation and adoption remain NOT_EVALUATED. |

K5 distributes the K2 and D/K3 source histories inside its Git bundle. Publishing
the packet therefore publishes those sources even without a separate AIREP PR.
The exact source refs, disclosures and excluded B2/B3/H2 units are recorded in the
prepublication review. The [external impact ledger](EXTERNAL_IMPACT_LEDGER.md)
keeps earlier v0.1.2 producer and v0.2 consumer evidence separate from these new
author-side results.

## Reproduce the integrated experiments

Run each command from the root of this `halvrenofviryel/phionyx-research` checkout.
Source checkout files and original first-run outputs are preserved; G replay records
are separate. [123 frozen files](standards-lab-evidence/frozen_inputs.json) were compared
byte-for-byte with the supplied S0/A/C/E source worktrees. Digests establish local
integrity, not independent custody or chronology.

| ID / purpose | Exact target and evidence class | Observed result | Boundary and evidence |
|---|---|---|---|
| **A — completeness appraisal**: distinguish valid supplied records from an appraised completeness basis | [verifier-evidence-03](https://www.ietf.org/archive/id/draft-he-agentproto-verifier-evidence-03.txt); internally developed from published text without linked implementation inspection, per original methodology | 12 synthetic vectors: **2 SATISFIED, 1 UNSATISFIED, 8 INDETERMINATE, 1 NOT_EVALUATED**; 59 tests; byte-identical replay | The two positives require a **stipulated finite exhaustive counterparty index and synthetic authority, party control/input-selection, scope and time facts**. No authenticated external basis, real-population completeness, event truth, full draft or EXR-1/CMP-2 exercise conformance. [Results/non-claims](../experiments/ietf/agentproto/verifier-evidence-03/RESULTS.md), [machine results](../experiments/ietf/agentproto/verifier-evidence-03/results.json), [method/reproduction](../experiments/ietf/agentproto/verifier-evidence-03/REPRODUCE.md). |
| **C — receipt boundaries**: distinguish receipt verification from consumption, execution and effect | [decision-receipts-03](https://www.ietf.org/archive/id/draft-gruszka-audit-decision-receipts-03.txt), SER-04 P1 and released `proofbundle==6.4.0`, commit `699545521ec5ef479bb84e61fe7461fc79ed558c`; internal probe of an external release | 9 scenarios: **6 PARTIALLY_EVALUATED, 3 NOT_EVALUATED**; 7 CLI vectors; 16 tests; 20 byte-identical artifacts | **All execution/effect observations UNOBSERVED**; consumption and §3.5 set-audit axes NOT_EVALUATED. No runtime scenario executed. `execution_proven` reflects digest presence; supplied sequence bounds do not establish population completeness. No replay bug, end-to-end authorization, preview behavior or full draft conformance inferred. [Results/non-claims](../experiments/ietf/audit/decision-receipts-03/RESULTS.md), [axis matrix](../experiments/ietf/audit/decision-receipts-03/cases/scenario_results.json), [method/reproduction](../experiments/ietf/audit/decision-receipts-03/REPRODUCE.md). |
| **C04 — -04 addendum**: measure the published F1–F10 CLI vectors and field-rule controls | [decision-receipts-04](https://www.ietf.org/archive/id/draft-gruszka-audit-decision-receipts-04.txt), same released `proofbundle==6.4.0`; internal probe | **F1/F2/F4 exit 2; the other 7 exit 0.** Four negative controls exit 2; two positive controls exit 0. **13 tests**, **33 byte-identical outputs**, no normalization | Draft expectations are separate from actual CLI results. **F10 consumption NOT_EVALUATED**, runtime execution NOT_EVALUATED, effects UNOBSERVED. Missing command inputs explain the already documented coverage boundary. No new bug or technical ambiguity; **NO_OUTREACH_NOW / HOLD**. [Results](../experiments/ietf/audit/decision-receipts-04/RESULTS.md), [machine results](../experiments/ietf/audit/decision-receipts-04/cases/results.json), [reproduction](../experiments/ietf/audit/decision-receipts-04/REPRODUCE.md). |
| **E — claim preservation**: track distinctions across SER, DSSE, digest-only and digest-resolved routes | [CP-00](https://www.ietf.org/archive/id/draft-abak-ai-evaluation-claim-preservation-00.txt), [SER-04](https://www.ietf.org/archive/id/draft-gruszka-signed-evaluation-receipts-04.txt), [mappings-04](https://www.ietf.org/archive/id/draft-gruszka-evaluation-receipt-mappings-04.txt); author-side semantic experiment. [EQR-05](https://www.ietf.org/archive/id/draft-watts-eqr-conformance-05.txt) is context only | **48 requirement×route cells:** 17 PRESERVED / 10 QUALIFIED_LOSS / 17 UNESTABLISHED / 4 NOT_APPLICABLE. Separately, **80 scenario×route observations:** 34 / 17 / 13 / 16 in that order. 30 tests; frozen JSON and Markdown reproduce byte-for-byte | These are bounded questions, not full requirements: PRESERVED is not full CP/SER conformance and NOT_APPLICABLE is not success. **SER Ed25519/selected-key, COSE and SCITT verification NOT_EVALUATED.** Local HMAC probes are separate. No independent interoperability, event truth, model safety or complete populations. [Results/non-claims](../experiments/ietf/claim-preservation/ser04/RESULTS.md), [machine results](../experiments/ietf/claim-preservation/ser04/results.json), [method/reproduction](../experiments/ietf/claim-preservation/ser04/README.md). |

```sh
python3 experiments/ietf/agentproto/verifier-evidence-03/reproduce.py
```

A needs Python 3.10+ and pytest; its evaluator is standard-library only and replay is offline.

```sh
bash experiments/ietf/audit/decision-receipts-03/reproduce.sh
```

C needs CPython 3.12, venv/pip and Linux x86_64 compatible locked wheels. It uses an
existing local wheel cache or downloads hash-locked PyPI artifacts in a fresh checkout.
G installed the five verified cached wheels into its own isolated venv. The only
normalization is the process-local `verified_origin` reporting token, after policy
evaluation; the [original capture](../experiments/ietf/audit/decision-receipts-03/evidence/api_results.original.json)
and first reproduction failure remain in the frozen [run record](../experiments/ietf/audit/decision-receipts-03/run_record.json).
Successful replay does not add unobserved runtime axes.

**Revision update, 2026-11-02T17:36Z:** the coordinator reported decision-receipts
**-04**. G fetched the [exact -04 text](standards-lab-evidence/sources/draft-gruszka-audit-decision-receipts-04.txt)
and verified SHA-256 `f5065d91493fb15a4995f85ffd1a71911d01bc9c8b063b1938521e1bfc05c826`.
C remains a frozen **-03-specific** result, not an assessment of the current revision.
The coordinator reports additions in §3.8 and Appendix A.5; author-reported vector
coverage is not our measurement. The separate **C04 addendum is now COMPLETE_LOCAL**. Its original commit is
`ecaff138be0fd833848b6f27267e555e6b31e7f6`, integrated without file changes as
`23f6b9dea1da6d229ce0acf646822d23d3f5c497`. G verified all 55 committed files and
reproduced **13 tests and 33 outputs byte-for-byte**, without normalization.
The 56 frozen C03 files remain unchanged. **AUDIT outreach remains
NO_OUTREACH_NOW / HOLD** because the reproduced boundary was already described
and no new bug or technical question was found. The
[historical discovery record](standards-lab-evidence/audit04_discovery.json) retains
its then-pending status; [integration inventory](standards-lab-evidence/c04_integration.json)
and [G replay](standards-lab-evidence/c04_replay.json) give the completed follow-up.

```sh
bash experiments/ietf/audit/decision-receipts-04/reproduce.sh
```

C04 uses the frozen C03 file-hash ledger rather than requiring its original Git
object at runtime. G reused its own local C03 venv read-only; no new network
source lookup or fresh-venv reproduction was performed by G.

```sh
python3 experiments/ietf/claim-preservation/ser04/src/run.py --check
```

E needs Python 3.10+ and the standard library; no external service is needed. The
[fixture provenance](../experiments/ietf/claim-preservation/ser04/SOURCE_PINS.json)
pins proofbundle fixture commit `a339424e07fd58fa261d8ca3f41af5de4dcbf751`.
Reconstructing 66 equal receipt byte strings does not mean proofbundle or the 66 SER
verification verdicts were run; neither was executed in E.

## Provenance and source/run digests

Preparation base: `275b871349721a8c917691d457c4a6270fe1028f`, branch
`codex/standards-lab-consolidation`. The clean starting tree, successful fetch and
unchanged HEAD are recorded in [initial state](standards-lab-evidence/initial_state.json).
The enclosing G commit is obtained with `git log -1 --format=%H -- docs/STANDARDS_LAB.md`;
it is separate from the experiment and integration commits below.

| Input | Original experiment commit (local provenance) | Integration commit (published in U1) | Source and original run record |
|---|---|---|---|
| S0 source audit, not an implementation experiment | `31f9b7e7cab5a1b556aa1ebab0dc29617e01e5c1` | `5478e8b107552468e440d9f709c18fd780502293` | [baseline](../research/standards-reentry/2026-11-02/baseline.json) |
| A | `e0ac30203e39949bb52d612eb3496c39ccb85651` | `95139b50ddd6263f7845537879250eca3994a77d` | [source manifest](../experiments/ietf/agentproto/verifier-evidence-03/sources/manifest.json), [run record](../experiments/ietf/agentproto/verifier-evidence-03/run_record.json) |
| C | `02a44a812699f853ea65fffa21320e7cc8ddb6c7` | `36b1214b72acafd784dcbd7b17cc6d2eb3de93dc` | [source manifest](../experiments/ietf/audit/decision-receipts-03/sources/manifest.json), [run record](../experiments/ietf/audit/decision-receipts-03/run_record.json) |
| C04 | `ecaff138be0fd833848b6f27267e555e6b31e7f6` | `23f6b9dea1da6d229ce0acf646822d23d3f5c497` | [source manifest](../experiments/ietf/audit/decision-receipts-04/sources/manifest.json), [original run](../experiments/ietf/audit/decision-receipts-04/run_record.json), [G replay](standards-lab-evidence/c04_replay.json) |
| E | `9f928980b3027d9dd892dfe297af98635fcd3c18` | `275b871349721a8c917691d457c4a6270fe1028f` | [source pins](../experiments/ietf/claim-preservation/ser04/SOURCE_PINS.json), [run record](../experiments/ietf/claim-preservation/ser04/run_record.json) |

[standards_lab.json](standards_lab.json) records SHA-256 for every linked experiment's
source manifest, original run record, report and result, plus exact source revision
URLs, raw-byte SHA-256 and UTC access times. G independently reacquired seven draft
revisions; all matched their original bytes and the fresh Datatracker snapshots
reported no newer revision for those seven families **at their recorded access times**.
The later decision-receipts -04 discovery above supersedes that earlier freshness
observation for C; it does not alter the -03 results. These are time-bounded checks: [fresh HTTP pins](standards-lab-evidence/http_sources.json),
[six repository pins](standards-lab-evidence/github_sources.json).

## D, F, B1, H1 and H2: separate local references

**D — AIREP explain CLI.** Repository `halvrenofviryel/ai-runtime-evidence-protocol`,
original commit `0130fcf8e7d70a0f9c4f977957e5de76ca8ef689`, integration commit **none**,
**UNPUBLISHED**. Local checkout:
`/home/toygar/.codex/worktrees/a4cd/ai-runtime-evidence-protocol`.
This author-side regression makes lifecycle states readable; the source basis is
public commit `075aff5610731736405951ecf3b7c4bfc3cc0f07`, implementation `0.2.0-beta.1`.
G checked exact-commit bytes of the [source record](standards-lab-evidence/local-refs/D/source-basis.json),
[validation record](standards-lab-evidence/local-refs/D/validation.json) and
[example](standards-lab-evidence/local-refs/D/EXPLAIN.md); it did **not** rerun D.
The original record reports 73 v0.2 tests, final 56/56 commands and 1,919 historical
files preserved, retaining the first sandbox failure. These are internal regressions.
Enforcement, relying-party claim evaluation and intended-target coverage remain
NOT_EVALUATED; no event truth, third-party validation or normative change is implied.

One-command reproduction **in a disposable copy of D at that exact commit**, with its
documented Python/Node dependencies:

```sh
python3 scripts/check_beta.py --out .reproduced/g-explain-check
```

**B1 — sealed ACDER-02 challenge preparation.** Repository
`halvrenofviryel/phionyx-research`, original commit
`d749ea7c1789aa0377a5e25e40d28f20cf700821` (coordinator-supplied; builder history not
inspected), integration commit **none**, **UNPUBLISHED**. Local checkout:
`/home/toygar/Documents/ChatGPT/AACDE/standards-reentry/2026-11-02/b1-acder-sealed-challenge/phionyx-research`.
The [public manifest snapshot](standards-lab-evidence/local-refs/B1/challenge_manifest.json)
lists 14 cases / 15 declared profile runs against
[ACDER-02](https://www.ietf.org/archive/id/draft-abak-agent-control-delivery-evidence-02.txt).
The [public commitment](standards-lab-evidence/local-refs/B1/commitment.json) is
`804c65c50dea4064f5e3d411c469a0089bb0ca9a061713c23793b572868193f8`.
G reads only public metadata/methodology, hashes those bytes and does not reproduce
the builder, access expected/private files, or validate the private seal.
The [methodology](standards-lab-evidence/local-refs/B1/METHODOLOGY.md) explicitly says
same-UID permissions do not establish blindness. Preparation is not a solver result,
a truth oracle, third-party independence, full draft conformance or deployment evidence.
Exact file hashes and local paths for D/B1 are in [local references](standards-lab-evidence/local_references.json).

**F — completed local claim-boundary demo, not SCITT compatibility.** Repository
`halvrenofviryel/ai-runtime-evidence-protocol`, exact commit
`84fe0aa9f29034aa6b873c0e83d689dc821bb398`, parent D
`0130fcf8e7d70a0f9c4f977957e5de76ca8ef689`, integration commit **none**,
**UNPUBLISHED**. Local checkout:
`/home/toygar/.codex/worktrees/dd94/ai-runtime-evidence-protocol`.
The [original results](standards-lab-evidence/local-refs/F/RESULTS.md) describe
three same-user-controlled synthetic scenarios against the conceptual boundaries
in RFC 9943, Measurement Capsule -01 and Agent Execution Evidence -02
([exact source pins](standards-lab-evidence/local-refs/F/SOURCE_PINS.json)).
The first two keep receiver/execution reports MISSING; composed supplied reports
satisfy selected native AIREP predicates while all three summaries stay INCOMPLETE.
**SCITT signature, registration/receipt and identity verification remain
NOT_EVALUATED.** This is not a SCITT compatibility, interoperability or conformance result.

The [original run record](standards-lab-evidence/local-refs/F/run_record.json)
reports **15 integration tests, 73 v0.2 tests and final 56/56 CI commands**,
with the earlier 47/56 sandbox outcome retained. G did not rerun those tests or the
runtime. G checked the four report/source snapshots against the exact Git commit,
the `evidence.tar.gz` SHA-256
`2f6a3457e3d17206e0e9c43a79f7026e678f0385066b8838434c0d65112180b6`,
all **138 archive members**, and the three archived JSON verification ledgers.
The [update verification inventory](standards-lab-evidence/update_references.json)
separates these checks from F's reported executions. No D/F implementation code or
archive was copied into research. To reproduce **in a disposable copy of exact F**,
with its documented Python 3.12/Node 20 bootstrap:

```sh
python3 integrations/scitt-claim-boundaries/demo.py
```

**H2 — separate CP-01 editorial candidate.** Repository
`halvrenofviryel/phionyx-research`, commit
`9e4524a1f4312c25b88af9444a7740662104b09a`, integration commit **none**,
**UNPUBLISHED; user approval required**. Local checkout:
`/home/toygar/Documents/ChatGPT/AACDE/standards-reentry/2026-11-02/h2-claim-preservation-candidate/phionyx-research`.
Its `standards/ietf/ai-evaluation-claim-preservation/candidate/01/` directory contains
candidate XML/TXT/HTML, `CP_00_TO_01.patch`, and `PARAGRAPH_EVIDENCE.json`.
The exact **26-file path/hash/commit inventory** is in
[update references](standards-lab-evidence/update_references.json).
G compared the checksum ledger, all 13 paragraph anchors, twelve normative sections
and BCP14 elements: **3 informative change groups, 0 normative changes**.
G did not rerender or rerun E; H2's renderer/test results remain attributed to H2.
No H2 files were merged or copied into G. This local candidate is not a submitted
Internet-Draft, a newly discovered normative requirement, adoption or conformance
finding; its supporting public artifact URL is still UNKNOWN.

**H1 — completed scoped ACDER-03 NO-GO review.** Exact commit
`57ab6d0f186f42f6a6788bb7b64b59bcae602424`, local checkout
`/home/toygar/Documents/ChatGPT/AACDE/standards-reentry/2026-11-02/h1-acder-evidence-gate/phionyx-research`.
The [report snapshot](standards-lab-evidence/local-refs/H1/ACDER_03_NO_GO.md)
records **NO_GO_ON_AVAILABLE_EVIDENCE: 0 proposed changes, 0 normative changes,
no patch**. It includes the actual C04 commit and bounded findings. This does not
complete the B3-dependent interoperability gate or establish that ACDER-02 is
defect-free. G checked 26 exact-commit files, 25 manifest hashes, 12 public-source
pins and eight report/run snapshots against the available frozen bytes; it copied
only five report/metadata files and did not rerun a normative review.
[Exact inventory and checks](standards-lab-evidence/h1_reference.json).

| Missing input | Status | Consequence |
|---|---|---|
| B2 isolated solver | **PENDING / NOT_EVALUATED** | No solver code/output or enforced isolation supplied; same-UID permissions are not isolation evidence. |
| B3 frozen comparison | **PENDING / NOT_EVALUATED** | No comparison supplied; B1 contributes no agreement count. |

The pending entries in [standards_lab.json](standards_lab.json) are deliberate omissions,
not failures converted to success. They do not block review of the reproduced A/C03/C04/E index.

## External evidence and publication boundaries

AIREP's existing [EXTERNAL_EVIDENCE.md at the inspected public commit](https://github.com/halvrenofviryel/ai-runtime-evidence-protocol/blob/075aff5610731736405951ecf3b7c4bfc3cc0f07/EXTERNAL_EVIDENCE.md)
requires an identified external artifact, frozen version, bounded claim and maintainer
reproduction. It remains unchanged. Its producer result targets v0.1.2 and its consumer
result targets an earlier v0.2 handoff; these cannot be added into a same-version
interoperability result. G cites that historical report without rerunning it or
upgrading its independence attestation. None of A/B1/C03/C04/D/E/F/H1/H2 qualifies as a new external
entry merely because it ran in another Codex task.

The [updated integrity record](standards-lab-evidence/update_validation.json) preserves
the earlier A/C03/E run records; those 105 tests were not repeated. The added C04
reproduction runs 13 tests and compares 33 outputs; these are separate records.

The [portfolio delta](STANDARDS_PORTFOLIO_DELTA.md) separates current documentation
from historical publications and gives exact cross-repository patch targets. No
normative Measurement Axioms or Resonatus change is justified by these bounded
results; no new semantic requirement was established. AIREP v0.1, normative schemas
and published Internet-Draft bytes are preserved.
