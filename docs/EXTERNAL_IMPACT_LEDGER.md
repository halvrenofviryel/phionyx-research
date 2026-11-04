# External impact ledger

This ledger separates availability, reproduction, independent implementation,
interoperability, adoption and standards impact. A public repository link or an
author-side rerun is not counted as external uptake.

The machine-readable record is [external_impact_ledger.json](external_impact_ledger.json).

The K1 plus K2/D/K3/K5 packet was merged into public `main` by
[PR #108](https://github.com/halvrenofviryel/phionyx-research/pull/108) at commit
[`54682cfd`](https://github.com/halvrenofviryel/phionyx-research/commit/54682cfd312dc8c7935e926539811cfc29ea6568).
Public availability changes the delivery state only; it does not add an external
reproducer, implementation, interoperability result, adoption event or standards
endorsement. The versioned release and DOI were published on 4 November 2026:
[GitHub release](https://github.com/halvrenofviryel/phionyx-research/releases/tag/control-evidence-study-v1.0.0)
and [Zenodo DOI `10.5281/zenodo.23960852`](https://doi.org/10.5281/zenodo.23960852).
That improves stable availability and citability; it does not change any
external-reproduction, interoperability, adoption or endorsement grade.
The bounded technical explanation was published as a
[Hugging Face Community Article](https://huggingface.co/blog/phionyx/when-an-ai-agent-says-stop-what-evidence-proves-th)
on 4 November 2026. That is an author-side communication event, not outside
reproduction or validation.
The existing
[Substack article](https://phionyxresearch.substack.com/p/what-did-the-ai-decide-and-what-does)
received a dated correction on the same day. It now points to the beta producer,
the exact study release, the version DOI and the technical article while
retaining the original historical text. This is a correction and discovery
event; it does not change the evidence grade.
The bounded result is also listed on the live
[phionyx.ai research](https://phionyx.ai/research) and
[publications](https://phionyx.ai/publications) pages. Deployment from Viryel
[PR #46](https://github.com/halvrenofviryel/Viryel/pull/46) completed on 4
November 2026. The research card states the synthetic, author-side and
non-production limits and links the exact release, DOI and technical article.
This is an author-side discovery surface, not external validation or adoption.

| Evidence | Evidence record date | Frozen target | Grade and role | What it establishes |
|---|---|---|---|---|
| Emek Can Doğru independent producer | 2026-09-02 | AIREP v0.1.2 | Maintainer-reproduced external producer | One independently authored producer was accepted by both pinned v0.1.2 verifiers |
| Joel Hillier / Certisyn consumer | 2026-09-02 | AIREP v0.2 verifier corpus v0.1 | Maintainer-reproduced external consumer/verifier | One independently implemented verifier matched the frozen fields, exposing one package-derived projection defect |
| K2 same-version packet | 2026-11-03 | AIREP v0.2.0-beta.1 | Author-side package; external role NOT_EVALUATED | A pinned self-service path exists; no outside producer or consumer result yet |
| K3 runtime packet | 2026-11-03 | LangGraph 1.2.19 plus AIREP v0.2 | Author-side runtime package; external reproduction NOT_EVALUATED | A pinned self-service runtime experiment exists; no outside rerun or product adoption yet |

The two completed external records target different frozen AIREP versions and
must remain separate. No row currently establishes same-version external
producer-to-consumer interoperability, product deployment, merged upstream use,
working-group adoption or standards endorsement.

## Four-goal reassessment

| Goal | Current decision | Basis |
|---|---|---|
| T1 — reproducible original result | **MET_LOCAL** | Frozen K1 result and clean replay; same-owner synthetic holdout remains the limit |
| T2 — same-version external interoperability | **NOT_MET** | The two external results target different AIREP versions; K2 has no external adapter result |
| T3 — real runtime evidence | **MET_BOUNDED_LOCAL** | K3 runs a pinned LangGraph runtime with controlled IPC and file effects; no LLM, independent observer or production deployment |
| T4 — substantive external uptake | **NOT_MET_FOR_CURRENT_PACKET** | No outside rerun, integration, product use or upstream merge for K1/K2/K3/K5 |

K6 initialization is complete: events have sources, record dates, evidence grades
and technical-use classifications, and T1–T4 have been reassessed. Monitoring
remains open because future external use cannot be completed by an author-side
publication step. No global ranking or “top 10” claim is supported at this state.
