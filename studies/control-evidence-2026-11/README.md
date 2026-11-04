# Control Delivery Is Not Execution

**A reproducible AIREP boundary study, version 1.0.0**

This study packages two complementary author-side measurements:

- a frozen 24-case synthetic comparison of an explicitly naive ACK-promotion
  rule and a bounded evidence evaluator; and
- a self-contained AIREP `v0.2.0-beta.1` reference/runtime packet with six
  controlled LangGraph scenarios.

The source packet was published on 3 November 2026 by
[phionyx-research PR #108](https://github.com/halvrenofviryel/phionyx-research/pull/108).
The immutable merge commit is
[`54682cfd312dc8c7935e926539811cfc29ea6568`](https://github.com/halvrenofviryel/phionyx-research/commit/54682cfd312dc8c7935e926539811cfc29ea6568).

## Current release state

The source is public and the versioned release metadata is prepared. The
dedicated GitHub release and Zenodo DOI have **not yet been issued**. Until they
exist, cite the immutable merge commit and use the citation files in this
directory. Do not invent or reserve a DOI in downstream references.

## Main results

| Lane | Frozen observation | Boundary |
|---|---|---|
| Synthetic ACK comparison | Naive ACK promoted unsupported stronger assertions in 16/18 shared holdout cases; bounded evaluator 0/18 | Controlled synthetic corpus; not a population error rate or product comparison |
| Bounded evaluator | 31/31 evidenced-claim recall; 54/54 state and qualification; 52/54 exact condition sets | Exact condition preservation is incomplete |
| AIREP reference lane | 28 tests, eight negative controls; 37 SATISFIED and one NOT_EVALUATED | First-party reference behavior, not external interoperability |
| LangGraph runtime lane | 13 tests and six controlled scenarios | Deterministic application nodes, no LLM, same-host observer |
| Offline packet | 172 inputs, two isolated author runs and 930 archived evidence files checked | External reproduction remains NOT_EVALUATED |

The study does not establish production safety, preemptive cancellation, full
ACDER/AIREP conformance, third-party validation, same-version external
interoperability, adoption or standards-body endorsement.

## Reproduce

From the repository root, verify the published packet:

```sh
python3 tools/verify_prepublication_candidate.py
python3 docs/external-replication/run.py --check-package
```

Run the two lanes on the supported Linux axis:

```sh
python3 docs/external-replication/run.py \
  --experiment all --out /tmp/airep-control-evidence
python3 -B experiments/ietf/acder02-control-benchmark/reproduce.py \
  --out /tmp/acder02-control-benchmark
```

Read [the research landing page](../../docs/CONTROL_EVIDENCE_RESEARCH.md) and
[the offline quickstart](../../docs/external-replication/reproduction-quickstart.md)
before interpreting the output.

## Build the deposit artifact

After committing all intended release files and confirming a clean worktree:

```sh
python3 studies/control-evidence-2026-11/build_release.py \
  --out-dir /tmp/control-evidence-release
python3 studies/control-evidence-2026-11/verify_release.py \
  /tmp/control-evidence-release/control-evidence-study-v1.0.0.tar.gz
```

The builder creates a deterministic archive, an external manifest and a SHA-256
sidecar. It records the exact source commit and refuses to package a dirty
worktree. It does not upload, tag, release or create a DOI.

## Citation objects

Keep these three objects separate:

1. Cite the [AIREP paper](https://doi.org/10.48550/arXiv.2608.21363) for the
   protocol and its evidence model.
2. Name the exact implementation target, AIREP `v0.2.0-beta.1` commit
   `8a6c01ecce457aa94330c0ed7219e4c56ebfe771`.
3. Cite this study for the K1/K2/K3/K5 experimental results. Replace the current
   immutable-commit citation with the dedicated study DOI after deposit.

Machine-readable drafts are provided as [CITATION.cff](CITATION.cff),
[CITATION.bib](CITATION.bib), [codemeta.json](codemeta.json) and
[zenodo.json](zenodo.json).

## Independent evidence

A rerun of the supplied author code is useful reproduction evidence but is not an
independently authored implementation. Use the blank
[external-run template](../../docs/external-replication/EXTERNAL_RUN_SUBMISSION_TEMPLATE.json)
and the [role checklist](../../docs/external-replication/role-and-independence-checklist.md).
Contributor identity is published only with permission.
