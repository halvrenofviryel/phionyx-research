# Control evidence research

**Publication status:** published in `main` on 3 November 2026 by
[PR #108](https://github.com/halvrenofviryel/phionyx-research/pull/108), merge
commit [`54682cfd312dc8c7935e926539811cfc29ea6568`](https://github.com/halvrenofviryel/phionyx-research/commit/54682cfd312dc8c7935e926539811cfc29ea6568).
The merge makes the author-side packet publicly inspectable; it does not turn it
into independent evidence. Version `1.0.0` was subsequently published from exact
release merge commit `a5956f6d575c431745f902a242b1a25262fed89d` as a
[GitHub release](https://github.com/halvrenofviryel/phionyx-research/releases/tag/control-evidence-study-v1.0.0)
and [Zenodo record](https://zenodo.org/records/23960852).

This study examines one practical distinction: a control request,
its receipt, its enforcement, its execution and an observed effect are separate
claims. A valid hash, signature or acknowledgement cannot by itself upgrade the
others.

The most useful entry point is the self-contained runtime packet. It runs six
controlled LangGraph scenarios and retains raw events, AIREP artifacts and the
bounded explain view. The comparison experiment is supporting evidence that shows
how an explicitly naive ACK rule overstates stronger claims on synthetic cases.

## Run the artifacts

### Runtime and same-version reference packet

On Linux x86_64 with CPython 3.12, Node 20.19.6 and Git installed:

```sh
cd docs/external-replication
python3 run.py --check-package
python3 run.py --experiment all --out /tmp/airep-reproduction
```

This runs the frozen K2 reference harness and the D plus K3 LangGraph experiment
without a network request, API key or model call. Begin with
[START_HERE.md](external-replication/START_HERE.md) and inspect the preserved
[author-side validation result](../reports/external-replication/RESULTS.md).

### Bounded comparison

```sh
cd experiments/ietf/acder02-control-benchmark
python3 -B reproduce.py --out /tmp/acder02-control-benchmark
```

Begin with the experiment [README](../experiments/ietf/acder02-control-benchmark/README.md)
and [results](../experiments/ietf/acder02-control-benchmark/RESULTS.md).

## What is established

| Artifact | Observed result | Supported interpretation |
|---|---|---|
| K1 frozen holdout | Naive ACK 16/18 unsupported stronger assertions; bounded evaluator 0/18 on the shared subset | The declared ACK-promotion rule loses evidence boundaries on this synthetic corpus |
| K1 bounded evaluator | 31/31 evidenced-claim recall; 54/54 state and qualification; 52/54 exact condition sets | The evaluator did not obtain its zero by always abstaining; exact condition preservation is not complete |
| K2 reference harness | 28 tests and eight negative controls; native final status INCOMPLETE with 37 SATISFIED and 1 NOT_EVALUATED | Same-version first-party reference behavior, not external producer-to-consumer interoperability |
| K3 LangGraph run | 13 tests and six controlled runtime scenarios | Bounded cooperative pause and separate receipt/execution/effect observations in one pinned runtime |
| K5 packet | 172 inputs, two clean isolated author-side runs and 930 archived evidence files verified | A third party can run the supplied author artifacts; no third party is inferred to have done so |

## What is not established

The artifacts do not establish independent validation of these new results,
production safety, preemptive cancellation, broad framework superiority, full
ACDER or AIREP conformance, same-version external interoperability, adoption or
IETF endorsement. The LangGraph experiment uses deterministic application nodes
and no LLM. Its observer shares the executor's host and trust domain.

The existing external AIREP evidence remains valuable but separate: the v0.1.2
producer result and the v0.2 consumer/verifier result target different frozen
packages and cannot be combined into a same-version interoperability claim. See
the [external impact ledger](EXTERNAL_IMPACT_LEDGER.md).

## Cite and reuse

For the experimental results, cite version DOI
[`10.5281/zenodo.23960852`](https://doi.org/10.5281/zenodo.23960852) and identify
the exact AIREP target as `v0.2.0-beta.1` commit
`8a6c01ecce457aa94330c0ed7219e4c56ebfe771`. The study-specific citation files
and deposit metadata are under
[`studies/control-evidence-2026-11/`](../studies/control-evidence-2026-11/).
For the protocol itself, cite
[*AIREP: A Protocol for Per-Decision Evidence in AI Runtime Governance*](https://doi.org/10.48550/arXiv.2608.21363).
Protocol, implementation target and experimental result are separate citation
objects.

## Review order

1. Read this page and the two short artifact entry pages.
2. Run the package hash check before executing dependencies.
3. Reproduce either lane into a new output directory.
4. Inspect native failure, missing and not-evaluated states before reading summary prose.
5. Use the blank external submission template only for a genuinely separate run
   or implementation; author-side reruns remain author-side evidence.

The source packet, versioned release and Zenodo DOI have been published. The
bounded technical explanation is available as a
[Hugging Face Community Article](https://huggingface.co/blog/phionyx/when-an-ai-agent-says-stop-what-evidence-proves-th).
This author-side communication does not change the evidence grade. IETF
submission remains a separate user-performed action. The historical
prepublication scope is retained in
[PREPUBLICATION_REVIEW_2026-11-03.md](PREPUBLICATION_REVIEW_2026-11-03.md), while
the current publication event is recorded in [PUBLICATION_STATUS.md](PUBLICATION_STATUS.md).
