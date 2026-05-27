#!/usr/bin/env python3
"""Render Paper 03 figures to PNG and PDF at 300dpi for arXiv submission.

Usage:
    python3 render_figures.py              # render all
    python3 render_figures.py --figure 4   # render one

Two rendering paths:

  - Figures 1, 2, 3, 5 are rendered via matplotlib so the build is
    fully local (no browser dependency, no external service). The
    ``.md`` files in this directory remain the canonical Mermaid
    sources for inline rendering on GitHub, Substack, and the Phionyx
    website; these matplotlib versions are the arXiv-PDF artefacts.
  - Figure 4 (coverage timeline) is a line chart rendered directly via
    matplotlib because its data shape exceeds Mermaid xychart-beta
    capabilities for publication-quality output.

Dependency: pip install matplotlib

The earlier mermaid-cli path (npx @mermaid-js/mermaid-cli) is documented
in README.md as an alternative when a Chromium-capable environment is
available. The matplotlib path is the default because it works in
headless sandboxes.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


# ── Style constants ──────────────────────────────────────────────────

BLOCKING = "#fee2e2"      # light red fill
BLOCKING_EDGE = "#dc2626"  # red edge
OBSERVE = "#dbeafe"        # light blue fill
OBSERVE_EDGE = "#2563eb"   # blue edge
EVENT = "#f3f4f6"          # light gray fill
EVENT_EDGE = "#4b5563"     # gray edge
EXEC = "#f5d0fe"           # light purple fill
EXEC_EDGE = "#a21caf"      # purple edge
STORE = "#dcfce7"          # light green fill
STORE_EDGE = "#16a34a"     # green edge
TRACE = "#fef3c7"          # light yellow fill
TRACE_EDGE = "#d97706"     # amber edge
TEXT_DARK = "#111827"


def _box(ax, x, y, w, h, text, fill, edge, fontsize=8, weight="normal", lw=1.2):
    import matplotlib.patches as mp
    rect = mp.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.04",
        linewidth=lw, edgecolor=edge, facecolor=fill,
    )
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h / 2, text,
            ha="center", va="center", fontsize=fontsize,
            color=TEXT_DARK, weight=weight, wrap=True)


def _arrow(ax, x1, y1, x2, y2, color="#1f2937", style="->", lw=1.2,
           connection="arc3,rad=0", linestyle="-"):
    import matplotlib.patches as mp
    arrow = mp.FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle=style, mutation_scale=12,
        linewidth=lw, color=color,
        connectionstyle=connection, linestyle=linestyle,
    )
    ax.add_patch(arrow)


def _ax(figsize):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def _save(fig, stem):
    for ext in ("png", "pdf"):
        out = HERE / f"{stem}.{ext}"
        fig.savefig(out, dpi=300 if ext == "png" else None, bbox_inches="tight")
        print(f"  wrote {out.name}")
    import matplotlib.pyplot as plt
    plt.close(fig)


# ── Figure 1: Two-layer MCP architecture ─────────────────────────────

def render_fig1():
    fig, ax = _ax((10, 6))

    # Claude Code session (top centre)
    _box(ax, 3.5, 8.5, 3.0, 1.1, "Claude Code session\n(LLM + harness)",
         EVENT, EVENT_EDGE, fontsize=9, weight="bold")

    # SessionStart hook (left of session)
    _box(ax, 0.2, 8.6, 2.6, 0.9, "SessionStart hook\nsession_start_attest.py",
         OBSERVE, OBSERVE_EDGE, fontsize=7)

    # Trace coordination file (centre)
    _box(ax, 3.7, 6.2, 2.6, 1.0, "~/.phionyx/active_trace\nshared trace_id",
         TRACE, TRACE_EDGE, fontsize=8, weight="bold")

    # Pipeline MCP (bottom left)
    _box(ax, 0.2, 3.5, 3.6, 2.0,
         "phionyx-pipeline MCP\n6 tools:\nverify_claim · response_gate\nverify_paths · causal_trace\ncheckpoint · session_report",
         EVENT, EVENT_EDGE, fontsize=7)

    # Server MCP (bottom right)
    _box(ax, 6.2, 3.5, 3.6, 2.0,
         "phionyx-mcp-server MCP\n8 capabilities (2 impl + 6 stub):\nverify_tool_descriptor\nrecord_tool_call\nverify_chain_integrity\nquery_audit_history",
         EVENT, EVENT_EDGE, fontsize=7)

    # Pipeline output (bottom left store)
    _box(ax, 0.4, 0.8, 3.3, 1.6,
         "data/mcp_telemetry/\nsession_<trace>.json\n(directive log)",
         STORE, STORE_EDGE, fontsize=7)

    # Server output (bottom right store)
    _box(ax, 6.3, 0.8, 3.5, 1.6,
         "~/.phionyx/mcp_audit/\n<trace>/<turn>.json\nRGE v0.2 envelope chain\nEd25519 + hash-linked",
         STORE, STORE_EDGE, fontsize=7)

    # Arrows
    # Session → MCPs (tool calls)
    _arrow(ax, 4.2, 8.5, 2.0, 5.5, color=EVENT_EDGE)
    ax.text(2.6, 7.1, "tool call", fontsize=7, color=EVENT_EDGE, style="italic")
    _arrow(ax, 5.8, 8.5, 8.0, 5.5, color=EVENT_EDGE)
    ax.text(6.9, 7.1, "tool call", fontsize=7, color=EVENT_EDGE, style="italic")

    # SessionStart → trace (reset)
    _arrow(ax, 2.8, 8.7, 4.0, 7.2, color=OBSERVE_EDGE, linestyle="--")
    ax.text(2.9, 8.05, "reset on\nstartup", fontsize=7, color=OBSERVE_EDGE, style="italic")

    # Both MCPs → trace (read)
    _arrow(ax, 2.5, 5.5, 4.0, 6.5, color=TRACE_EDGE, linestyle=":", lw=1.0)
    _arrow(ax, 7.5, 5.5, 6.0, 6.5, color=TRACE_EDGE, linestyle=":", lw=1.0)
    ax.text(2.9, 5.85, "read", fontsize=7, color=TRACE_EDGE, style="italic")
    ax.text(6.9, 5.85, "read", fontsize=7, color=TRACE_EDGE, style="italic")

    # MCPs → output stores (write)
    _arrow(ax, 2.0, 3.5, 2.0, 2.4, color=STORE_EDGE)
    _arrow(ax, 8.0, 3.5, 8.0, 2.4, color=STORE_EDGE)
    ax.text(1.4, 2.95, "write", fontsize=7, color=STORE_EDGE, style="italic")
    ax.text(8.2, 2.95, "write", fontsize=7, color=STORE_EDGE, style="italic")

    # Server store → Pipeline MCP (chain head surfacing)
    _arrow(ax, 6.3, 1.6, 3.7, 4.4, color=EVENT_EDGE, linestyle="--", connection="arc3,rad=-0.3")
    ax.text(4.5, 2.2, "head_hash + valid\n(mcp_envelope_chain)", fontsize=6.5,
            color=EVENT_EDGE, style="italic", ha="center")

    ax.set_title("Figure 1 — Two-layer MCP architecture with shared trace_id (ADR-0006)",
                 fontsize=10, weight="bold", pad=8)
    _save(fig, "fig1_two_layer_mcp")


# ── Figure 2: Claude Code lifecycle with 12 hooks ────────────────────

def render_fig2():
    fig, ax = _ax((14, 9))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 11)

    # Lifecycle events as horizontal spine (well-spaced, no overlap)
    events = [
        ("SessionStart", 1.0),
        ("UserPromptSubmit", 3.0),
        ("PreToolUse", 6.5),
        ("tool exec", 9.5),
        ("PostToolUse", 11.4),
        ("Stop", 13.4),
        ("SubagentStop", 14.9),
    ]
    spine_y = 5.5

    # Spine arrow
    _arrow(ax, 0.3, spine_y, 15.7, spine_y, color="#4b5563", lw=1.5, style="-|>")

    for label, x in events:
        fill = EXEC if label == "tool exec" else EVENT
        edge = EXEC_EDGE if label == "tool exec" else EVENT_EDGE
        _box(ax, x - 0.75, spine_y - 0.4, 1.5, 0.8, label, fill, edge,
             fontsize=7.5, weight="bold")

    # PreCompact event (off-spine, upper right)
    _box(ax, 14.5, 8.1, 1.4, 0.7, "PreCompact", EVENT, EVENT_EDGE,
         fontsize=7.5, weight="bold")
    _box(ax, 14.5, 9.2, 1.4, 0.9,
         "pre_compact_\ncheckpoint.py\nlog gate age",
         OBSERVE, OBSERVE_EDGE, fontsize=6)
    _arrow(ax, 15.2, 9.2, 15.2, 8.8, color=OBSERVE_EDGE, linestyle="--", lw=0.9, style="-")

    # Observability hooks ABOVE spine (two tiers, well-spaced to fit 9 hooks)
    obs_hooks = [
        # tier 1 (closer to spine, y=7.4)
        ("session_start_attest.py\nlog session boundary", 1.0, 7.4),
        ("log_user_prompt.py\nlog prompt SHA + len", 3.0, 7.4),
        ("check_mcp_tool_call.py\nlog 3rd-party MCP\n(matcher: mcp__.*)", 6.5, 7.4),
        ("auto_attest_commit.py\nlog commit SHA\n(matcher: Bash)", 11.0, 7.4),
        ("attest_subagent_stop.py\nlog subagent end", 14.9, 7.4),
        # tier 2 (farther, y=9.0)
        ("log_external_ingress.py\nlog URL+size\n(matcher: WebFetch/Search)", 12.5, 9.0),
        # v0.7.1/v0.7.2 additions
        ("check_memory_schema.py\n(v0.7.1 F-MS1)\nfrontmatter Pydantic validation", 1.0, 9.0),
        ("post_edit_language_check.py\n(v0.7.2 P2)\npy_compile + ruff / tsc /\njson / yaml / memory_schema\n(matcher: Edit|Write|MultiEdit|\nNotebookEdit)", 11.0, 9.2),
        ("run_targeted_tests.py\n(v0.7.2 P4)\ndiff → pytest routes\nStop hook (after question_grounding)", 13.4, 9.2),
    ]
    for text, x, y in obs_hooks:
        h = 1.4 if y > 8.5 else 1.1  # taller boxes for the multiline v0.7.x labels
        _box(ax, x - 0.95, y - h / 2, 1.9, h, text, OBSERVE, OBSERVE_EDGE, fontsize=5.5 if y > 8.5 else 6)
        _arrow(ax, x, y - h / 2, x, spine_y + 0.4, color=OBSERVE_EDGE, linestyle="--", lw=0.9, style="-")

    # Subagent layer (above the entire spine, manual-invoke flow)
    _box(ax, 0.3, 10.4, 4.2, 0.65,
         "Subagent layer (v0.7.2 P1):  diff-reviewer  — fresh context, Read-only,\n"
         "invoked manually for semantic review; not a hook.",
         "#fef3c7", "#d97706", fontsize=6.5, weight="bold")

    # Blocking hooks BELOW spine — PreToolUse has 4 of them, fan out in two rows
    block_hooks_t1 = [   # tier 1: closer to spine
        ("check_mcp_gate.py\nBLOCK on missing gate\nmatcher: Bash\n(commit|push|merge|\nrebase|cherry-pick|\nmake-commit)", 4.4, 3.0),
        ("check_edit_gate.py\nBLOCK on Edit/Write\n> 20 lines\nmatcher: Edit|Write\n|MultiEdit|NotebookEdit", 7.4, 3.0),
        ("check_question_grounding.py\nBLOCK if Q references\nunread artifact\n(always-on)", 13.4, 3.0),
    ]
    block_hooks_t2 = [   # tier 2: farther from spine
        ("check_bash_external_\neffect.py\nBLOCK on gh/npm/\ndocker/kubectl/...\nmatcher: Bash", 5.5, 0.9),
        ("check_agent_spawn.py\nBLOCK on Agent\nspawn", 8.5, 0.9),
    ]
    for text, x, y in block_hooks_t1:
        _box(ax, x - 1.0, y - 0.7, 2.0, 1.4, text, BLOCKING, BLOCKING_EDGE,
             fontsize=5.8, weight="bold")
        _arrow(ax, x, y + 0.7, x, spine_y - 0.4, color=BLOCKING_EDGE, lw=1.1, style="-")
    for text, x, y in block_hooks_t2:
        _box(ax, x - 1.0, y - 0.55, 2.0, 1.1, text, BLOCKING, BLOCKING_EDGE,
             fontsize=5.8, weight="bold")
        # Arrow routes via a kink to avoid overlapping tier 1
        _arrow(ax, x, y + 0.55, x, spine_y - 0.4, color=BLOCKING_EDGE, lw=1.1,
               style="-", connection="arc3,rad=0.0")

    # Legend (bottom left)
    leg_y = 10.4
    _box(ax, 0.3, leg_y, 1.7, 0.45, "BLOCKING hook", BLOCKING, BLOCKING_EDGE, fontsize=7, weight="bold")
    _box(ax, 2.2, leg_y, 1.9, 0.45, "observability hook", OBSERVE, OBSERVE_EDGE, fontsize=7)
    _box(ax, 4.3, leg_y, 1.5, 0.45, "lifecycle event", EVENT, EVENT_EDGE, fontsize=7)
    _box(ax, 6.0, leg_y, 1.2, 0.45, "tool exec", EXEC, EXEC_EDGE, fontsize=7)

    ax.text(15.6, 5.7, "time →", fontsize=8, color="#4b5563", style="italic", ha="right")
    ax.set_title("Figure 2 — Claude Code lifecycle with 15 hook attachment points (5 blocking + 10 observability) + subagent layer",
                 fontsize=10, weight="bold", pad=8)
    _save(fig, "fig2_hook_lifecycle")


# ── Figure 3: Data flow from prompt to coverage metric ───────────────

def render_fig3():
    fig, ax = _ax((11, 8))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 12)

    # Actors as vertical lifelines
    actors = [
        ("User", 0.7),
        ("Assistant\n(Claude)", 2.3),
        ("PreTool\nhook", 4.0),
        ("Pipeline MCP\n(gate)", 5.7),
        ("Tool\nruntime", 7.4),
        ("Telemetry +\ngit log", 9.0),
        ("audit\nscript", 10.3),
    ]
    for name, x in actors:
        _box(ax, x - 0.5, 11.0, 1.0, 0.8, name, EVENT, EVENT_EDGE, fontsize=7, weight="bold")
        # vertical lifeline
        ax.plot([x, x], [11.0, 0.5], color="#9ca3af", linestyle=":", linewidth=0.7)

    # Sequence of arrows (y values descending)
    def msg(y, x1, x2, label, color="#1f2937", lw=1.0, dashed=False):
        ls = "--" if dashed else "-"
        _arrow(ax, x1, y, x2, y, color=color, lw=lw, style="->", linestyle=ls)
        mid = (x1 + x2) / 2
        ax.text(mid, y + 0.1, label, fontsize=6.5, color=color, ha="center", style="italic")

    msg(10.3, 0.7, 2.3, "1. prompt: 'fix the bug'")
    msg(9.8, 2.3, 5.7, "2. phionyx_response_gate(claim_fixed, ...)", color=BLOCKING_EDGE)
    msg(9.3, 5.7, 9.0, "3. write directive entry", color=STORE_EDGE, dashed=True)
    msg(8.8, 5.7, 2.3, "4. directive: pass", color=EVENT_EDGE, dashed=True)
    msg(8.3, 2.3, 4.0, "5. PreToolUse: Edit('paper.md', ...)")
    msg(7.8, 4.0, 9.0, "6. read recent gate calls", color=STORE_EDGE, dashed=True)
    msg(7.3, 4.0, 7.4, "7. allow → tool fires", color=EXEC_EDGE)
    msg(6.8, 7.4, 0.7, "8. edit applied", color=EXEC_EDGE, dashed=True)
    msg(6.3, 7.4, 9.0, "9. PostToolUse: auto_attest", color=OBSERVE_EDGE, dashed=True)
    msg(5.8, 0.7, 2.3, "10. 'commit'")
    msg(5.3, 2.3, 4.0, "11. PreToolUse: Bash('git commit')")
    msg(4.8, 4.0, 9.0, "12. recent gate? YES → allow", color=STORE_EDGE, dashed=True)
    msg(4.3, 4.0, 7.4, "13. allow", color=EXEC_EDGE)
    msg(3.8, 7.4, 9.0, "14. commit SHA + attestation", color=STORE_EDGE, dashed=True)

    # Audit later
    ax.plot([0.5, 10.8], [3.0, 3.0], color="#d1d5db", linewidth=0.6, linestyle="-.")
    ax.text(5.5, 3.15, "... time passes; more turns ...", fontsize=7, color="#6b7280",
            ha="center", style="italic")

    msg(2.5, 0.7, 10.3, "15. run audit script", color="#4b5563")
    msg(2.0, 10.3, 9.0, "16. read telemetry + git log", color=STORE_EDGE, dashed=True)
    msg(1.5, 10.3, 10.3, "17. coverage = gate_calls / (2 × commits)", color="#4b5563")
    msg(1.0, 10.3, 0.7, "18. report written + dashboard", color="#4b5563", dashed=True)

    ax.set_title("Figure 3 — Data flow from prompt through gate, hook, commit, and audit",
                 fontsize=10, weight="bold", pad=8)
    _save(fig, "fig3_data_flow")


# ── Figure 4: Coverage timeline (matplotlib — unchanged) ─────────────

def render_fig4():
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from datetime import date

    daily = [
        (date(2026, 4, 28),  0.0), (date(2026, 4, 29),  0.0),
        (date(2026, 4, 30),  0.0), (date(2026, 5, 1),   0.0),
        (date(2026, 5, 2),   0.0), (date(2026, 5, 3),   0.0),
        (date(2026, 5, 4),   0.0), (date(2026, 5, 5),   0.0),
        (date(2026, 5, 6),   0.0), (date(2026, 5, 7),   0.0),
        (date(2026, 5, 8),   0.0), (date(2026, 5, 9),   0.0),
        (date(2026, 5, 10),  0.0), (date(2026, 5, 11),  0.0),
        (date(2026, 5, 13),  0.0), (date(2026, 5, 15),  0.0),
        (date(2026, 5, 16),  0.0), (date(2026, 5, 18),  0.0),
        (date(2026, 5, 19),  0.0), (date(2026, 5, 20),  0.0),
        (date(2026, 5, 21),  0.0), (date(2026, 5, 22),  0.0),
        (date(2026, 5, 23),  0.0), (date(2026, 5, 24),  7.7),
        (date(2026, 5, 25),  2.9), (date(2026, 5, 26), 85.7),
    ]

    fig, ax = plt.subplots(figsize=(10, 5))
    xs = [d for d, _ in daily]
    ys = [v for _, v in daily]
    ax.plot(xs, ys, marker="o", linewidth=1.2, color="#1f2937", label="Daily coverage (%)")
    ax.axhline(7.5, linestyle="--", color="#dc2626", linewidth=1.0,
               label="30-day baseline 2026-05-25 (7.5%)")
    ax.axhline(9.5, linestyle="--", color="#2563eb", linewidth=1.0,
               label="30-day re-measurement 2026-05-26 (9.5%)")
    ax.axvline(date(2026, 5, 26), color="#16a34a", linestyle=":", linewidth=1.5,
               alpha=0.7, label="Intervention")

    ax.set_ylim(-2, 100)
    ax.set_ylabel("Gate coverage (%)")
    ax.set_xlabel("Date (2026)")
    ax.set_title("Daily gate coverage, 30-day window ending 2026-05-26")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b-%d"))
    fig.autofmt_xdate()
    ax.legend(loc="upper left", fontsize=9, framealpha=0.95)
    ax.grid(True, axis="y", alpha=0.25)

    _save(fig, "fig4_coverage_timeline")


# ── Figure 5: RGE v0.2 envelope schema ───────────────────────────────

def render_fig5():
    fig, ax = _ax((10, 7))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 9)

    # Main envelope class
    env_text = (
        "GovernedResponseEnvelope (RGE v0.2)\n"
        "─────────────────────────────────\n"
        "trace_id           : str\n"
        "turn_index         : int\n"
        "producer           : str\n"
        "user_text          : str\n"
        "tool_descriptor_hash      : str (sha256)\n"
        "descriptor_change_detected: bool\n"
        "tool_permission_scope     : list[str]\n"
        "input_hash         : str (sha256)\n"
        "output_hash        : str (sha256)\n"
        "approval_state     : str\n"
        "anomaly_flag       : bool\n"
        "decision           : str\n"
        "decision_reason    : str\n"
        "runtime_policy_basis      : list[str]\n"
        "integrity          : IntegrityBlock"
    )
    _box(ax, 0.5, 1.5, 5.5, 6.5, env_text, EVENT, EVENT_EDGE, fontsize=7)

    # Integrity block
    integ_text = (
        "IntegrityBlock\n"
        "──────────────\n"
        "previous   : sha256\n"
        "current    : sha256\n"
        "signature  : Ed25519\n"
        "public_key : base64"
    )
    _box(ax, 7.0, 4.5, 4.5, 3.0, integ_text, BLOCKING, BLOCKING_EDGE, fontsize=8, weight="bold")

    # Filesystem store
    store_text = (
        "FilesystemEnvelopeStore\n"
        "──────────────────────\n"
        "iter_chain(trace_id) → Envelope[]\n"
        "head(trace_id)       → sha256\n"
        "verify_chain(envs)   → Verdict"
    )
    _box(ax, 7.0, 1.5, 4.5, 2.3, store_text, STORE, STORE_EDGE, fontsize=8)

    # Arrows
    _arrow(ax, 6.0, 6.0, 7.0, 6.0, color=BLOCKING_EDGE, lw=1.5)
    ax.text(6.5, 6.18, "integrity", fontsize=7, color=BLOCKING_EDGE, style="italic", ha="center")

    _arrow(ax, 6.0, 2.5, 7.0, 2.5, color=STORE_EDGE, lw=1.5)
    ax.text(6.5, 2.68, "persists", fontsize=7, color=STORE_EDGE, style="italic", ha="center")

    # Chain linkage arrow (self-loop)
    _arrow(ax, 3.0, 7.95, 3.0, 8.6, color="#4b5563", lw=1.0, style="<->")
    ax.text(3.2, 8.3, "integrity.previous → prior.integrity.current\n(hash chain — tamper-evident)",
            fontsize=7, color="#4b5563", style="italic", va="center")

    ax.set_title("Figure 5 — Governed Response Envelope v0.2: schema + chain linkage",
                 fontsize=10, weight="bold", pad=8)
    _save(fig, "fig5_envelope_chain")


# ── Main ─────────────────────────────────────────────────────────────

RENDERERS = {
    1: render_fig1,
    2: render_fig2,
    3: render_fig3,
    4: render_fig4,
    5: render_fig5,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figure", type=int, choices=[1, 2, 3, 4, 5], default=None,
                        help="Render only this figure (default: all)")
    args = parser.parse_args()

    try:
        import matplotlib  # noqa: F401
    except ImportError:
        print("matplotlib not installed. pip install matplotlib", file=sys.stderr)
        return 1

    targets = [args.figure] if args.figure else [1, 2, 3, 4, 5]
    for n in targets:
        print(f"Rendering figure {n}...")
        RENDERERS[n]()
    return 0


if __name__ == "__main__":
    sys.exit(main())
