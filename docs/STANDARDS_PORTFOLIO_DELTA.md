# Standards portfolio delta — 2026-11-02

This is the preparation-stage audit. Its publication and validation statements
describe the recorded snapshot; later U1 publication and the claim-lint correction
are covered by [publication status](PUBLICATION_STATUS.md) and the live PR checks.

This is a bounded documentation audit of six public repository READMEs at the recorded snapshot times,
the existing AIREP external-evidence record, two local standards landing pages and
selected public publication references. It is not an implementation audit of the
six repositories. Exact URLs, decoded Git-blob/raw-body SHA-256 values and UTC times
are in [GitHub pins](standards-lab-evidence/github_sources.json) and
[HTTP pins](standards-lab-evidence/http_sources.json). Original S0 and experiment
records were not refreshed in place. The [initial state](standards-lab-evidence/initial_state.json)
records G's fixed integration base; no rebase/reset to moving main occurred.

## Snapshot and status

| Repository | Inspected public commit | Finding at this revision |
|---|---|---|
| phionyx-research | `69bc8cfd282e9a0a45e34b1fcf6106b1ab618f9d` | Experimental runtime; no released RGE→AIREP projection. Mixed legacy/current AIREP language and unconditional signing prose need bounded corrections. [Snapshot](standards-lab-evidence/sources/phionyx-research--README.md) |
| ai-runtime-evidence-protocol | `075aff5610731736405951ecf3b7c4bfc3cc0f07` | Experimental v0.2 beta implementation; v0.1 frozen/supported. README L59–79 correctly separates historical external roles from current first-party tests. [Snapshot](standards-lab-evidence/sources/ai-runtime-evidence-protocol--README.md) |
| measurement-axioms | `ea672f3918c53ac9ad22ad72d0b0a5d70a9a59ce` | Published v1.0 doctrine, 45 numbered requirements; no implementation-conformance claim; independent reproducibility NOT_MEASURED. No stale status established in checked README. [Snapshot](standards-lab-evidence/sources/measurement-axioms--README.md) |
| phionyx-mcp-server | `7dc7f7eb1db80f465e7d438d95878ab2633983f4` | Own v0.2.2 release language; optional signing explicitly documented. AIREP introduction still generalizes the earlier decision-receipt model. [Snapshot](standards-lab-evidence/sources/phionyx-mcp-server--README.md) |
| phionyx-pipeline-mcp | `e36acd84022c3bc014e9a7083074fb5af62c276e` | Own v0.3.1 language; repeated sibling release versions and legacy AIREP description create drift points. [Snapshot](standards-lab-evidence/sources/phionyx-pipeline-mcp--README.md) |
| resonatus-ontology | `46229d179c40524f12d70d68f735205fecf4c861` | v1.1.0 optional strict profiles; v1.0.0 core/default SHACL frozen. README correctly distinguishes formal checks, 7/22 query coverage and unestablished external reuse. [Snapshot](standards-lab-evidence/sources/resonatus-ontology--README.md) |

GitHub connector discovery and exact-commit files agree with S0's public heads.
Sandbox `git ls-remote` failed DNS; its failures are retained in
[repository_heads.json](standards-lab-evidence/repository_heads.json), with successful
connector resolution in the GitHub pins. This does not imply that other branches
or unpublished work are absent.

## Actionable deltas

Line numbers below refer to the **inspected public snapshots**, not the edited G README.
There are **10 finding groups: 5 stale version/status groups (P01/P02/P03/P06/P08),
3 claim-boundary groups (P04/P05/P07), and 2 duplicate/index groups (P09/P10)**.
One group can affect multiple files. No repository-wide count of every occurrence
or every broken URL is claimed.

| ID | Exact target | Evidence and bounded action | Disposition in G |
|---|---|---|---|
| P01 | phionyx-research `standards/ietf/agent-control-delivery-evidence/README.md` L16–19, L107–109, L125–130 | Says current published baseline is `-01`; fresh [Datatracker metadata](standards-lab-evidence/sources/draft-abak-agent-control-delivery-evidence-metadata.json) and [exact -02 bytes](standards-lab-evidence/sources/draft-abak-agent-control-delivery-evidence-02.txt) show revision 02. Relabel the local -01 area as a historical archive and link -02 externally. Do not overwrite published/candidate files or rewrite historical review dispositions. | Recorded only; standards work area left unchanged under this task's bounded README/registry scope. |
| P02 | phionyx-research `README.md` L266, L381; phionyx-mcp-server `README.md` L30–34; phionyx-pipeline-mcp `README.md` L15, L185 | A generic one-decision-record description understates the four-family current model documented by AIREP README L24–27, L70–82. Scope the earlier model to v0.1/Decision and name the four current families. No maturity upgrade. | Corrected in research's AIREP section and research-links summary; other repos get the patch plan below. |
| P03 | phionyx-research `README.md` L268 | Unscoped fixed groups and Core/Verified/Trusted labels are presented as general current AIREP. AIREP README L108–112 describes the v0.2 assurance ladder separately. Replace this duplicate version-sensitive enumeration with the canonical specification/status link. | Corrected; no schema or normative class changed. |
| P04 | phionyx-research `README.md` L270 | “profile of AIREP” appears beside “projection not yet implemented”; AIREP README L229–235 explicitly distinguishes raw RGE from AIREP and requires release/version/verification evidence for a projection claim. Use “developed alongside” and retain the no-released-projection boundary. | Corrected; no claim flag strengthened. |
| P05 | phionyx-research `README.md` L11–12, L285; phionyx-pipeline-mcp `README.md` L39 | Unconditional signed-envelope narration obscures optional key provisioning. MCP README L148–156 explicitly emits UNSIGNED without a key, consistent with `portfolio.yaml` defaults. Qualify signing with configured key and avoid claiming every runtime turn is already a signed receipt. | Research introduction and MCP companion sentence corrected; pipeline wording planned only. |
| P06 | phionyx-research `portfolio.yaml` L45 | `spec_versions: ["v0.1"]` omits the v0.2 format identifier present in the inspected current AIREP README. Add only `v0.2`; do not treat the registry as a release pin or upgrade external-validation/conformance flags. | Corrected to `["v0.1", "v0.2"]`; all status/validation/relationship flags unchanged. |
| P07 | AIREP Zenodo record `20475137`, `metadata.description` | Historical metadata calls the two reference verifiers independent and calls RGE a reference implementation. The current [AIREP external-evidence record](standards-lab-evidence/sources/ai-runtime-evidence-protocol--EXTERNAL_EVIDENCE.md) distinguishes first-party stacks, external roles and no released RGE projection. Preserve archived bytes; propose a clearly dated metadata correction/erratum after separate approval. | External publication correction plan only. No Zenodo write. |
| P08 | phionyx-research `README.md` L404 | The generic AIREP link describes only v0.1, underrepresenting the current beta target. Link to AIREP's maintained implementation status while preserving frozen-version boundaries. | Corrected; no sibling release number copied into that summary. |
| P09 | phionyx-research `README.md` L272/L381; phionyx-mcp-server `README.md` L34; phionyx-pipeline-mcp `README.md` L15/L17/L185 | Repeated release/date/role prose drifts independently. Keep one canonical experimental-results entry at [Standards Lab](STANDARDS_LAB.md), retain AIREP's own status/specification and EXTERNAL_EVIDENCE as authorities for AIREP, and shorten sibling summaries. | Research duplicate reduced. Cross-repo Lab links are proposed only after an approved, accessible publication exists. |
| P10 | phionyx-research `README.md` Documentation & Research section, previously L374 onward | No compact entry point to the newly integrated, bounded A/C/E results. Add a single prominent Lab link; do not recast these internal runs as external evidence. | Added one prominent link; original experiment reports remain canonical for their measurements. |

P04's original line numbers can be checked against the stored public snapshot;
the existing claim linter has limited regex coverage and is not a semantic oracle.
The [local validation record](standards-lab-evidence/validation.json) records the
actual gate result separately from this manual audit. The full live-portfolio
linter and unrelated SDK suite were not run; G does not claim those are green.

## Publication and cross-link checks

- **ACDER:** exact public revision **02**; the local work-area README still says
  01 (P01). The versioned -00/-01 archive URLs remain historical targets, not
  evidence that those versions are current. No confirmed 404 was found among
  the successfully acquired selected sources; this was not a complete link crawl.
- **Claim Preservation:** exact public revision **00**, posted 23 September 2026.
  The [landing-page snapshot](standards-lab-evidence/sources/phionyx-research--standards--ietf--ai-evaluation-claim-preservation--README.md)
  accurately describes individual/Informational intent and no WG adoption or
  interoperability result. The historical CP-00 citation to ACDER-01 is a
  versioned citation, not a broken link to be silently upgraded.
- **References:** the freshly acquired Datatracker reference surfaces show ACDER
  with 8 rows (**7 external-author + 1 same-author CP reference**) and CP with
  **3 external-author rows**; mappings occurs in both sets, giving **9 unique
  external referring draft identities**. These are informative bibliographic
  references, not adoption, implementation, endorsement or evidence-root counts.
  The bounded row extraction and comparison to S0 are in
  [reference check](standards-lab-evidence/reference_check.json). No growth claim
  is made without a comparable older measurement.
- **AIREP paper:** the [versioned arXiv abstract](https://arxiv.org/abs/2608.21363v2)
  records revision v2 on 16 September 2026 and describes the four-family model.
  This is an author publication, not independent implementation evidence.
- **AIREP artifacts:** [Zenodo 20475137](https://zenodo.org/records/20475137)
  identifies the historical v0.1 archive; [22101986](https://zenodo.org/records/22101986)
  identifies alpha. Neither DOI is a beta artifact identifier. The beta release
  metadata was read via the [GitHub connector capture](standards-lab-evidence/release_connector.json)
  after raw REST acquisition returned 403 rate limit; its content reports a
  prerelease published 9 September 2026. The connector capture is a text snapshot,
  **not an asserted raw HTTP-body digest**. Exact-commit AIREP README bytes independently
  support the current beta status. The raw REST limitation remains UNKNOWN in the
  acquisition manifest; it is not misreported as a broken release or successful
  raw-byte retrieval.
- **Unpublished results:** A/C/E links in the Lab are working relative repository
  paths. D/B1/F/H1 are exact repository/commit/local-path references with portable
  report/metadata snapshots; H2 has an exact local artifact inventory and no files merged into G. No nonexistent GitHub result commit URL is offered as
  accessible evidence. The local D, B1, F and H1 snapshot Markdown retains its original
  context; relative links inside those copied reports are resolved in their
  original repository, not in G's snapshot folder.

## External evidence: neither overstate nor erase

AIREP's [existing methodology](standards-lab-evidence/sources/ai-runtime-evidence-protocol--EXTERNAL_EVIDENCE.md)
requires a frozen version, external artifact identity, bounded claim and
maintainer-side reproduction. Its two recorded roles are material and should
not be erased by a blanket “no external evidence” statement:

- The producer report targets **v0.1.2** (AIREP commit
  `44387bd43cc06ba656eaa7ff670be5c8e3220aca`, external commit
  `31e12be987105d2ba93ab2abe6135d9e6d5374d2`). Independence is methodology/attestation;
  first acceptance does not establish general or v0.2 interoperability.
- The consumer report targets **v0.2 handoff corpus v0.1**, package digest
  `b47f01c81577c9dc95b7d1f1fd1119c839866e182d24c251c386ad2a08b17923`.
  All frozen fields match over 18 cases, while the derived comparison remains
  **17 AGREE / 1 DISAGREE** (`CLS-XT1` expected-projection defect). Expected outcomes
  were present, so it is not expectation-blind. BSD-3-Clause covers only the
  named verifier-source deposit; no license is inferred for its other artifacts.

These are attributed historical reports, not G reruns. Different roles/versions
do not combine into one same-version interoperability claim. A/C03/C04/E are internal;
D is author-side regression; B1 is preparation; F is a completed same-user-controlled local demo with all SCITT verification
NOT_EVALUATED; B2/B3 remain pending. H2 is a separate unpublished informative
candidate, not a normative change or submission. The exact references and G
report-only checks are in [update references](standards-lab-evidence/update_references.json).
`portfolio.yaml`'s coarse `external_validation=false` defaults are retained to
avoid an unbounded validation flag. The Lab supplies scoped role/version context
rather than claiming the Boolean fully represents existing historical evidence.

## Exact cross-repository patch plan — no edits performed

Apply only in a separately authorized task after rechecking the pinned file
context. Proposed public Lab target: `halvrenofviryel/phionyx-research`,
`docs/STANDARDS_LAB.md` at a user-approved published commit; **no accessible
public target commit exists for this G package yet**.

| Repository / pinned file target | Proposed bounded edit | Guard |
|---|---|---|
| [phionyx-mcp-server README L30](https://github.com/halvrenofviryel/phionyx-mcp-server/blob/7dc7f7eb1db80f465e7d438d95878ab2633983f4/README.md#L30), L34 | Describe current four-family AIREP, scope decision-receipt description to earlier v0.1/Decision; replace repeated release details with canonical AIREP status and an approved Lab link for internal experiments. | Retain no released RGE projection and no same-beta interop; leave own package version and signing semantics unchanged. |
| [phionyx-pipeline-mcp README L15](https://github.com/halvrenofviryel/phionyx-pipeline-mcp/blob/e36acd84022c3bc014e9a7083074fb5af62c276e/README.md#L15), L17, L39, L185 | Shorten duplicate version/status narrative, qualify companion signing by key configuration, correct “is its developed alongside,” and point experimental results to the approved Lab. | Keep own v0.3.1 claim; no conformance/authorization/interoperability upgrade. |
| [AIREP README L87](https://github.com/halvrenofviryel/ai-runtime-evidence-protocol/blob/075aff5610731736405951ecf3b7c4bfc3cc0f07/README.md#L87), citation section L270 onward | If useful after approval, add a dated historical-metadata clarification near publication/citation context (P07), and a clearly internal-results Lab link near related standards work. | EXTERNAL_EVIDENCE remains unchanged; do not put internal Codex results in it. Archive bytes/frozen v0.1 and schemas stay unchanged. |
| [Measurement Axioms README L39](https://github.com/halvrenofviryel/measurement-axioms/blob/ea672f3918c53ac9ad22ad72d0b0a5d70a9a59ce/README.md#L39), L45–51, L82–90 reviewed | **No patch proposed.** Existing absence/proxy and separate measurement/enforcement/evidence axes already represent the distinctions exercised here. | G supplies no measured new semantic requirement. No normative change merely for cross-reference. |
| [Resonatus README L135](https://github.com/halvrenofviryel/resonatus-ontology/blob/46229d179c40524f12d70d68f735205fecf4c861/README.md#L135), L137–145 reviewed | **No patch proposed.** Existing formal/empirical and missing-measurement limits are consistent; no new causal/ontological requirement was measured. | Frozen core and normative profiles remain unchanged; no ceremonial Lab link or requirement added. |

The local ACDER landing-page correction (P01) and external Zenodo metadata correction
(P07) are also explicit follow-up plans, not changes made by G. No draft text,
other repository, publication record or external message was modified.

## Later decision-receipts revision discovery

At 2026-11-02T17:36Z the coordinator reported decision-receipts -04. G verified
its [exact raw bytes and supplied digest](standards-lab-evidence/audit04_discovery.json).
The earlier metadata freshness observation is historical; C03 is not a current
revision assessment. Its frozen scenarios and counts remain unchanged. C04 is a
separate completed addendum at original `ecaff138be0fd833848b6f27267e555e6b31e7f6`,
integrated as `23f6b9dea1da6d229ce0acf646822d23d3f5c497`. G reproduced 13 tests
and 33 byte-identical outputs: F1/F2/F4 exit 2, other seven exit 0, with four negative
and two positive controls. The original author expectations and measured CLI
results remain separate. F10 consumption is NOT_EVALUATED; no runtime/effect is
observed. No new bug or technical question resulted: **NO_OUTREACH_NOW / HOLD**.

H1 is now a completed scoped **NO_GO_ON_AVAILABLE_EVIDENCE** reference at
`57ab6d0f186f42f6a6788bb7b64b59bcae602424`: zero proposed/normative changes and no
patch. It does not complete the B3-dependent gate. Only report/metadata snapshots
are included; [H1 inventory](standards-lab-evidence/h1_reference.json).

The final README pass removes the duplicated phrase “hash-chained hash chain” and
qualifies the Documentation MCP bullet with signing only when a key is configured.
This matches the earlier P04 signing correction; no implementation behavior changes.
