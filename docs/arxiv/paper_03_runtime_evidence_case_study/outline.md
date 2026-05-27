# Paper 03 — Section Outline

**Working title:** *Self-Governing AI-Pair-Programming: Measuring and Closing the Stochastic Input Generation Gap with Deterministic Runtime Hooks*

**Author:** Ali Toygar Abak (Phionyx Research) — ORCID 0009-0002-3718-4010
**Categories:** primary `cs.SE`; secondary `cs.AI`
**Status:** draft 2026-05-26

| § | Title | Word budget | Figure |
|---|---|---:|---|
| Abstract | — | 250 | — |
| §1 | Introduction | 600 | — |
| §2 | Background and substrate | 900 | Fig 1 |
| §3 | The stochastic input generation gap | 700 | — |
| §4 | System architecture | 1500 | Figs 2, 3 |
| §5 | Measurement protocol | 600 | — |
| §6 | Case study: closing the gap | 1500 | Fig 4 |
| §7 | Comparative analysis | 1200 | — |
| §8 | Reviewer-runnable evidence | 400 | — |
| §9 | Limitations | 500 | — |
| §10 | Future work | 400 | — |
| §11 | Conclusion | 300 | — |
| App. A | settings.json hook configuration | 300 | — |
| App. B | Audit script output schema | 300 | — |
| App. C | RGE v0.2 envelope fields | 300 | Fig 5 |
| **Total** | | **~9750** | **5 figures** |

## Figure inventory

1. **Fig 1** (§2.4): two-layer MCP architecture with shared `trace_id` (Mermaid block diagram).
2. **Fig 2** (§4.4): Claude Code lifecycle with 12 hook attachment points, colour-coded by class (Mermaid).
3. **Fig 3** (§4): data flow from prompt → tool call → gate → commit → telemetry → audit metric (Mermaid sequence).
4. **Fig 4** (§6): coverage timeline 2026-04-26 → 2026-05-26, intervention marker, forecast band (matplotlib via render_figures.py; Mermaid fallback for inline preview).
5. **Fig 5** (App. C): RGE v0.2 envelope field diagram (Mermaid class diagram).

## Evidence sources (every numeric claim cites one of these)

- `docs/arxiv/CANONICAL_EVIDENCE_TABLE.md` — pipeline architecture constants (46 blocks, CQS 0.862), public test count T7 = 1,131
- `docs/strategic/runtime_evidence_self_audit_2026-05-25.md` — 7.5% baseline
- `docs/strategic/runtime_evidence_self_audit_2026-05-26.md` — 9.5% post-intervention
- `phionyx_core/contracts/telemetry/canonical_blocks_v3_8_0.json` — pipeline order
- `docs/adr/0006-mcp-integration.md` — shared-trace contract
- Pinned git SHAs for all referenced commits

## Identity guardrails

- Runtime evidence, not cognition runtime
- No AGI progress claims (per `.claude/rules/agi-architecture.md`)
- No internal jargon ("frozen", "publication-ready", "manuscript ready")
- Public test count: T7 = 1,131 (never the internal 2,571)
- Honour manifesto §7 "What Phionyx Does Not Claim"

## Mind-loop stage declaration

This work touches mind-loop stage = **none (infrastructure)**. Hook coverage is automation/governance improvement, not cognitive progress. Per `.claude/rules/agi-architecture.md` Invariant 2.
