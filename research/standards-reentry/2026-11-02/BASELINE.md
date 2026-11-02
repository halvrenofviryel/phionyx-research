# Standards/repository baseline — 2026-11-02

## Current facts

This is the S0 source/repository audit. The observation window is **2026-11-02T16:15:38Z to 2026-11-02T16:25:44Z**; it is not a claim about the end of 2 November. **148 source artifacts** were retrieved and hashed, covering **21 required topics (17 draft families, RFC 9943, AgentProto agenda, AUDIT scheduling and important dates)**, plus reference verification and eight repository snapshots. No required source is UNAVAILABLE.

- Workspace: `/home/toygar/Documents/ChatGPT/AACDE/standards-reentry/2026-11-02/s0-baseline/phionyx-research`
- Branch: `codex/standards-baseline-20261102`
- Fixed base / initial HEAD / fetched `origin/main`: `69bc8cfd282e9a0a45e34b1fcf6106b1ab618f9d`.
- Initial `git status --short` and porcelain output: empty; worktree clean. `git fetch --all --prune`: exit 0. The base was not moved.
- Fetch deleted `origin/codex/acde-01-independent-assessment`, leaving a dangling `origin/HEAD`; it added three Dependabot branches and `origin/docs/claim-realignment`. No symbolic ref was repaired. Public API default branch is `main`.
- No applicable `AGENTS.md` was found. All git operations use this isolated clone; other clones were not modified.
- External sources and implementation code are read-only. Only `BASELINE.md`, `baseline.json`, and `SOURCE_SHA256SUMS.txt` are created in this directory. This audit performs no protocol/interop runtime tests.

All 20 inspected draft families (17 required plus three discovered through references) are currently **active individual Internet-Drafts**, not WG-adopted documents. A group label in the document header is not an adoption signal. Intended status below comes from the text; Datatracker `intended_std_level` is unset for these drafts. RFC 9943 is separately an IETF/SCITT Proposed Standard published in June 2026 ([RFC Editor metadata](https://www.rfc-editor.org/rfc/rfc9943.json)).

| Draft family | Brief expectation | Observed current | Header date | Datatracker update UTC | Intended status |
|---|---|---|---|---|---|
| `draft-abak-agent-control-delivery-evidence` | -02 | [-02](https://www.ietf.org/archive/id/draft-abak-agent-control-delivery-evidence-02.txt) | 2026-10-11 | 2026-10-11T20:19:40Z | Informational |
| `draft-abak-ai-evaluation-claim-preservation` | -00 | [-00](https://www.ietf.org/archive/id/draft-abak-ai-evaluation-claim-preservation-00.txt) | 2026-09-23 | 2026-09-23T15:55:27Z | Informational |
| `draft-agentic-ai-usecases-requirements` | -05 | [-07](https://www.ietf.org/archive/id/draft-agentic-ai-usecases-requirements-07.txt) | 2026-11-02 | 2026-11-02T14:30:36Z | Informational |
| `draft-baek-audit-absence-claims` | -00 | [-00](https://www.ietf.org/archive/id/draft-baek-audit-absence-claims-00.txt) | 2026-10-31 | 2026-10-31T08:57:57Z | Informational |
| `draft-bu-agentproto-security-principal-binding` | -08 | [-08](https://www.ietf.org/archive/id/draft-bu-agentproto-security-principal-binding-08.txt) | 2026-10-14 | 2026-10-14T02:22:47Z | Informational |
| `draft-gruszka-audit-decision-receipts` | -00 | [-03](https://www.ietf.org/archive/id/draft-gruszka-audit-decision-receipts-03.txt) | 2026-11-02 | 2026-11-02T09:01:08Z | Informational |
| `draft-gruszka-evaluation-receipt-mappings` | -04 | [-04](https://www.ietf.org/archive/id/draft-gruszka-evaluation-receipt-mappings-04.txt) | 2026-10-26 | 2026-10-26T15:11:39Z | Informational |
| `draft-gruszka-signed-evaluation-receipts` | -04 | [-04](https://www.ietf.org/archive/id/draft-gruszka-signed-evaluation-receipts-04.txt) | 2026-10-26 | 2026-10-26T15:09:51Z | Informational |
| `draft-he-agentproto-verifier-evidence` | -03 | [-03](https://www.ietf.org/archive/id/draft-he-agentproto-verifier-evidence-03.txt) | 2026-10-31 | 2026-10-31T23:16:42Z | Informational |
| `draft-kuehlewind-audit-architecture` | current; no exact revision specified | [-01](https://www.ietf.org/archive/id/draft-kuehlewind-audit-architecture-01.txt) | 2026-09-07 | 2026-09-07T11:49:34Z | Informational |
| `draft-nandakumar-agentproto-pace` | current; no exact revision specified | [-00](https://www.ietf.org/archive/id/draft-nandakumar-agentproto-pace-00.txt) | 2026-11-01 | 2026-11-01T20:40:36Z | Standards Track |
| `draft-sergeev-audit-task-requirements` | -00 | [-00](https://www.ietf.org/archive/id/draft-sergeev-audit-task-requirements-00.txt) | 2026-10-15 | 2026-10-16T06:11:55Z | Informational |
| `draft-templeman-scitt-measurement-capsule` | -01 | [-01](https://www.ietf.org/archive/id/draft-templeman-scitt-measurement-capsule-01.txt) | 2026-10-27 | 2026-10-28T05:12:04Z | Experimental |
| `draft-thaha-scitt-agent-execution-evidence` | current; no exact revision specified | [-02](https://www.ietf.org/archive/id/draft-thaha-scitt-agent-execution-evidence-02.txt) | 2026-11 | 2026-11-01T10:05:28Z | Standards Track |
| `draft-wadkins-agentproto-action-determinability` | current; no exact revision specified | [-00](https://www.ietf.org/archive/id/draft-wadkins-agentproto-action-determinability-00.txt) | 2026-09-10 | 2026-09-11T15:20:23Z | Informational |
| `draft-watts-eqr-conformance` | -05 | [-05](https://www.ietf.org/archive/id/draft-watts-eqr-conformance-05.txt) | 2026-10-30 | 2026-10-31T10:24:30Z | Experimental |
| `draft-zhang-audit-record-limits` | -00 | [-00](https://www.ietf.org/archive/id/draft-zhang-audit-record-limits-00.txt) | 2026-10-27 | 2026-10-27T13:13:18Z | Informational |

For use-cases and AUDIT decision-receipts, both the expected and actually current revisions are pinned. Architecture `-00` is included only as historical context; the brief did not specify that revision. Its current revision is `-01`. Historical ACDE `-00`/`-01` bytes are also pinned to identify the external probes accurately.

Meeting facts: AgentProto is an active WG ([group record](https://datatracker.ietf.org/api/v1/group/group/2645/)); its [agenda-127-agentproto-00](https://datatracker.ietf.org/meeting/127/materials/agenda-127-agentproto-00) names work planning, use cases/requirements and architecture/dialog discussion. The [session page](https://datatracker.ietf.org/meeting/127/session/agentproto) schedules **16 November 22:00–17 November 00:00 UTC** (14:00–16:00 PST). AUDIT is a **BoF** ([group record](https://datatracker.ietf.org/api/v1/group/group/?acronym=audit)), scheduled **17 November 17:00–18:30 UTC** (09:00–10:30 PST), according to its [session page](https://datatracker.ietf.org/meeting/127/session/audit). No AUDIT agenda document is linked there at retrieval; a scheduled session is not an approved/adopted architecture.

The [IETF 127 important dates](https://datatracker.ietf.org/meeting/127/important-dates/) list the I-D and early-registration cutoffs at **2 November 23:59 UTC** (3 November 02:59 Europe/Istanbul), draft WG agendas due **4 November**, and revised WG agendas due **9 November**, each at 23:59 UTC. No external submission is performed.

## Changes since late October

No previous audit snapshot was supplied. The comparison cutoff is explicitly **25 October 2026 23:59:59 UTC**. The following distinguish dated developments after that cutoff from corrections to brief expectations; they do not invent historical reference counts.

1. **Use-cases expected -05 versus observed -07.** The pinned -05 is dated 27 October; -07 is dated 2 November and updated at 14:30:36Z. Inspection of both texts shows linked-dialog terminology, A1-11 device continuation and B3-10 downstream cancellation/termination outcome reporting in -07, plus clearer dialog-versus-OAuth/WIMSE responsibilities. This is a comparison of the pinned texts, not a WG adoption claim. Sources: [agentic-ai-usecases-requirements-05](https://www.ietf.org/archive/id/draft-agentic-ai-usecases-requirements-05.txt), [agentic-ai-usecases-requirements-07](https://www.ietf.org/archive/id/draft-agentic-ai-usecases-requirements-07.txt).

2. **AUDIT decision receipts expected -00 versus observed -03.** The -00 header is 1 November; -03 is 2 November, updated at 09:01:08Z. Appendix B describes added SCITT composition, completeness prerequisites, key-compromise/access limits, mapping questions, timestamp anchoring and missing-outcome discussion. The architecture document is separately current at -01 (7 September), not -03. Sources: [gruszka-audit-decision-receipts-00](https://www.ietf.org/archive/id/draft-gruszka-audit-decision-receipts-00.txt), [gruszka-audit-decision-receipts-03](https://www.ietf.org/archive/id/draft-gruszka-audit-decision-receipts-03.txt), [kuehlewind-audit-architecture-01](https://www.ietf.org/archive/id/draft-kuehlewind-audit-architecture-01.txt).

3. **New and revised evidence/dialog work after the late-October cutoff.** PACE -00 and agent-execution-evidence -02 are dated/posted 1 November; verifier-evidence -03 and absence-claims -00 are dated 31 October. Record-limits -00 and measurement-capsule -01 are dated 27 October; evaluation receipts/mappings -04 are dated 26 October; EQR -05 has a 30 October header and a 31 October Datatracker update. Dates are measured separately from draft-status claims. Sources: [nandakumar-agentproto-pace-00](https://www.ietf.org/archive/id/draft-nandakumar-agentproto-pace-00.txt), [thaha-scitt-agent-execution-evidence-02](https://www.ietf.org/archive/id/draft-thaha-scitt-agent-execution-evidence-02.txt), [he-agentproto-verifier-evidence-03](https://www.ietf.org/archive/id/draft-he-agentproto-verifier-evidence-03.txt), [baek-audit-absence-claims-00](https://www.ietf.org/archive/id/draft-baek-audit-absence-claims-00.txt), [zhang-audit-record-limits-00](https://www.ietf.org/archive/id/draft-zhang-audit-record-limits-00.txt), [templeman-scitt-measurement-capsule-01](https://www.ietf.org/archive/id/draft-templeman-scitt-measurement-capsule-01.txt), [gruszka-signed-evaluation-receipts-04](https://www.ietf.org/archive/id/draft-gruszka-signed-evaluation-receipts-04.txt), [gruszka-evaluation-receipt-mappings-04](https://www.ietf.org/archive/id/draft-gruszka-evaluation-receipt-mappings-04.txt), [watts-eqr-conformance-05](https://www.ietf.org/archive/id/draft-watts-eqr-conformance-05.txt).

4. **External repositories advanced while the six portfolio default-branch heads predate late October.** Public releases include proofbundle v6.4.0 (28 October) and Cedulon v0.16.0 (26 October), then v0.17.0 (31 October). Their observed default-branch HEADs are distinct from those release tags and the dated 25 October comparison commits. The six halvrenofviryel repository HEAD dates are September or 11 October. No local checkout of those other repositories was treated as current remote truth. Sources: [b7n0de--proofbundle-releases](https://api.github.com/repos/b7n0de/proofbundle/releases?per_page=100), [b7n0de--proofbundle-head](https://api.github.com/repos/b7n0de/proofbundle/commits/main), [b7n0de--proofbundle-late-october-head](https://api.github.com/repos/b7n0de/proofbundle/commits?until=2026-10-25T23%3A59%3A59Z&per_page=1), [dogrucanemek-alt--cedulon-releases](https://api.github.com/repos/dogrucanemek-alt/cedulon/releases?per_page=100), [dogrucanemek-alt--cedulon-head](https://api.github.com/repos/dogrucanemek-alt/cedulon/commits/master), [dogrucanemek-alt--cedulon-late-october-head](https://api.github.com/repos/dogrucanemek-alt/cedulon/commits?until=2026-10-25T23%3A59%3A59Z&per_page=1).

5. **IETF 127 planning has a pinned agenda and a same-day cutoff.** AgentProto agenda -00 was updated 30 October and schedules use cases/requirements and architecture/dialog discussion on 16 November 22:00–00:00 UTC. AUDIT is a BoF, scheduled 17 November 17:00–18:30 UTC; no AUDIT agenda was linked on its session page at retrieval. The I-D cutoff is 2 November 23:59 UTC, with draft/revised WG agendas due 4/9 November. No submissions or scheduling actions are taken. Sources: [ietf127-agentproto-agenda-00](https://datatracker.ietf.org/meeting/127/materials/agenda-127-agentproto-00), [ietf127-agentproto-agenda-metadata](https://datatracker.ietf.org/api/v1/doc/document/agenda-127-agentproto/), [ietf127-agentproto](https://datatracker.ietf.org/meeting/127/session/agentproto), [ietf127-audit](https://datatracker.ietf.org/meeting/127/session/audit), [audit-group-list](https://datatracker.ietf.org/api/v1/group/group/?acronym=audit), [ietf127-dates](https://datatracker.ietf.org/meeting/127/important-dates/).

## Abak draft reference surface

Re-read the two Datatracker Referenced-by pages: **ACDE: 7 external active drafts + 1 author cross-reference**; **claim-preservation: 3 external active drafts + 0 author cross-references**. There are **9 unique external draft families** across the two surfaces; evaluation-receipt-mappings appears on both. These are measured reference relationships, not adoption, endorsement, impact or implementation counts.

| Target | Referencing current draft | Relationship | Referenced target revision |
|---|---|---|---|
| ACDE | [draft-abak-ai-evaluation-claim-preservation-00](https://www.ietf.org/archive/id/draft-abak-ai-evaluation-claim-preservation-00.txt) | author self-reference; informative | draft-abak-agent-control-delivery-evidence-01 |
| ACDE | [draft-baek-audit-absence-claims-00](https://www.ietf.org/archive/id/draft-baek-audit-absence-claims-00.txt) | external-author draft reference; informative | draft-abak-agent-control-delivery-evidence-02 |
| ACDE | [draft-dogru-cedulon-core-04](https://www.ietf.org/archive/id/draft-dogru-cedulon-core-04.txt) | external-author draft reference; informative | unversioned document URL |
| ACDE | [draft-dogru-cedulon-decision-profile-04](https://www.ietf.org/archive/id/draft-dogru-cedulon-decision-profile-04.txt) | external-author draft reference; informative | draft-abak-agent-control-delivery-evidence-01 |
| ACDE | [draft-gruszka-evaluation-receipt-mappings-04](https://www.ietf.org/archive/id/draft-gruszka-evaluation-receipt-mappings-04.txt) | external-author draft reference; informative | draft-abak-agent-control-delivery-evidence-02 |
| ACDE | [draft-sergeev-claim-boundaries-02](https://www.ietf.org/archive/id/draft-sergeev-claim-boundaries-02.txt) | external-author draft reference; informative | draft-abak-agent-control-delivery-evidence-02 |
| ACDE | [draft-wadkins-agentproto-action-determinability-00](https://www.ietf.org/archive/id/draft-wadkins-agentproto-action-determinability-00.txt) | external-author draft reference; informative | draft-abak-agent-control-delivery-evidence-01 |
| ACDE | [draft-zhang-audit-record-limits-00](https://www.ietf.org/archive/id/draft-zhang-audit-record-limits-00.txt) | external-author draft reference; informative | draft-abak-agent-control-delivery-evidence-02 |
| Claim preservation | [draft-gruszka-evaluation-receipt-mappings-04](https://www.ietf.org/archive/id/draft-gruszka-evaluation-receipt-mappings-04.txt) | external-author draft reference; informative | draft-abak-ai-evaluation-claim-preservation-00 |
| Claim preservation | [draft-gruszka-signed-evaluation-receipts-04](https://www.ietf.org/archive/id/draft-gruszka-signed-evaluation-receipts-04.txt) | external-author draft reference; informative | draft-abak-ai-evaluation-claim-preservation-00 |
| Claim preservation | [draft-watts-eqr-conformance-05](https://www.ietf.org/archive/id/draft-watts-eqr-conformance-05.txt) | external-author draft reference; informative | draft-abak-ai-evaluation-claim-preservation-00 |

Sources: [ACDE Referenced by](https://datatracker.ietf.org/doc/draft-abak-agent-control-delivery-evidence/referencedby/); [claim-preservation Referenced by](https://datatracker.ietf.org/doc/draft-abak-ai-evaluation-claim-preservation/referencedby/). Every listed target identity was checked in the fetched current draft text. The Cedulon core reference is unversioned, so its date label must not be promoted to an exact target revision. Datatracker uses heuristic extraction and excludes title-only references; this is the observed surface, not a complete citation census. “External” means different draft authorship, not demonstrated implementation independence.

## Repo maturity/status snapshot

Public default-branch HEADs were resolved through GitHub, then README and evidence files were read at exact commit URLs. Release objects, prereleases and tags are listed separately. Tag ordering below is version ordering among observed tags, not an inferred creation chronology. GitHub collections were requested with `per_page=100`; each returned fewer than 100 records. No registry publication was independently checked. Other local checkouts were not inspected or substituted for public state.

| Repository | Default branch HEAD (committer UTC) | Latest non-prerelease GitHub release | Highest observed version tag | README maturity/status |
|---|---|---|---|---|
| [b7n0de/proofbundle](https://raw.githubusercontent.com/b7n0de/proofbundle/c8b5b28519191cbe8d229cbf3378e749cb8ccc64/README.md) | `c8b5b28519191cbe8d229cbf3378e749cb8ccc64` (2026-11-02T14:56:59Z) | v6.4.0 (2026-10-28T08:59:05Z); target `699545521ec5ef479bb84e61fe7461fc79ed558c` | v6.4.0 → `699545521ec5ef479bb84e61fe7461fc79ed558c` | README describes v6.4.0 and heterogeneous profile maturity. SCITT/CCF reader and Rust verifier are experimental; decision receipt validity does not prove decision correctness, and build provenance is not an evaluation/security audit. |
| [dogrucanemek-alt/cedulon](https://raw.githubusercontent.com/dogrucanemek-alt/cedulon/6316eb7f5027a6de56cf6643f1715afe6c882aa7/README.md) | `6316eb7f5027a6de56cf6643f1715afe6c882aa7` (2026-10-31T23:50:38Z) | v0.17.0 (2026-10-31T13:26:57Z); target `85ecee2aa694008d00e7010cb53bd56830aab79d` | v0.17.0 → `85ecee2aa694008d00e7010cb53bd56830aab79d` | README describes an agent-spend audit layer above payment rails. Core demos use mock wallets/rails; the separately described live demo is read-only Base Sepolia reconciliation. Package availability does not establish production settlement maturity. |
| [halvrenofviryel/ai-runtime-evidence-protocol](https://raw.githubusercontent.com/halvrenofviryel/ai-runtime-evidence-protocol/075aff5610731736405951ecf3b7c4bfc3cc0f07/README.md) | `075aff5610731736405951ecf3b7c4bfc3cc0f07` (2026-09-23T22:48:04Z) | v0.1.2 (2026-09-23T19:03:11Z); target `44387bd43cc06ba656eaa7ff670be5c8e3220aca` | v0.2.0-beta.1 → `8a6c01ecce457aa94330c0ed7219e4c56ebfe771` | Experimental proposed format with first-party implementation; v0.2.0-beta.1 is the implementation target and is not stable. The v0.1 line remains frozen and supported; valid records do not establish event truth. |
| [halvrenofviryel/measurement-axioms](https://raw.githubusercontent.com/halvrenofviryel/measurement-axioms/ea672f3918c53ac9ad22ad72d0b0a5d70a9a59ce/README.md) | `ea672f3918c53ac9ad22ad72d0b0a5d70a9a59ce` (2026-09-13T15:10:36Z) | none in public releases collection | v1.0.0 → `d009fcb97c6ca03e962fb9c5f8ea6e21b619a1f5` | Research doctrine plus normative extract and self-audit. README makes no implementation conformance or prevalence claim; independent reproducibility is NOT_MEASURED and independent review is NOT_REQUESTED. |
| [halvrenofviryel/phionyx-mcp-server](https://raw.githubusercontent.com/halvrenofviryel/phionyx-mcp-server/7dc7f7eb1db80f465e7d438d95878ab2633983f4/README.md) | `7dc7f7eb1db80f465e7d438d95878ab2633983f4` (2026-09-12T11:22:45Z) | v0.2.0 (2026-05-30T05:34:00Z); target `d3ae678ef129fba04c250640e42f38eec5a65397` | v0.2.2 → `fdf5ba66f7b2e610b365224f681203287123faca` | README identifies v0.2.2 and reports five of eight capabilities implemented with three explicit stubs; uses RGE v0.2. A conformant RGE-to-AIREP projection is not implemented. No fresh runtime test in this audit. |
| [halvrenofviryel/phionyx-pipeline-mcp](https://raw.githubusercontent.com/halvrenofviryel/phionyx-pipeline-mcp/e36acd84022c3bc014e9a7083074fb5af62c276e/README.md) | `e36acd84022c3bc014e9a7083074fb5af62c276e` (2026-09-12T11:22:39Z) | v0.2.0 (2026-05-29T19:03:24Z); target `e9df6fb4489a248aefd1ccdbb27deb9c60fdad64` | v0.3.1 → `b8c76f42b169700cea3c6368295162bb6e81ae19` | README identifies v0.3.1 with optional, default-off evidence binding. Claim-governance gate and outward MCP server are distinct components; README does not supply a general production-maturity certification. |
| [halvrenofviryel/phionyx-research](https://raw.githubusercontent.com/halvrenofviryel/phionyx-research/69bc8cfd282e9a0a45e34b1fcf6106b1ab618f9d/README.md) | `69bc8cfd282e9a0a45e34b1fcf6106b1ab618f9d` (2026-09-23T16:44:18Z) | v0.9.1 (2026-08-10T13:01:41Z); target `b590a0023feb5fa1f1e01c070d9eaa9e35dc15f9` | v0.9.1 → `b590a0023feb5fa1f1e01c070d9eaa9e35dc15f9` | README describes an early working implementation under alignment and limits production-readiness to demos; runtime/security claims remain research-grade, benchmarks first-party. A released RGE-to-AIREP conformant projection is not implemented. |
| [halvrenofviryel/resonatus-ontology](https://raw.githubusercontent.com/halvrenofviryel/resonatus-ontology/46229d179c40524f12d70d68f735205fecf4c861/README.md) | `46229d179c40524f12d70d68f735205fecf4c861` (2026-10-11T17:06:15Z) | v1.1.0 (2026-10-11T17:07:33Z); target `46229d179c40524f12d70d68f735205fecf4c861` | v1.1.0 → `46229d179c40524f12d70d68f735205fecf4c861` | Frozen v1.0.0 core/default SHACL with additive optional v1.1 strict profiles. Structural conformance is not scientific validation; executable competency coverage is 7/22, and external reuse/real-system intervention are not established. |

AIREP additionally has **v0.2.0-beta.1**, published 9 September, marked as a prerelease, targeting `8a6c01ecce457aa94330c0ed7219e4c56ebfe771`. Its latest stable release by publication time is **v0.1.2** (23 September); the semantic-version order and publication order differ. Pipeline also has the historical **v0.3.0a1** prerelease. Source release/tag collections are separately pinned in the source table.

This audit clone begins at the public research `main` commit, while the research release `v0.9.1` points to `b590a0023feb5fa1f1e01c070d9eaa9e35dc15f9`. That release and current `main` are distinct states. A README version and an old local checkout cannot replace a remote HEAD/release lookup.

**External interop scope.** [Proofbundle interop/acde_01](https://raw.githubusercontent.com/b7n0de/proofbundle/c8b5b28519191cbe8d229cbf3378e749cb8ccc64/interop/acde_01/README.md) is an external-author verifier-side reading of **ACDE -01**, outside the proofbundle library. Its published run record identifies head `ecd2fe99e9587a565b5f4480a9084fd32644a987`, 146 derived vectors and a 130-sentence inventory classified as 108 agreement, 0 contradiction, 14 ambiguity, 8 not implemented. These are reported historical results, not newly reproduced in S0. Native cryptographic verification is outside that exercise. Its pinned -01 digest matches the independently retrieved -01 bytes (`2f0356fcb834ba6b80970721273cd8e2e0b2cc19ef1f89a0205a78991653fabf`). It does not establish a current -02 implementation.

[Cedulon interop/abak-00](https://raw.githubusercontent.com/dogrucanemek-alt/cedulon/6316eb7f5027a6de56cf6643f1715afe6c882aa7/interop/abak-00/README.md) describes a settlement-accounting example using ACDE **-00**, explicitly disclaims being an implementation, and requires published **0.8.0** packages outside its repository; a follow-up case driver uses **0.12.0**. Those package/version boundaries remain separate from current `v0.17.0`/HEAD. The historical reported gaps are not asserted to persist in current Cedulon. S0 downloads metadata/README/run-record material and does not execute either external probe.

**AIREP external evidence boundaries.** The current [EXTERNAL_EVIDENCE.md at 075aff5610731736405951ecf3b7c4bfc3cc0f07](https://raw.githubusercontent.com/halvrenofviryel/ai-runtime-evidence-protocol/075aff5610731736405951ecf3b7c4bfc3cc0f07/EXTERNAL_EVIDENCE.md) records two separate evidence classes:

- Emek Can Doğru: independently authored **producer**, frozen **v0.1.2**, AIREP commit `44387bd43cc06ba656eaa7ff670be5c8e3220aca`, external commit `31e12be987105d2ba93ab2abe6135d9e6d5374d2`. The source records acceptance by both frozen reference verifiers and maintainer reproduction. Authorship independence remains methodology/attestation; an artifact cannot prove what its author did not read.
- Joel Hillier / Certisyn: independently implemented **consumer/verifier**, frozen **v0.2 Independent-Verifier Corpus v0.1**. Package SHA-256 `b47f01c81577c9dc95b7d1f1fd1119c839866e182d24c251c386ad2a08b17923`; implementation SHA-256 `2aef1212adeaab5a1dc7f07c3f240183db97478b247c008c5fcc0e177fbfeca8`. The source records agreement on frozen fields in all 18 cases and **17 AGREE / 1 DISAGREE** on the package projection. `CLS-XT1` is documented as expected `PASS` versus observed `NOT_EVALUATED` because revocation prevented signature evaluation; this is a package expectation defect, not a permission to convert unknowns to PASS. Expected outcomes were supplied, so the run is not expected-blind.
- **No same-version independent producer↔consumer interoperability result follows.** The two versions and roles are not additive; the source says no AIREP version has both roles measured. S0 verifies the current published record and its bytes; it does not newly reproduce these implementations or independently establish the authorship histories.
- The Certisyn deposit licenses only `AIREP-verifier-source.txt` under BSD-3-Clause. The other three artifacts have no license asserted; no DOI is claimed for that deposit. Frozen AIREP v0.1 content and normative schemas remain untouched.

## Claims we must NOT make

- A signature or a hash proves that the reported event occurred or that the result is true.
- Valid supplied records establish that the complete relevant population was supplied.
- Missing, unavailable, unexercised or inconclusive evidence is PASS or FAIL.
- An individual draft, a reference, an agenda listing or an RFC composition implies adoption, endorsement, certification or implementation.
- Reference counts are an impact score or a measured increase from a prior baseline.
- First-party tests or this internal audit are independent third-party evidence.
- The AIREP v0.1.2 producer and v0.2 consumer together demonstrate same-version interoperability.
- Proofbundle interop/acde_01 implements current ACDE -02 or is part of the proofbundle library.
- Cedulon interop/abak-00 is an ACDE implementation or its historical package results describe current HEAD.
- GitHub tags, stable release objects, prereleases, README versions and package-registry availability are interchangeable.
- This source audit ran external implementations, audited their security, validated normative schemas or established production readiness.

**Unknowns and limits.** No prior reference-count snapshot, no complete citation census, no independent execution in this audit, no production-readiness/security assessment, no registry release verification, and no independent validation of author work-order attestations. The AUDIT agenda is not linked yet; scheduling can change. File-level publication dates not exposed by sources remain unknown; a HEAD committer timestamp is not a file modification timestamp. The failed `/api/v1/group/group/audit/` lookup returned 404 and was recovered through the acronym-filtered group collection. All required source topics were pinned.

**Validation result: PASS.** Strict JSON parsing, all 148 raw-byte SHA-256/length comparisons, draft metadata/reference crosschecks, URL/checksum/report consistency and the staged three-file scope check passed. `git diff --cached --check` passed. Application and external-implementation tests were not run because this is a source audit.

**Validation and reproduction.** The checks below validate JSON, unique source identities/URLs, manifest-to-report links, expected/current revisions, the measured reference counts and the restricted output set. With `S0_SOURCE_CACHE=/tmp/s0-baseline-20261102`, they additionally rehash every downloaded body. The cache is temporary and is not a fourth committed artifact. The checksum file uses `SHA256  canonical-public-URL` rows, not filesystem paths. Later remote downloads can be compared to these digests; mutable API/HTML byte drift alone is not a substantive-change verdict.

Run from the audit clone root:

```bash
python3 -c 'from pathlib import Path; p=Path("research/standards-reentry/2026-11-02/BASELINE.md"); exec(p.read_text().split("```python\n",1)[1].split("```",1)[0])'
```

```python
import collections, hashlib, json, os, pathlib, re, urllib.parse
root = pathlib.Path("research/standards-reentry/2026-11-02")
def unique_object(pairs):
    out = {}
    for key, value in pairs:
        assert key not in out, ("duplicate JSON key", key)
        out[key] = value
    return out
j = json.loads((root / "baseline.json").read_text(), object_pairs_hook=unique_object)
md = (root / "BASELINE.md").read_text()
sources = j["sources"]
by_id = {s["id"]: s for s in sources}
assert len(by_id) == len(sources)
urls = {s["canonical_url"] for s in sources}
assert len(urls) == len(sources)
manifest = {}
for line in (root / "SOURCE_SHA256SUMS.txt").read_text().splitlines():
    if not line or line.startswith("#"): continue
    digest, url = line.split("  ", 1)
    assert url not in manifest
    manifest[url] = digest
assert set(manifest) == urls
for s in sources:
    assert s["status"] == "PINNED" and s["http_status"] == 200
    assert re.fullmatch(r"[0-9a-f]{64}", s["sha256"])
    assert manifest[s["canonical_url"]] == s["sha256"]
    assert s["retrieved_at_utc"].endswith("Z")
    assert s["exact_revision"] and s["date_basis"] and s["intended_status"] and s["group_status"]
    assert "](" + s["canonical_url"] + ")" in md
    assert s["sha256"] in md
    if s.get("date_source_id"): assert s["date_source_id"] in by_id
links = re.findall(r"\]\((https://[^)]+)\)", md)
assert set(links) <= urls
assert len(j["required_source_ids"]) == 21
assert set(j["required_source_ids"]) <= set(by_id)
assert not j["unavailable_required_sources"]
assert len(j["repositories"]) == 8
for d in j["drafts"]:
    assert d["current_source_id"] in by_id
    if d["expected_revision"] is not None:
        assert d["name"] + "-" + d["expected_revision"] in by_id
    assert d["metadata_source"] in by_id and d["page_source"] in by_id
for r in j["repositories"]:
    assert re.fullmatch(r"[0-9a-f]{40}", r["remote_head"])
    assert set(r["source_ids"]) <= set(by_id)
for r in j["references"]:
    rows = r["rows"]
    assert len({x["draft"] for x in rows}) == len(rows)
    assert r["total_active_rows"] == len(rows)
    assert r["self_reference_rows"] == sum(x["relationship"] == "author self-reference" for x in rows)
    assert r["external_active_rows"] + r["self_reference_rows"] == len(rows)
    assert all(x["source_id"] in by_id for x in rows)
assert j["counts"]["retrieved_source_artifacts"] == len(sources)
assert j["counts"]["acde_active_external"] == j["references"][0]["external_active_rows"] == 7
assert j["counts"]["claim_active_external"] == j["references"][1]["external_active_rows"] == 3
assert j["counts"]["unique_external_referring_drafts"] == 9
assert j["airep_external_evidence"]["same_version_producer_consumer_interop_established"] is False
assert {p.name for p in root.iterdir()} == {"BASELINE.md", "baseline.json", "SOURCE_SHA256SUMS.txt"}
cache = os.environ.get("S0_SOURCE_CACHE")
if cache:
    for s in sources:
        raw = (pathlib.Path(cache) / (s["id"] + ".body")).read_bytes()
        assert len(raw) == s["byte_length"]
        assert hashlib.sha256(raw).hexdigest() == s["sha256"]
    for d in j["drafts"]:
        meta = json.loads((pathlib.Path(cache) / (d["metadata_source"] + ".body")).read_text())
        assert meta["name"] == d["name"] and meta["rev"] == d["current_revision"]
        text = (pathlib.Path(cache) / (d["current_source_id"] + ".body")).read_text()
        assert d["current_source_id"] in text[:2000]
    assert hashlib.sha256(pathlib.Path("README.md").read_bytes()).hexdigest() == by_id["halvrenofviryel--phionyx-research-readme"]["sha256"]
    for r in j["references"]:
        html = (pathlib.Path(cache) / (r["referencedby_source_id"] + ".body")).read_text()
        names = set(re.findall(r'href="/doc/(draft-[^"/]+)/"', html))
        assert names == {row["draft"] for row in r["rows"]}
        for row in r["rows"]:
            text = (pathlib.Path(cache) / (row["source_id"] + ".body")).read_text()
            assert r["target"] in re.sub(r"\s+", "", text)
    print("PASS: raw-byte SHA-256/size checks and reference-page/text crosschecks")
print(f"PASS: JSON, {len(sources)} source records, URL/checksum/report consistency, 21 required topics, 8 repositories, scope and claim boundaries")
```

## Source table

This table contains every successfully retrieved artifact, including supporting metadata. Exact revisions, byte counts, intended/group status, date basis and retrieval method are machine-readable in `baseline.json`; the draft and repo tables above expose the primary publication/status facts. **UNKNOWN** is a missing publication/update date, not a failed retrieval. For commit-pinned repository files, the file publication date is not inferred from HEAD.

| Source / canonical public URL | Publication/update (see date basis in JSON) | Retrieved at UTC | SHA-256 of response bytes |
|---|---|---|---|
| [acde-referencedby](https://datatracker.ietf.org/doc/draft-abak-agent-control-delivery-evidence/referencedby/) | UNKNOWN | 2026-11-02T16:16:28Z | `e0e4926ef98d2ca4702efc949921b8abca3443060f24e9ece580bd8a80fcb3d6` |
| [agentproto-group](https://datatracker.ietf.org/api/v1/group/group/2645/) | 2026-10-09T20:16:22Z | 2026-11-02T16:18:17Z | `bc668ef30dbd6ef0bb1260f3bf4391da42dd81e312912b006bb7cad45c0d1893` |
| [audit-group-list](https://datatracker.ietf.org/api/v1/group/group/?acronym=audit) | 2026-10-08T18:33:40Z | 2026-11-02T16:18:17Z | `313a238c87c7f957f128c9b1dd57c0d4fdedace8f31cd5c9e35be7c1947010e8` |
| [b7n0de--proofbundle-head](https://api.github.com/repos/b7n0de/proofbundle/commits/main) | 2026-11-02T14:56:59Z | 2026-11-02T16:16:28Z | `ee96adb238a47be3d2d7b06b55adfc262cbbd85cb3bb79c7138eab811c10b62e` |
| [b7n0de--proofbundle-interop-README.md](https://raw.githubusercontent.com/b7n0de/proofbundle/c8b5b28519191cbe8d229cbf3378e749cb8ccc64/interop/acde_01/README.md) | 2026-10-11T13:38:06Z | 2026-11-02T16:16:30Z | `a7668fadd9c338213e5504e526959f7bd86e7033a1edd997040025b7b296b4f5` |
| [b7n0de--proofbundle-interop-README.md-history](https://api.github.com/repos/b7n0de/proofbundle/commits?sha=c8b5b28519191cbe8d229cbf3378e749cb8ccc64&path=interop%2Facde_01%2FREADME.md&per_page=1) | 2026-10-11T13:38:06Z | 2026-11-02T16:25:43Z | `311852460add2e717b8ce1b35afd75902a31e685a56f8f01287fc4da4ece4169` |
| [b7n0de--proofbundle-interop-REQUIREMENTS.md](https://raw.githubusercontent.com/b7n0de/proofbundle/c8b5b28519191cbe8d229cbf3378e749cb8ccc64/interop/acde_01/REQUIREMENTS.md) | 2026-10-11T13:38:06Z | 2026-11-02T16:16:31Z | `b807697b6c9af96bd8268acd8997f4e464f7d6659b5833573d0086422410bb0c` |
| [b7n0de--proofbundle-interop-REQUIREMENTS.md-history](https://api.github.com/repos/b7n0de/proofbundle/commits?sha=c8b5b28519191cbe8d229cbf3378e749cb8ccc64&path=interop%2Facde_01%2FREQUIREMENTS.md&per_page=1) | 2026-10-11T13:38:06Z | 2026-11-02T16:25:42Z | `311852460add2e717b8ce1b35afd75902a31e685a56f8f01287fc4da4ece4169` |
| [b7n0de--proofbundle-interop-RUN_RECORD.md](https://raw.githubusercontent.com/b7n0de/proofbundle/c8b5b28519191cbe8d229cbf3378e749cb8ccc64/interop/acde_01/RUN_RECORD.md) | 2026-10-11T13:38:06Z | 2026-11-02T16:16:31Z | `0fc999dcfb53a81d1d3b0f611b10be023bbfdae87e550d842ded8379bef6dad4` |
| [b7n0de--proofbundle-interop-RUN_RECORD.md-history](https://api.github.com/repos/b7n0de/proofbundle/commits?sha=c8b5b28519191cbe8d229cbf3378e749cb8ccc64&path=interop%2Facde_01%2FRUN_RECORD.md&per_page=1) | 2026-10-11T13:38:06Z | 2026-11-02T16:25:44Z | `311852460add2e717b8ce1b35afd75902a31e685a56f8f01287fc4da4ece4169` |
| [b7n0de--proofbundle-interop-requirements.json](https://raw.githubusercontent.com/b7n0de/proofbundle/c8b5b28519191cbe8d229cbf3378e749cb8ccc64/interop/acde_01/requirements.json) | 2026-10-11T13:38:06Z | 2026-11-02T16:16:32Z | `34cfa519a324c9f8c6c821cb9d70314d50d011b6679340caec505b2adeb1b4df` |
| [b7n0de--proofbundle-interop-requirements.json-history](https://api.github.com/repos/b7n0de/proofbundle/commits?sha=c8b5b28519191cbe8d229cbf3378e749cb8ccc64&path=interop%2Facde_01%2Frequirements.json&per_page=1) | 2026-10-11T13:38:06Z | 2026-11-02T16:25:44Z | `311852460add2e717b8ce1b35afd75902a31e685a56f8f01287fc4da4ece4169` |
| [b7n0de--proofbundle-interop-requirements_map.json](https://raw.githubusercontent.com/b7n0de/proofbundle/c8b5b28519191cbe8d229cbf3378e749cb8ccc64/interop/acde_01/requirements_map.json) | 2026-10-11T13:38:06Z | 2026-11-02T16:16:32Z | `5291aa665c9d5fd03b1c6875ca853dca56ba45c26a9bb7ba45af15b30a142abc` |
| [b7n0de--proofbundle-interop-requirements_map.json-history](https://api.github.com/repos/b7n0de/proofbundle/commits?sha=c8b5b28519191cbe8d229cbf3378e749cb8ccc64&path=interop%2Facde_01%2Frequirements_map.json&per_page=1) | 2026-10-11T13:38:06Z | 2026-11-02T16:25:43Z | `311852460add2e717b8ce1b35afd75902a31e685a56f8f01287fc4da4ece4169` |
| [b7n0de--proofbundle-interop-run_record.json](https://raw.githubusercontent.com/b7n0de/proofbundle/c8b5b28519191cbe8d229cbf3378e749cb8ccc64/interop/acde_01/run_record.json) | 2026-10-11T13:38:06Z | 2026-11-02T16:16:32Z | `d223cc1683882156179c70e88114fc308c9bb80faca7c9a3d584679847a15a14` |
| [b7n0de--proofbundle-interop-run_record.json-history](https://api.github.com/repos/b7n0de/proofbundle/commits?sha=c8b5b28519191cbe8d229cbf3378e749cb8ccc64&path=interop%2Facde_01%2Frun_record.json&per_page=1) | 2026-10-11T13:38:06Z | 2026-11-02T16:25:42Z | `311852460add2e717b8ce1b35afd75902a31e685a56f8f01287fc4da4ece4169` |
| [b7n0de--proofbundle-interop-tree](https://api.github.com/repos/b7n0de/proofbundle/contents/interop/acde_01?ref=c8b5b28519191cbe8d229cbf3378e749cb8ccc64) | Mon, 02 Nov 2026 14:57:07 GMT | 2026-11-02T16:16:30Z | `d3bb13bd558b621ac7c97a730cca00d0bbb3913ead8c3be1f6228f74884845f7` |
| [b7n0de--proofbundle-late-october-head](https://api.github.com/repos/b7n0de/proofbundle/commits?until=2026-10-25T23%3A59%3A59Z&per_page=1) | Sun, 25 Oct 2026 23:44:30 GMT | 2026-11-02T16:18:19Z | `1ad25ef3556b7f504cf650591b4d9d5c7ae4acce7121b41dd3628330fe478913` |
| [b7n0de--proofbundle-metadata](https://api.github.com/repos/b7n0de/proofbundle) | 2026-11-02T14:57:07Z | 2026-11-02T16:16:27Z | `ced095e024f85b71775f2f43a6cfc8a5f7eeaf53360f35fed914f7530b12bcfc` |
| [b7n0de--proofbundle-readme](https://raw.githubusercontent.com/b7n0de/proofbundle/c8b5b28519191cbe8d229cbf3378e749cb8ccc64/README.md) | 2026-10-27T22:00:22Z | 2026-11-02T16:16:30Z | `c51f1bbdc5378ef5a8a854219f334a5644f3ad4a98c4980f34df7bc3d45d575a` |
| [b7n0de--proofbundle-readme-history](https://api.github.com/repos/b7n0de/proofbundle/commits?sha=c8b5b28519191cbe8d229cbf3378e749cb8ccc64&path=README.md&per_page=1) | 2026-10-27T22:00:22Z | 2026-11-02T16:25:43Z | `3383a98f9a944462fd6d8250410cf7b15cdd66f033b5ffa0bd1480be0b280dd0` |
| [b7n0de--proofbundle-releases](https://api.github.com/repos/b7n0de/proofbundle/releases?per_page=100) | UNKNOWN | 2026-11-02T16:16:29Z | `47d9dd80ae24c005deda4a933704e3b31a6e61ae817c2b1ba18c8462fbd8275c` |
| [b7n0de--proofbundle-tags](https://api.github.com/repos/b7n0de/proofbundle/tags?per_page=100) | Mon, 02 Nov 2026 14:57:07 GMT | 2026-11-02T16:16:28Z | `23d4527cc64f03ee4d9782e3fcf4d54013278c0342158bc31e8c71ee4df394f3` |
| [claim-referencedby](https://datatracker.ietf.org/doc/draft-abak-ai-evaluation-claim-preservation/referencedby/) | UNKNOWN | 2026-11-02T16:16:28Z | `4aedf24f0ae45e74a14d2dd71e053f53dbc2fecccc13cc9043dbf8b386b4a89a` |
| [dogrucanemek-alt--cedulon-head](https://api.github.com/repos/dogrucanemek-alt/cedulon/commits/master) | 2026-10-31T23:50:38Z | 2026-11-02T16:16:28Z | `f6c939663e61c8d1d99618afe43cdf855b88f26a5ae6845b38085ccdc316f999` |
| [dogrucanemek-alt--cedulon-interop-README.md](https://raw.githubusercontent.com/dogrucanemek-alt/cedulon/6316eb7f5027a6de56cf6643f1715afe6c882aa7/interop/abak-00/README.md) | 2026-09-03T22:43:10Z | 2026-11-02T16:16:30Z | `8dfff73122fbe84e35fa2d219a65562d8688234694985bbb933d7dbd5d9b7cb3` |
| [dogrucanemek-alt--cedulon-interop-README.md-history](https://api.github.com/repos/dogrucanemek-alt/cedulon/commits?sha=6316eb7f5027a6de56cf6643f1715afe6c882aa7&path=interop%2Fabak-00%2FREADME.md&per_page=1) | 2026-09-03T22:43:10Z | 2026-11-02T16:25:43Z | `9daf56fc31f23f81fe6bfd915698ad72c819cfd10742dcb6dfde8fe709d23d55` |
| [dogrucanemek-alt--cedulon-interop-tree](https://api.github.com/repos/dogrucanemek-alt/cedulon/contents/interop/abak-00?ref=6316eb7f5027a6de56cf6643f1715afe6c882aa7) | Sat, 31 Oct 2026 23:50:43 GMT | 2026-11-02T16:16:29Z | `af66e800e9d7bbbd28000af71c1193d05ee7f9aadddccd7c0fc48b5db9973e49` |
| [dogrucanemek-alt--cedulon-late-october-head](https://api.github.com/repos/dogrucanemek-alt/cedulon/commits?until=2026-10-25T23%3A59%3A59Z&per_page=1) | Sun, 25 Oct 2026 23:50:45 GMT | 2026-11-02T16:18:20Z | `8d6dcf2e5d059352b3d2106839351609191a441dfd8e84db5ec91f5cc34387fd` |
| [dogrucanemek-alt--cedulon-metadata](https://api.github.com/repos/dogrucanemek-alt/cedulon) | 2026-10-31T23:50:43Z | 2026-11-02T16:16:27Z | `3a49ddcb19db47dd1a12d22d5f5341093bfc3ea13874e735e6da79d7dfa3912b` |
| [dogrucanemek-alt--cedulon-readme](https://raw.githubusercontent.com/dogrucanemek-alt/cedulon/6316eb7f5027a6de56cf6643f1715afe6c882aa7/README.md) | 2026-10-12T19:41:28Z | 2026-11-02T16:16:29Z | `edd61462b08a32b615c09530c3a323f8341b8dd28e0df5b96312a4e560fdf306` |
| [dogrucanemek-alt--cedulon-readme-history](https://api.github.com/repos/dogrucanemek-alt/cedulon/commits?sha=6316eb7f5027a6de56cf6643f1715afe6c882aa7&path=README.md&per_page=1) | 2026-10-12T19:41:28Z | 2026-11-02T16:25:42Z | `9cd2b4caed004d617d1e1618c424cce2507b18787a83538f45b316829400a0e8` |
| [dogrucanemek-alt--cedulon-releases](https://api.github.com/repos/dogrucanemek-alt/cedulon/releases?per_page=100) | UNKNOWN | 2026-11-02T16:16:29Z | `247f0e0133fd58a317121c3d827b4fc60ee2fc09be46b93c4094cc92c4c2b9b0` |
| [dogrucanemek-alt--cedulon-tags](https://api.github.com/repos/dogrucanemek-alt/cedulon/tags?per_page=100) | Sat, 31 Oct 2026 23:50:43 GMT | 2026-11-02T16:16:28Z | `2da84aa0628ec483d19d0b8d1b0dc2421181007d7ed2595ae07c620d964d1314` |
| [draft-abak-agent-control-delivery-evidence-00](https://www.ietf.org/archive/id/draft-abak-agent-control-delivery-evidence-00.txt) | 2026-08-30 | 2026-11-02T16:17:26Z | `414fcae84d4b6b778068e9b9e47df56b9b56d4a523ff220599ef82c238e1e9cf` |
| [draft-abak-agent-control-delivery-evidence-01](https://www.ietf.org/archive/id/draft-abak-agent-control-delivery-evidence-01.txt) | 2026-09-04 | 2026-11-02T16:17:26Z | `2f0356fcb834ba6b80970721273cd8e2e0b2cc19ef1f89a0205a78991653fabf` |
| [draft-abak-agent-control-delivery-evidence-02](https://www.ietf.org/archive/id/draft-abak-agent-control-delivery-evidence-02.txt) | 2026-10-11 | 2026-11-02T16:15:39Z | `fe3baeb08c8e0979ca64efece098c972827fab483debe0b2bcbfd697bb714782` |
| [draft-abak-agent-control-delivery-evidence-metadata](https://datatracker.ietf.org/api/v1/doc/document/draft-abak-agent-control-delivery-evidence/) | 2026-10-11T20:19:40Z | 2026-11-02T16:15:38Z | `3d50183144ff1f1a73c81f69e7d3588ad0ebfdb31a8e93646ac9cb239db56154` |
| [draft-abak-agent-control-delivery-evidence-page](https://datatracker.ietf.org/doc/draft-abak-agent-control-delivery-evidence/) | 2026-10-11T20:19:40Z | 2026-11-02T16:15:39Z | `57781eb48f0b267e649148159b2618982fd26a61aee6b51d703f31d30490ce91` |
| [draft-abak-ai-evaluation-claim-preservation-00](https://www.ietf.org/archive/id/draft-abak-ai-evaluation-claim-preservation-00.txt) | 2026-09-23 | 2026-11-02T16:15:40Z | `9088079da04ed23fdead8a54894ac70bcf6ff26ce4834c815e4dc6961986de54` |
| [draft-abak-ai-evaluation-claim-preservation-metadata](https://datatracker.ietf.org/api/v1/doc/document/draft-abak-ai-evaluation-claim-preservation/) | 2026-09-23T15:55:27Z | 2026-11-02T16:15:38Z | `5ef1980c985c7aa433b3b711671f76ca23e6eddab9178027f8247ad631550aee` |
| [draft-abak-ai-evaluation-claim-preservation-page](https://datatracker.ietf.org/doc/draft-abak-ai-evaluation-claim-preservation/) | 2026-09-23T15:55:27Z | 2026-11-02T16:15:39Z | `c4f3bd24ea915eaec44a7ac87ff632b22cb991007f2be0ce539c1ff8135885bc` |
| [draft-agentic-ai-usecases-requirements-05](https://www.ietf.org/archive/id/draft-agentic-ai-usecases-requirements-05.txt) | 2026-10-27 | 2026-11-02T16:15:39Z | `d6071888e117657b5d2558519d1e0d991f3707daab31b8f1aab2dcd58a4eb629` |
| [draft-agentic-ai-usecases-requirements-07](https://www.ietf.org/archive/id/draft-agentic-ai-usecases-requirements-07.txt) | 2026-11-02 | 2026-11-02T16:15:40Z | `33491c0b417b155b84801687b17a3ad2f669622fa92f50cd0e39c6163735fe58` |
| [draft-agentic-ai-usecases-requirements-metadata](https://datatracker.ietf.org/api/v1/doc/document/draft-agentic-ai-usecases-requirements/) | 2026-11-02T14:30:36Z | 2026-11-02T16:15:38Z | `8b96ea843572f723d431f7861716a21a0aaa0081009835c671a24e3b999d57d7` |
| [draft-agentic-ai-usecases-requirements-page](https://datatracker.ietf.org/doc/draft-agentic-ai-usecases-requirements/) | 2026-11-02T14:30:36Z | 2026-11-02T16:15:39Z | `d044c6782325ac5643ae4ce7f5a5e4316098e42996fdc2ded915eb4470485fff` |
| [draft-baek-audit-absence-claims-00](https://www.ietf.org/archive/id/draft-baek-audit-absence-claims-00.txt) | 2026-10-31 | 2026-11-02T16:15:41Z | `69f2fb87357e4811fcbff1e2f1f805d62ff635398e107994b8a7049938fe6f65` |
| [draft-baek-audit-absence-claims-metadata](https://datatracker.ietf.org/api/v1/doc/document/draft-baek-audit-absence-claims/) | 2026-10-31T08:57:57Z | 2026-11-02T16:15:40Z | `36fb57d74b4406a9c19d475729d3a042f8948661bfe3244743fddb3513627f9b` |
| [draft-baek-audit-absence-claims-page](https://datatracker.ietf.org/doc/draft-baek-audit-absence-claims/) | 2026-10-31T08:57:57Z | 2026-11-02T16:15:40Z | `dda4994472f1c7d30397f808652ca201a39b90f6dbadd6635a00bd293c1a1206` |
| [draft-bu-agentproto-security-principal-binding-08](https://www.ietf.org/archive/id/draft-bu-agentproto-security-principal-binding-08.txt) | 2026-10-14 | 2026-11-02T16:15:40Z | `c796fc408bdfcd4498d96c0b9d3a75db1bfc0fe89c845545d9e8dc555ce73eea` |
| [draft-bu-agentproto-security-principal-binding-metadata](https://datatracker.ietf.org/api/v1/doc/document/draft-bu-agentproto-security-principal-binding/) | 2026-10-14T02:22:47Z | 2026-11-02T16:15:38Z | `31ea0fff19e447cdeda9cafd2b10f25c5a41638a9f3f0006c16ff5b392e68363` |
| [draft-bu-agentproto-security-principal-binding-page](https://datatracker.ietf.org/doc/draft-bu-agentproto-security-principal-binding/) | 2026-10-14T02:22:47Z | 2026-11-02T16:15:39Z | `c59d32d388ae2745c6b6b4b9c5f29c3d0e44e72b87db9d935e3fc1ec840383b0` |
| [draft-dogru-cedulon-core-04](https://www.ietf.org/archive/id/draft-dogru-cedulon-core-04.txt) | 2026-10-07 | 2026-11-02T16:17:24Z | `3553ea5fa4c1f568eaedaf7aec54f105a635aec5adb7eb82cf7f8932ac811309` |
| [draft-dogru-cedulon-core-metadata](https://datatracker.ietf.org/api/v1/doc/document/draft-dogru-cedulon-core/) | 2026-10-07T19:45:44Z | 2026-11-02T16:17:23Z | `9b57965c39aa0d267442b675fe6399ba502f16c7237f707897500294135cb07a` |
| [draft-dogru-cedulon-core-page](https://datatracker.ietf.org/doc/draft-dogru-cedulon-core/) | 2026-10-07T19:45:44Z | 2026-11-02T16:17:23Z | `eb98ebb69cecc7131cf73d2f82f367f701f58f0707947fb3d6d07e473b1d3383` |
| [draft-dogru-cedulon-decision-profile-04](https://www.ietf.org/archive/id/draft-dogru-cedulon-decision-profile-04.txt) | 2026-10-05 | 2026-11-02T16:17:24Z | `0d7d474664d0d49b656320871cc34c0b63b3c88c711cdab5cc7d7dbbfcb367f4` |
| [draft-dogru-cedulon-decision-profile-metadata](https://datatracker.ietf.org/api/v1/doc/document/draft-dogru-cedulon-decision-profile/) | 2026-10-05T01:27:03Z | 2026-11-02T16:17:23Z | `2c26295b0a86dc978f1f4e97b745db514f4dc40fa0a9d8c1b15eac52ae4598a6` |
| [draft-dogru-cedulon-decision-profile-page](https://datatracker.ietf.org/doc/draft-dogru-cedulon-decision-profile/) | 2026-10-05T01:27:03Z | 2026-11-02T16:17:23Z | `300f9eaa4a2e45b94ec5312a32fb9b9b7cf83dd0ef00fc4e7feee3773291ea34` |
| [draft-gruszka-audit-decision-receipts-00](https://www.ietf.org/archive/id/draft-gruszka-audit-decision-receipts-00.txt) | 2026-11-01 | 2026-11-02T16:15:40Z | `427a7f6958c9c4f169136e980989bc55de707e24a52e9b55fc60d25430f1eefa` |
| [draft-gruszka-audit-decision-receipts-03](https://www.ietf.org/archive/id/draft-gruszka-audit-decision-receipts-03.txt) | 2026-11-02 | 2026-11-02T16:15:41Z | `c0aae84b82108a3bd40cbbbee33df13c760b5c2e943a205e9efca4c623438245` |
| [draft-gruszka-audit-decision-receipts-metadata](https://datatracker.ietf.org/api/v1/doc/document/draft-gruszka-audit-decision-receipts/) | 2026-11-02T09:01:08Z | 2026-11-02T16:15:40Z | `95acdfe207f5ddc516de8ec8e18b197a7cc3f191a2ce114ab94a85c8326e5fbe` |
| [draft-gruszka-audit-decision-receipts-page](https://datatracker.ietf.org/doc/draft-gruszka-audit-decision-receipts/) | 2026-11-02T09:01:08Z | 2026-11-02T16:15:40Z | `9668314ec615fa797cc06f130830c310195011b93348f9f7b994e51e09276932` |
| [draft-gruszka-evaluation-receipt-mappings-04](https://www.ietf.org/archive/id/draft-gruszka-evaluation-receipt-mappings-04.txt) | 2026-10-26 | 2026-11-02T16:15:42Z | `aa24f2d4c6b51509aba836c3786d6eb32711c8638ae0621cd4a6a7a54c978c25` |
| [draft-gruszka-evaluation-receipt-mappings-metadata](https://datatracker.ietf.org/api/v1/doc/document/draft-gruszka-evaluation-receipt-mappings/) | 2026-10-26T15:11:39Z | 2026-11-02T16:15:41Z | `5cdf3e45b241954f705eb61912ef9f8ef03a4cd83f435ce618738d1b31e272f4` |
| [draft-gruszka-evaluation-receipt-mappings-page](https://datatracker.ietf.org/doc/draft-gruszka-evaluation-receipt-mappings/) | 2026-10-26T15:11:39Z | 2026-11-02T16:15:41Z | `affde7269024d8d6b32d60026ac0573667ac823216fb0026822cda90b37c6e4a` |
| [draft-gruszka-signed-evaluation-receipts-04](https://www.ietf.org/archive/id/draft-gruszka-signed-evaluation-receipts-04.txt) | 2026-10-26 | 2026-11-02T16:15:42Z | `d60c3dd95aefb8019a5f1c0ce041d8c4eb1d4571302766944bfbc92b91c1e358` |
| [draft-gruszka-signed-evaluation-receipts-metadata](https://datatracker.ietf.org/api/v1/doc/document/draft-gruszka-signed-evaluation-receipts/) | 2026-10-26T15:09:51Z | 2026-11-02T16:15:41Z | `2d8b1fd5b1e7bb8a94489fb2067db9696b49ec9f95340287d6d00c063039c331` |
| [draft-gruszka-signed-evaluation-receipts-page](https://datatracker.ietf.org/doc/draft-gruszka-signed-evaluation-receipts/) | 2026-10-26T15:09:51Z | 2026-11-02T16:15:41Z | `0c7d8d14c11e109095f4a9107a7413ab2b3e8f4fddb0b84c230a1e5ffcfda7d7` |
| [draft-he-agentproto-verifier-evidence-03](https://www.ietf.org/archive/id/draft-he-agentproto-verifier-evidence-03.txt) | 2026-10-31 | 2026-11-02T16:15:39Z | `c64cb2fd988476a56f82bdc4386a652c5841f7b3723941bffea44e73208ef600` |
| [draft-he-agentproto-verifier-evidence-metadata](https://datatracker.ietf.org/api/v1/doc/document/draft-he-agentproto-verifier-evidence/) | 2026-10-31T23:16:42Z | 2026-11-02T16:15:38Z | `68d2f16394ebf5eb147bada903402e04fa0a87efeb4339ff4d75a6c892bf1853` |
| [draft-he-agentproto-verifier-evidence-page](https://datatracker.ietf.org/doc/draft-he-agentproto-verifier-evidence/) | 2026-10-31T23:16:42Z | 2026-11-02T16:15:39Z | `1bf2907cf312c0c6e1852def71aaf0de11f3995e9feb5af57451049beb2fa556` |
| [draft-kuehlewind-audit-architecture-00](https://www.ietf.org/archive/id/draft-kuehlewind-audit-architecture-00.txt) | 2026-05-18 | 2026-11-02T16:15:40Z | `43a68f99f4b9457b2074711b630c9f8e3a57ce9766947e5d833f1899384731ef` |
| [draft-kuehlewind-audit-architecture-01](https://www.ietf.org/archive/id/draft-kuehlewind-audit-architecture-01.txt) | 2026-09-07 | 2026-11-02T16:15:41Z | `1dfdc835bfed03c3b923bf2163733a8428630c39c72fc63c52ebd078dd2ee075` |
| [draft-kuehlewind-audit-architecture-metadata](https://datatracker.ietf.org/api/v1/doc/document/draft-kuehlewind-audit-architecture/) | 2026-09-07T11:49:34Z | 2026-11-02T16:15:40Z | `f7e0041e10aaf06ee01444ef42b23402d4b230ac582e3da28b05ba2b4b3db398` |
| [draft-kuehlewind-audit-architecture-page](https://datatracker.ietf.org/doc/draft-kuehlewind-audit-architecture/) | 2026-09-07T11:49:34Z | 2026-11-02T16:15:40Z | `c111c792d0760db601a160a6dc8dfc149ab854a9688f1dcb895963047e9f8b71` |
| [draft-nandakumar-agentproto-pace-00](https://www.ietf.org/archive/id/draft-nandakumar-agentproto-pace-00.txt) | 2026-11-01 | 2026-11-02T16:15:41Z | `aff623233c2dc1572b2b0d4bd826cb7fdf839496233364fa0e33ed1a49e49477` |
| [draft-nandakumar-agentproto-pace-metadata](https://datatracker.ietf.org/api/v1/doc/document/draft-nandakumar-agentproto-pace/) | 2026-11-01T20:40:36Z | 2026-11-02T16:15:40Z | `e71f242c705085e78b65e617ff0d6bd06b007aba5c3a67d0263467ce59ae89a3` |
| [draft-nandakumar-agentproto-pace-page](https://datatracker.ietf.org/doc/draft-nandakumar-agentproto-pace/) | 2026-11-01T20:40:36Z | 2026-11-02T16:15:40Z | `c738dd8ab3be8d92bf5c12a456b18ba5d602240ee979008664e3ee2f85b39a55` |
| [draft-sergeev-audit-task-requirements-00](https://www.ietf.org/archive/id/draft-sergeev-audit-task-requirements-00.txt) | 2026-10-15 | 2026-11-02T16:15:41Z | `532a14ef7757cf68cce7ce77e4404810d1afc9bfe9926f2e5884fb353b3804f5` |
| [draft-sergeev-audit-task-requirements-metadata](https://datatracker.ietf.org/api/v1/doc/document/draft-sergeev-audit-task-requirements/) | 2026-10-16T06:11:55Z | 2026-11-02T16:15:40Z | `45d57f11a47e666a35153942d5f9f638d642c52b3377e3e6867b82a59eca162d` |
| [draft-sergeev-audit-task-requirements-page](https://datatracker.ietf.org/doc/draft-sergeev-audit-task-requirements/) | 2026-10-16T06:11:55Z | 2026-11-02T16:15:40Z | `3a35348942c6f43176b47884e624d20d86cf9950ec5499ed3d408bf4c5bfb5ac` |
| [draft-sergeev-claim-boundaries-02](https://www.ietf.org/archive/id/draft-sergeev-claim-boundaries-02.txt) | 2026-10-15 | 2026-11-02T16:17:24Z | `67d93ac09bd572bb01b5e00c3101daa6ee3a2217f5e23d2bb02658d6a731ccc0` |
| [draft-sergeev-claim-boundaries-metadata](https://datatracker.ietf.org/api/v1/doc/document/draft-sergeev-claim-boundaries/) | 2026-10-15T22:59:21Z | 2026-11-02T16:17:23Z | `45f002e0da690905adf695e13ca43e4ccadbfabca2b89a71603dcf99d7eb7ef8` |
| [draft-sergeev-claim-boundaries-page](https://datatracker.ietf.org/doc/draft-sergeev-claim-boundaries/) | 2026-10-15T22:59:21Z | 2026-11-02T16:17:23Z | `017fec4e5cc3b5ca4c9634b7768784531768b2bc62e687cd9439e5f1d3eab307` |
| [draft-templeman-scitt-measurement-capsule-01](https://www.ietf.org/archive/id/draft-templeman-scitt-measurement-capsule-01.txt) | 2026-10-27 | 2026-11-02T16:15:42Z | `d02bb2146fef267050e689375c7db22cb954f02f0a69ff8038382540c5192600` |
| [draft-templeman-scitt-measurement-capsule-metadata](https://datatracker.ietf.org/api/v1/doc/document/draft-templeman-scitt-measurement-capsule/) | 2026-10-28T05:12:04Z | 2026-11-02T16:15:41Z | `dd3c2f3de27490d16ea10ae8e74de5b0173946c7bbfbadcb02a537f0a6a7236c` |
| [draft-templeman-scitt-measurement-capsule-page](https://datatracker.ietf.org/doc/draft-templeman-scitt-measurement-capsule/) | 2026-10-28T05:12:04Z | 2026-11-02T16:15:41Z | `cfd8481a675d7f9284c35b68489d35876a16e94a6b1f2f34a6121459c3eb1fd2` |
| [draft-thaha-scitt-agent-execution-evidence-02](https://www.ietf.org/archive/id/draft-thaha-scitt-agent-execution-evidence-02.txt) | 2026-11 | 2026-11-02T16:15:42Z | `2b1f9f27b04a2c67c358c222827dbdb445c198fd9b8bba2fb56e5a2a3ba6a092` |
| [draft-thaha-scitt-agent-execution-evidence-metadata](https://datatracker.ietf.org/api/v1/doc/document/draft-thaha-scitt-agent-execution-evidence/) | 2026-11-01T10:05:28Z | 2026-11-02T16:15:41Z | `2ba61eeb3b815bd709695eddce3a363303e07de34a9de8a36f692afb5d48dc26` |
| [draft-thaha-scitt-agent-execution-evidence-page](https://datatracker.ietf.org/doc/draft-thaha-scitt-agent-execution-evidence/) | 2026-11-01T10:05:28Z | 2026-11-02T16:15:42Z | `1f614aaeb7241a7184dbd3c06f142e22c789ee263afa021b4280f5be129e352e` |
| [draft-wadkins-agentproto-action-determinability-00](https://www.ietf.org/archive/id/draft-wadkins-agentproto-action-determinability-00.txt) | 2026-09-10 | 2026-11-02T16:15:39Z | `1dd8b04e074cad734014584d7a068c7a9509b4af4b8df102e4a605887467e31b` |
| [draft-wadkins-agentproto-action-determinability-metadata](https://datatracker.ietf.org/api/v1/doc/document/draft-wadkins-agentproto-action-determinability/) | 2026-09-11T15:20:23Z | 2026-11-02T16:15:38Z | `cc1d7b7302bd7c33dca62ca16121bcbf765f728d29f597dce85f50db3c80bb8c` |
| [draft-wadkins-agentproto-action-determinability-page](https://datatracker.ietf.org/doc/draft-wadkins-agentproto-action-determinability/) | 2026-09-11T15:20:23Z | 2026-11-02T16:15:39Z | `785c6d83b1acfc141cca57a49ac6955e64d5179143e83451796a161fa0050895` |
| [draft-watts-eqr-conformance-05](https://www.ietf.org/archive/id/draft-watts-eqr-conformance-05.txt) | 2026-10-30 | 2026-11-02T16:15:42Z | `18a46eeabe9cd942e410f5ba2258d2eaf61c8d7fe4f425ee3f5eb63fbd753c5d` |
| [draft-watts-eqr-conformance-metadata](https://datatracker.ietf.org/api/v1/doc/document/draft-watts-eqr-conformance/) | 2026-10-31T10:24:30Z | 2026-11-02T16:15:41Z | `13b1ecddae865b9bef69d4cb03ee403741ce7dceab888483f96bcac18b2fc886` |
| [draft-watts-eqr-conformance-page](https://datatracker.ietf.org/doc/draft-watts-eqr-conformance/) | 2026-10-31T10:24:30Z | 2026-11-02T16:15:41Z | `78fe380f7db2b60e3bf8ddd33ddffc8c2f38f11eaeba44268ca0f0e04dba9240` |
| [draft-zhang-audit-record-limits-00](https://www.ietf.org/archive/id/draft-zhang-audit-record-limits-00.txt) | 2026-10-27 | 2026-11-02T16:15:41Z | `edf9fd3e2d3db9e365c090a8e994fc6b3b1a247131d06bfd802d0a506e7df4e5` |
| [draft-zhang-audit-record-limits-metadata](https://datatracker.ietf.org/api/v1/doc/document/draft-zhang-audit-record-limits/) | 2026-10-27T13:13:18Z | 2026-11-02T16:15:40Z | `9394d1f1b03acb5a24e51f5271119d0ba08ed67179651b553184f5c65b779b40` |
| [draft-zhang-audit-record-limits-page](https://datatracker.ietf.org/doc/draft-zhang-audit-record-limits/) | 2026-10-27T13:13:18Z | 2026-11-02T16:15:40Z | `751edc1a3a119d4b4a806148af29c0d804315ecb030602ec80f04b7eca1a3686` |
| [halvrenofviryel--ai-runtime-evidence-protocol-external-evidence](https://raw.githubusercontent.com/halvrenofviryel/ai-runtime-evidence-protocol/075aff5610731736405951ecf3b7c4bfc3cc0f07/EXTERNAL_EVIDENCE.md) | 2026-09-02T19:02:27Z | 2026-11-02T16:16:28Z | `b88d482221a77f748e73874cd9bb19f8a4c493f6cf04389262f384abf1155661` |
| [halvrenofviryel--ai-runtime-evidence-protocol-external-evidence-history](https://api.github.com/repos/halvrenofviryel/ai-runtime-evidence-protocol/commits?sha=075aff5610731736405951ecf3b7c4bfc3cc0f07&path=EXTERNAL_EVIDENCE.md&per_page=1) | 2026-09-02T19:02:27Z | 2026-11-02T16:25:44Z | `5b4d1eb21c39533d04aca9fea34f37e35a1f7563703c5bf96e55167a1b9d6c4c` |
| [halvrenofviryel--ai-runtime-evidence-protocol-head](https://api.github.com/repos/halvrenofviryel/ai-runtime-evidence-protocol/commits/main) | 2026-09-23T22:48:04Z | 2026-11-02T16:16:26Z | `3b2c0d4a87279d8977cbf57ffcc3f559a4bed94cc77eda600603e0c2e1425212` |
| [halvrenofviryel--ai-runtime-evidence-protocol-metadata](https://api.github.com/repos/halvrenofviryel/ai-runtime-evidence-protocol) | 2026-09-24T02:57:58Z | 2026-11-02T16:16:25Z | `2cb7076c9f5595bde581d4d3a2cdcdf61898e2c7ebdc131026621b0f10321454` |
| [halvrenofviryel--ai-runtime-evidence-protocol-readme](https://raw.githubusercontent.com/halvrenofviryel/ai-runtime-evidence-protocol/075aff5610731736405951ecf3b7c4bfc3cc0f07/README.md) | 2026-09-23T22:46:21Z | 2026-11-02T16:16:27Z | `7a043fd6289773900c0ab3d8c2096b22b9cb6737176564be9b3c51e0867382d4` |
| [halvrenofviryel--ai-runtime-evidence-protocol-readme-history](https://api.github.com/repos/halvrenofviryel/ai-runtime-evidence-protocol/commits?sha=075aff5610731736405951ecf3b7c4bfc3cc0f07&path=README.md&per_page=1) | 2026-09-23T22:46:21Z | 2026-11-02T16:25:44Z | `3d551dd710dd29406812161a938528d3de01837c05f4da91e74ca7468b6a8f79` |
| [halvrenofviryel--ai-runtime-evidence-protocol-releases](https://api.github.com/repos/halvrenofviryel/ai-runtime-evidence-protocol/releases?per_page=100) | UNKNOWN | 2026-11-02T16:16:27Z | `68bd9744095119a6936bc42e3326c1f3d0dbc2c3be60ff5a24fd0008517c4aea` |
| [halvrenofviryel--ai-runtime-evidence-protocol-tags](https://api.github.com/repos/halvrenofviryel/ai-runtime-evidence-protocol/tags?per_page=100) | Thu, 24 Sep 2026 02:57:58 GMT | 2026-11-02T16:16:26Z | `fe3fdb7c0fa205a9e8cb71782a061809e7c04987820a350f71e253d197a15b0b` |
| [halvrenofviryel--measurement-axioms-head](https://api.github.com/repos/halvrenofviryel/measurement-axioms/commits/main) | 2026-09-13T15:10:36Z | 2026-11-02T16:16:26Z | `be129671d8827e91c1701b947c72116dd82b3a526e3d7734ba8729685eb41d08` |
| [halvrenofviryel--measurement-axioms-metadata](https://api.github.com/repos/halvrenofviryel/measurement-axioms) | 2026-09-13T15:10:41Z | 2026-11-02T16:16:25Z | `81e828490cfb1f1fb079312e1f69ad1bfaac35b94c0180c0e05ccf8b6bfedc4a` |
| [halvrenofviryel--measurement-axioms-readme](https://raw.githubusercontent.com/halvrenofviryel/measurement-axioms/ea672f3918c53ac9ad22ad72d0b0a5d70a9a59ce/README.md) | 2026-09-13T14:46:21Z | 2026-11-02T16:16:27Z | `989d338737b4006f67f56b19f75a6ee332e23758472b4cdeed95b73490641c4d` |
| [halvrenofviryel--measurement-axioms-readme-history](https://api.github.com/repos/halvrenofviryel/measurement-axioms/commits?sha=ea672f3918c53ac9ad22ad72d0b0a5d70a9a59ce&path=README.md&per_page=1) | 2026-09-13T14:46:21Z | 2026-11-02T16:25:43Z | `357caf520c43c3efa247b4709ae351ada00762b35e504fd345b4f96e6a813c73` |
| [halvrenofviryel--measurement-axioms-releases](https://api.github.com/repos/halvrenofviryel/measurement-axioms/releases?per_page=100) | UNKNOWN | 2026-11-02T16:16:27Z | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |
| [halvrenofviryel--measurement-axioms-tag-commit](https://api.github.com/repos/halvrenofviryel/measurement-axioms/commits/d009fcb97c6ca03e962fb9c5f8ea6e21b619a1f5) | 2026-08-02T20:11:52Z | 2026-11-02T16:18:18Z | `9c05d859d5161abe20c61e853e1e6060228bef42325d82a60a01b64ecff6f987` |
| [halvrenofviryel--measurement-axioms-tags](https://api.github.com/repos/halvrenofviryel/measurement-axioms/tags?per_page=100) | Sun, 13 Sep 2026 15:10:41 GMT | 2026-11-02T16:16:26Z | `fcf1ed98e6d256128aa34db693a52020d511d5b6fe9ce857de39097657246f3d` |
| [halvrenofviryel--phionyx-mcp-server-head](https://api.github.com/repos/halvrenofviryel/phionyx-mcp-server/commits/main) | 2026-09-12T11:22:45Z | 2026-11-02T16:16:26Z | `5a4f37d1a064f67b2205b5e5bd4d49f2db8de4a69679683367599e0e422b979c` |
| [halvrenofviryel--phionyx-mcp-server-metadata](https://api.github.com/repos/halvrenofviryel/phionyx-mcp-server) | 2026-09-12T11:22:49Z | 2026-11-02T16:16:25Z | `b91dc168093c88625688ca39020b0bafdab58e64da760101202472923d1a3e3e` |
| [halvrenofviryel--phionyx-mcp-server-readme](https://raw.githubusercontent.com/halvrenofviryel/phionyx-mcp-server/7dc7f7eb1db80f465e7d438d95878ab2633983f4/README.md) | 2026-09-12T11:20:14Z | 2026-11-02T16:16:27Z | `6937932c9f1705fec8688fd6200a2e1ee52cc02951bb7996b6af4a4cf33095dd` |
| [halvrenofviryel--phionyx-mcp-server-readme-history](https://api.github.com/repos/halvrenofviryel/phionyx-mcp-server/commits?sha=7dc7f7eb1db80f465e7d438d95878ab2633983f4&path=README.md&per_page=1) | 2026-09-12T11:20:14Z | 2026-11-02T16:25:43Z | `2500cdc83d36c0de2da4d2466dc3db9ba3bd6f863549dd9492f93a7e4db22345` |
| [halvrenofviryel--phionyx-mcp-server-releases](https://api.github.com/repos/halvrenofviryel/phionyx-mcp-server/releases?per_page=100) | UNKNOWN | 2026-11-02T16:16:27Z | `8f3bdfd740cd834488095ae509050a26cbccd88297503ddfb50c157d82e4dc85` |
| [halvrenofviryel--phionyx-mcp-server-tag-commit](https://api.github.com/repos/halvrenofviryel/phionyx-mcp-server/commits/fdf5ba66f7b2e610b365224f681203287123faca) | 2026-08-10T13:56:07Z | 2026-11-02T16:18:18Z | `ed56b239dd1831d5cfe4a66faa9d0ddc6df4d123a7e2dc9f39f4c75a4aea9399` |
| [halvrenofviryel--phionyx-mcp-server-tags](https://api.github.com/repos/halvrenofviryel/phionyx-mcp-server/tags?per_page=100) | Sat, 12 Sep 2026 11:22:49 GMT | 2026-11-02T16:16:26Z | `e4554ef98edecc7aee165976424a9f7402f35090e4c63b4ad584560110374a52` |
| [halvrenofviryel--phionyx-pipeline-mcp-head](https://api.github.com/repos/halvrenofviryel/phionyx-pipeline-mcp/commits/main) | 2026-09-12T11:22:39Z | 2026-11-02T16:16:26Z | `6ebfd604f9c76cfd3cb8267b14ddd5f4b5b1df6d0bff99f8ca10672a285e27b2` |
| [halvrenofviryel--phionyx-pipeline-mcp-metadata](https://api.github.com/repos/halvrenofviryel/phionyx-pipeline-mcp) | 2026-09-12T11:22:43Z | 2026-11-02T16:16:25Z | `4691da56d76e942b4ada5862ba879f4de9870ee409428e0e4764897f3a90057c` |
| [halvrenofviryel--phionyx-pipeline-mcp-readme](https://raw.githubusercontent.com/halvrenofviryel/phionyx-pipeline-mcp/e36acd84022c3bc014e9a7083074fb5af62c276e/README.md) | 2026-09-12T11:20:10Z | 2026-11-02T16:16:27Z | `1078534f2dcd3a8270ddcced595c77628ada6a023c93e5658f5afb7fedc18bd2` |
| [halvrenofviryel--phionyx-pipeline-mcp-readme-history](https://api.github.com/repos/halvrenofviryel/phionyx-pipeline-mcp/commits?sha=e36acd84022c3bc014e9a7083074fb5af62c276e&path=README.md&per_page=1) | 2026-09-12T11:20:10Z | 2026-11-02T16:25:42Z | `ab0c42bd296c663fdb6f4d188ae5e02e80978e1409b35f4f64f7375960419039` |
| [halvrenofviryel--phionyx-pipeline-mcp-releases](https://api.github.com/repos/halvrenofviryel/phionyx-pipeline-mcp/releases?per_page=100) | UNKNOWN | 2026-11-02T16:16:26Z | `1aeb58bb29d2ccaee4c095f8bdd6ab46b52e96ad1630d78d9a35abc46bf457ad` |
| [halvrenofviryel--phionyx-pipeline-mcp-tag-commit](https://api.github.com/repos/halvrenofviryel/phionyx-pipeline-mcp/commits/b8c76f42b169700cea3c6368295162bb6e81ae19) | 2026-08-10T13:48:28Z | 2026-11-02T16:18:19Z | `71c27cb12ba9c5d4167b5a6a4f0141cbb4c90a21459fc8300b900705790cc029` |
| [halvrenofviryel--phionyx-pipeline-mcp-tags](https://api.github.com/repos/halvrenofviryel/phionyx-pipeline-mcp/tags?per_page=100) | Sat, 12 Sep 2026 11:22:43 GMT | 2026-11-02T16:16:26Z | `bde5c0f335ab047dc1f708368a389a6a53066cc740f23ff8e6fbb19680c38ff8` |
| [halvrenofviryel--phionyx-research-head](https://api.github.com/repos/halvrenofviryel/phionyx-research/commits/main) | 2026-09-23T16:44:18Z | 2026-11-02T16:16:26Z | `c98a6e1a53d63f68cc6e6f951402ccb9b91c360139cf1d8e0c17ce586677962d` |
| [halvrenofviryel--phionyx-research-metadata](https://api.github.com/repos/halvrenofviryel/phionyx-research) | 2026-09-23T16:44:42Z | 2026-11-02T16:16:25Z | `d723b75fb8c12c7f96da38aae84dfa5011b479a91b83449461fb03d7ed9e8084` |
| [halvrenofviryel--phionyx-research-readme](https://raw.githubusercontent.com/halvrenofviryel/phionyx-research/69bc8cfd282e9a0a45e34b1fcf6106b1ab618f9d/README.md) | 2026-09-23T16:44:18Z | 2026-11-02T16:16:27Z | `d3bb34f6963f3e3006699d889244ceb512ff49f6c3a9e6c740e6e829584551f5` |
| [halvrenofviryel--phionyx-research-readme-history](https://api.github.com/repos/halvrenofviryel/phionyx-research/commits?sha=69bc8cfd282e9a0a45e34b1fcf6106b1ab618f9d&path=README.md&per_page=1) | 2026-09-23T16:44:18Z | 2026-11-02T16:25:43Z | `aa9cbe1216271f1b74ffc2d094d28a241c89205bb60daa26eb9f6fddf4bf93bb` |
| [halvrenofviryel--phionyx-research-releases](https://api.github.com/repos/halvrenofviryel/phionyx-research/releases?per_page=100) | UNKNOWN | 2026-11-02T16:16:27Z | `885dbb142bb192ecfdd054d01d32e33ceeecf44a2646d362b1d1b9cc72b9407c` |
| [halvrenofviryel--phionyx-research-tags](https://api.github.com/repos/halvrenofviryel/phionyx-research/tags?per_page=100) | Wed, 23 Sep 2026 16:44:42 GMT | 2026-11-02T16:16:26Z | `4eff6b8665c31f1562d9529b11fbc07297c2d52ead341f214e8be15ffec1e18d` |
| [halvrenofviryel--resonatus-ontology-head](https://api.github.com/repos/halvrenofviryel/resonatus-ontology/commits/main) | 2026-10-11T17:06:15Z | 2026-11-02T16:16:26Z | `ba28befe6c9f918dc2237af98e939d006b48c1bf3dca444fc5d66b7e847dd15b` |
| [halvrenofviryel--resonatus-ontology-metadata](https://api.github.com/repos/halvrenofviryel/resonatus-ontology) | 2026-10-11T17:08:13Z | 2026-11-02T16:16:25Z | `37d0e149405e72a3fd2e2125ce7ad920314ccea5135cca6e3a584c7b22323e77` |
| [halvrenofviryel--resonatus-ontology-readme](https://raw.githubusercontent.com/halvrenofviryel/resonatus-ontology/46229d179c40524f12d70d68f735205fecf4c861/README.md) | 2026-10-11T17:00:05Z | 2026-11-02T16:16:27Z | `ac7958ad1eddd8eacd247f2aa3e84a9a3d38b74cd4be1589779a2fc91da1b85c` |
| [halvrenofviryel--resonatus-ontology-readme-history](https://api.github.com/repos/halvrenofviryel/resonatus-ontology/commits?sha=46229d179c40524f12d70d68f735205fecf4c861&path=README.md&per_page=1) | 2026-10-11T17:00:05Z | 2026-11-02T16:25:43Z | `9bcc1db8b43c3170743d9fbe81d60cd60517ee5a17a62ac01abab77eb419228c` |
| [halvrenofviryel--resonatus-ontology-releases](https://api.github.com/repos/halvrenofviryel/resonatus-ontology/releases?per_page=100) | UNKNOWN | 2026-11-02T16:16:27Z | `75da434ddd9058466d552e02c879a77d49044755b3055643bc757c940392f1ba` |
| [halvrenofviryel--resonatus-ontology-tags](https://api.github.com/repos/halvrenofviryel/resonatus-ontology/tags?per_page=100) | Sun, 11 Oct 2026 17:08:13 GMT | 2026-11-02T16:16:27Z | `eaeb6733f613cc8239d702fe7c3b02b8370aa71bf5fb8f8074e33d0c407d03a1` |
| [ietf127-agenda](https://datatracker.ietf.org/meeting/127/agenda/) | UNKNOWN | 2026-11-02T16:16:28Z | `aadbaa323cc16e3ae13c1d66df97f04e6e60cf898a8862147a66f7d04f906b5c` |
| [ietf127-agentproto](https://datatracker.ietf.org/meeting/127/session/agentproto) | UNKNOWN | 2026-11-02T16:16:28Z | `75205cc367fe68d12cc100ab30a4e43fe515b705cd65f18438fc47c549829d0a` |
| [ietf127-agentproto-agenda-00](https://datatracker.ietf.org/meeting/127/materials/agenda-127-agentproto-00) | 2026-10-30T16:48:20Z | 2026-11-02T16:17:24Z | `7a9e133e254f9e4a0466a570dfc08ccc6065b2f606083f0a9604f04ee9b79ecf` |
| [ietf127-agentproto-agenda-metadata](https://datatracker.ietf.org/api/v1/doc/document/agenda-127-agentproto/) | 2026-10-30T16:48:20Z | 2026-11-02T16:17:25Z | `c81c68041511a7f4175c98d5be0633534934b19c1d611a0d5a49e87745996d91` |
| [ietf127-audit](https://datatracker.ietf.org/meeting/127/session/audit) | UNKNOWN | 2026-11-02T16:16:28Z | `3db2dd4e15c2beeb101b013bd4db343f409c69b8135eaec3464bcb7dd4518863` |
| [ietf127-dates](https://datatracker.ietf.org/meeting/127/important-dates/) | UNKNOWN | 2026-11-02T16:16:28Z | `9a65c9252ed7b457836ab228f8c5400487832a82ab3d1a38d8c1a1ec34b0cf6e` |
| [rfc9943](https://www.rfc-editor.org/rfc/rfc9943.txt) | 2026-06 | 2026-11-02T16:16:27Z | `204aea020731e1306e8ffe0aaae5c9559a7a8edf24bd089ae79d6a6d6c7676f1` |
| [rfc9943-metadata](https://www.rfc-editor.org/rfc/rfc9943.json) | 2026-06 | 2026-11-02T16:17:26Z | `eb0ff209549d0b2c19e353b3f46b91953574c4e06e6274c97a87d02e9a4f5bbb` |
