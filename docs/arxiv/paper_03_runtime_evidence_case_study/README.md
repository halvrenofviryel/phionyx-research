# Paper 03 — Runtime Evidence Case Study

**Working title:** *Self-Governing AI-Pair-Programming: Measuring and Closing the Stochastic Input Generation Gap with Deterministic Runtime Hooks*

**Status:** Draft, 2026-05-26. Pinned to monorepo commit `4bca5f3e`.

This directory holds the markdown source for Phionyx arXiv Paper 03, the case-study companion to Paper 02 ([@abak2026evidenceprotocol]). It applies the evidence-oriented runtime-telemetry protocol from Paper 02 reflexively to Phionyx's own AI-pair-programming development workflow.

## Contents

| File | Purpose |
|---|---|
| `paper.md` | Canonical markdown source (~9750 words across 11 sections + 3 appendices). |
| `outline.md` | Section-level outline + word budgets + figure inventory + evidence-source pointers. |
| `references.bib` | BibTeX file. Self-contained for arXiv submission; reuses entries from `paper_02/references.bib` with consistent keys. |
| `figures/fig1_two_layer_mcp.md` | Two-layer MCP architecture with shared `trace_id` (Mermaid). |
| `figures/fig2_hook_lifecycle.md` | Claude Code lifecycle with 12 hook attachment points (Mermaid). |
| `figures/fig3_data_flow.md` | Data flow from prompt to coverage metric (Mermaid sequence). |
| `figures/fig4_coverage_timeline.md` | Coverage timeline 2026-04-26 → 2026-05-26 (Mermaid + matplotlib for arXiv PDF). |
| `figures/fig5_envelope_chain.md` | RGE v0.2 envelope schema + chain linkage (Mermaid class diagram). |
| `figures/render_figures.py` | Render all five figures to PNG and PDF at 300dpi for arXiv submission. |

## Rendering targets

The paper source is **Markdown-first** so it renders on GitHub, Substack, phionyx.ai/research, and any IDE preview. Mermaid blocks inside the figure files render inline on GitHub and Substack.

For arXiv submission, run:

```bash
cd docs/arxiv/paper_03_runtime_evidence_case_study/figures
python3 render_figures.py
```

This produces:
- `fig1_two_layer_mcp.{png,pdf}` (rendered via `@mermaid-js/mermaid-cli`)
- `fig2_hook_lifecycle.{png,pdf}` (via mermaid-cli)
- `fig3_data_flow.{png,pdf}` (via mermaid-cli)
- `fig4_coverage_timeline.{png,pdf}` (via matplotlib; the chart shape exceeds Mermaid `xychart-beta` capabilities for arXiv-PDF quality)
- `fig5_envelope_chain.{png,pdf}` (via mermaid-cli)

Dependencies:
- `npm install -g @mermaid-js/mermaid-cli` (for fig 1, 2, 3, 5)
- `pip install matplotlib` (for fig 4)

For LaTeX conversion (optional, for arXiv's preferred `.tex` source):

```bash
pandoc paper.md \
  --bibliography=references.bib \
  --citeproc \
  --csl=ieee.csl \
  -o paper.tex
```

The conversion matches Paper 02's `paper.md → paper.tex` build path.

## Reusable everywhere

This paper is designed to be cited and excerpted across multiple surfaces:

- **arXiv:** preprint submission once a sibling submission_package/ is prepared (mirrors paper_02 layout).
- **phionyx.ai/research:** rendered as a research artefact alongside Paper 02.
- **Substack:** can be excerpted into a Phionyx Research post (the case-study narrative arc is naturally readable in segments).
- **Visa-narrative artefact set (Q1 2027):** load-bearing evidence of Phionyx's self-governance discipline.
- **Founder Console:** `/runtime-evidence` dashboard already renders the live numbers cited in §6 ([source](../../../apps/founder-console/app/runtime-evidence/page.tsx)).
- **CLAUDE.md cross-reference:** future updates to the project constitution can link here as the canonical explanation of the binding-enforcement layer.

When citing this paper externally, use:

> Abak, A. T. (2026). *Self-Governing AI-Pair-Programming: Measuring and Closing the Stochastic Input Generation Gap with Deterministic Runtime Hooks*. Phionyx arXiv Paper 03. Manuscript. URL: github.com/halvrenofviryel/phionyx-research, commit `4bca5f3e`.

## Identity guardrails (honoured throughout)

- Runtime evidence, not cognition runtime. No AGI progress claims.
- Public test count: **T7 = 1,131 passed @ c8fa1f9 on Python 3.12** (canonical evidence table). Internal 2,571 not cited in this paper.
- No internal jargon in publication-facing copy ("frozen", "publication-ready", "manuscript ready").
- Manifesto §7 ("What Phionyx Does Not Claim") preserved.
- Per `.claude/rules/agi-architecture.md` Invariant 2, mind-loop stage = **none — infrastructure**.

## Reproduction

Every numeric claim in the paper traces to:

- `docs/arxiv/CANONICAL_EVIDENCE_TABLE.md` (T7, A1–A7)
- `docs/strategic/runtime_evidence_self_audit_2026-05-25.md` (baseline)
- `docs/strategic/runtime_evidence_self_audit_2026-05-26.md` (post-intervention)
- A pinned git SHA: `4bca5f3e` (current), `0d66e17d`, `af45aec1`, `c8fa1f9`
- A pinned file path: `tools/claude_code_mcp/_telemetry.py:10–14`, etc.

To reproduce the coverage measurement:

```bash
git clone https://github.com/halvrenofviryel/phionyx-research
cd phionyx-research
git checkout 4bca5f3e
python3 scripts/active/runtime_evidence_self_audit.py --days 30
# Output: docs/strategic/runtime_evidence_self_audit_<DATE>.md
```
