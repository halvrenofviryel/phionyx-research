# Reproduce the bounded K2 and D + K3 results

This packet lets an unrelated researcher run the supplied author's experiments
without contacting the author, obtaining private expected answers, configuring
credentials, or making paid model calls. It contains exact local source and
dependency artifacts. It is a **local publication candidate, not a published
release or evidence that an external participant has run anything**.

On the documented Linux toolchain, one command runs both lanes:

```sh
python3 run.py --experiment all --out /tmp/airep-reproduction
```

The output path must not already exist. Run from this directory, or use the
absolute path to `run.py` from anywhere. No network is needed during replay.
For one lane, replace `all` with `k2` or `k3`.

| Lane | What runs | What the result can establish |
|---|---|---|
| K2 | Frozen beta.1 reference producer, Python verifier/reconciler, Node verifier and negative controls | Same-version author-side reference behavior; external implementation roles remain NOT_EVALUATED |
| D + K3 | Actual pinned LangGraph StateGraph, local IPC, controlled file effects, and D's explain CLI | Bounded cooperative pause and separate evidence stages; no LLM, preemptive kill, independent witness, or relying-party acceptance |

Start with [reproduction-quickstart.md](reproduction-quickstart.md). Inspect
[protocol-pins.json](protocol-pins.json) and verify the packet with
`python3 run.py --check-package`. The two source refs are separate; no merged
AIREP candidate or F integration is included. Unpublished D/K3 code is inside
`bundles/airep-sources.bundle`; no unavailable GitHub URL is required.

To implement an independent producer or consumer, follow
[the role checklist](role-and-independence-checklist.md) and the existing K2
adapter contract after extraction. Simply rerunning this packet is reproduction
of the author's code, not an independently written implementation.

Copy [the blank submission template](EXTERNAL_RUN_SUBMISSION_TEMPLATE.json)
outside this hash-pinned packet before filling it. No runner sends, uploads,
opens an issue, requests an endorsement, or upgrades external evidence status.
The existing [AIREP issue #62](https://github.com/halvrenofviryel/ai-runtime-evidence-protocol/issues/62)
describes the producer challenge; this local candidate has not been posted there.

Package validation and historical results are indexed in
[RESULTS_INDEX.md](RESULTS_INDEX.md). The publication review includes both
[K2](review/k2/review.json) and [D plus K3](review/d-plus-k3/review.json).

**Decision:** technical self-service candidate; publication/outreach HOLD pending
explicit owner approval. External reproduction/adoption remains NOT_EVALUATED.
