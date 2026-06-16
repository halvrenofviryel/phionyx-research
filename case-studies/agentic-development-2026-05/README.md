# Case Study — Agentic Development (2026-05)

> **What this is:** the public-safe data behind Phionyx's *agentic development* case study — measurements of how often Claude (an AI coding agent) actually invokes the runtime-evidence gates while writing the Phionyx codebase itself.
>
> **Consumer-facing landing:** [phionyx.ai/agentic-development](https://phionyx.ai/agentic-development) — read this first if you arrived here without context.

---

## Why this case study matters

The Phionyx manifesto commits to *"governance must be executable at runtime."* The case study tests that commitment **reflexively** — by measuring whether Phionyx's own AI-pair-programming development workflow exhibits the discipline Phionyx publishes for production AI systems.

Concretely: Phionyx's `CLAUDE.md` rule requires Claude (the AI coding agent) to call `phionyx_response_gate` before claiming a fix is working and before every commit. If Claude does not follow the rule, the rule is advisory in name only. We measure compliance directly.

## What the snapshots show

The four markdown files under `snapshots/` are the output of running the deterministic measurement scripts at two boundary moments:

| File | When | What it measures |
|---|---|---|
| `01-baseline_2026-05-25.md` | day before the binding hook layer landed | 30-day rolling coverage; reads **7.5%** — the advisory rule alone produces sub-10% compliance |
| `02-post-intervention_2026-05-26.md` | day the binding hook layer + MCP config fixes landed | same 30-day window, re-measured; reads **9.5%** — bumped by the heavily-gated intervention day itself, structural effect not yet visible because the window predates the hooks |
| `03-scenarios_pre-restart.md` | first run of the 13-scenario verification suite | 13 / 13 hard-pass — each binding mechanism verified individually against synthetic stdin payloads |
| `04-scenarios_post-restart.md` | re-run after `/mcp restart` | 13 / 13 hard-pass; C4 strengthened from informational to hard-block JSON emission as a side-effect of the fresh session telemetry |

These four files are the entire public-evidence surface the case study is built on. Every numeric claim in the consumer landing page traces here.

## Reproduce the numbers

The two Python scripts under `scripts/` are the deterministic transformations that produce the snapshots from the underlying telemetry + git log. You can re-run them on the Phionyx Core SDK's public mirror (which carries the same code) — but the source telemetry (`data/mcp_telemetry/session_*.json`) is per-installation, so a reviewer running the script on their own setup measures their *own* compliance, not Phionyx's.

```bash
# Audit script — measures rolling-window coverage
python3 scripts/runtime_evidence_self_audit.py --days 30

# Scenario suite — verifies each binding mechanism
python3 scripts/runtime_evidence_test_scenarios.py
```

Both scripts produce markdown reports identical in shape to the snapshots in this directory. The audit's output is `runtime_evidence_self_audit_<DATE>.md`; the scenario runner's output is `test_scenarios_<DATE>.md`.

## The figure

`figures/coverage_timeline.png` — the daily coverage timeline behind the 7.5% → 9.5% movement. The single 85.7% spike is the intervention-day session itself; the structural effect of the hooks is a falsifiable forecast that the next 30-day audit window will measure.

## Two windows, one dashboard

The live Founder Console dashboard at `localhost:3005/runtime-evidence` (Phionyx's internal monitoring view) renders the same numbers with a second window added: **"since binding-active cutoff"** — the post-intervention window where the falsifiable forecast applies. As that window accumulates more days, its coverage should rise structurally. If it doesn't, the hook design failed and the case study is refuted.

## The honest framing

This case study does **not** claim:
- That the binding hook layer solves all AI-pair-programming compliance problems.
- That 7.5% → 9.5% is statistically meaningful — it is one data point pair on a 30-day rolling window.
- That the post-intervention forecast is proven — it is *falsifiable*, not validated.

It does claim:
- A measurement methodology that any reviewer can re-run.
- An honestly-disclosed baseline.
- A binding mechanism + the falsifiable forecast that the next audit window will measure whether it worked.

## Source repository

This case study is a snapshot from the private Phionyx development monorepo.

## Citation

Cite this case study by repository path + commit SHA:

```
Abak, A. T. (2026). Phionyx Research — Agentic Development Case Study (2026-05).
phionyx-research repository, case-studies/agentic-development-2026-05/.
```

License: AGPL-3.0-or-later (matches the parent repo).

## Updates

This snapshot is **dated 2026-05-26**. As the binding-active window accumulates more measurement days, fresh snapshots will be added to `snapshots/` (next expected: 30 days after the binding-active cutoff). The directory layout will not change; only new files will be added.
