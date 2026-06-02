#!/usr/bin/env python3
"""Runtime evidence self-audit — measure my own pipeline-mcp consistency
across the last N days. Produces docs/strategic/runtime_evidence_self_audit_<DATE>.md.

Per manifesto v1.1 §2: "Governance must be executable at runtime." This
script measures whether Phionyx's own AI-session governance has been
executable AND executed.

Outputs (per day, for the last N days):
  - commits opened
  - pipeline-mcp tool calls (per tool)
  - verify_claim + response_gate ratio against commits
  - directive distribution (pass / regenerate / reject)
  - identified gaps

Method: reads `data/mcp_telemetry/session_*.json` (authoritative per-session
record produced by `_persist_state` in tools/claude_code_mcp/
phionyx_claude_mcp.py) + cross-references `git log` for commit counts.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TELEMETRY_DIR = REPO_ROOT / "data" / "mcp_telemetry"
OUT_DIR = REPO_ROOT / "docs" / "strategic"

GATE_TOOLS = {"phionyx_verify_claim", "phionyx_response_gate"}
ALL_TOOLS = {
    "phionyx_verify_claim",
    "phionyx_response_gate",
    "phionyx_verify_paths",
    "phionyx_causal_trace",
    "phionyx_checkpoint",
    "phionyx_session_report",
}


def load_sessions(since: datetime) -> list[dict]:
    sessions: list[dict] = []
    for f in sorted(TELEMETRY_DIR.glob("session_*.json")):
        try:
            data = json.loads(f.read_text())
        except Exception as exc:
            print(f"  skip {f.name}: {exc}", file=sys.stderr)
            continue
        ts = data.get("session_start") or 0
        if datetime.fromtimestamp(ts) < since:
            continue
        sessions.append(data)
    return sessions


def per_day_tool_counts(sessions: list[dict]) -> dict[date, Counter]:
    """For each day, count tool calls bucketed by the entry's OWN timestamp.

    BUGFIX 2026-05-27: previously bucketed by session_start, which
    attributed *every* timeline entry to the date the session began.
    For long-running sessions that span multiple calendar days, this
    inflated the session-start day's coverage and zeroed out the
    later days. Cf. /api/runtime-evidence (Founder Console) which
    correctly buckets by entry.timestamp; the discrepancy surfaced when
    a 24+ hour session showed 67 gate calls on the start day and 0 on
    the next day while the FC dashboard showed 38 + 29 = 67 split
    correctly.
    """
    by_day: dict[date, Counter] = defaultdict(Counter)
    for s in sessions:
        session_start = s.get("session_start") or 0
        for entry in s.get("timeline", []):
            entry_ts = entry.get("timestamp") or session_start
            d = datetime.fromtimestamp(entry_ts).date()
            tool = entry.get("tool", "unknown")
            by_day[d][tool] += 1
    return by_day


def per_day_directives(sessions: list[dict]) -> dict[date, Counter]:
    """For each day, count directive emissions bucketed by entry timestamp.

    Same BUGFIX as per_day_tool_counts (2026-05-27).
    """
    by_day: dict[date, Counter] = defaultdict(Counter)
    for s in sessions:
        session_start = s.get("session_start") or 0
        for entry in s.get("timeline", []):
            entry_ts = entry.get("timestamp") or session_start
            d = datetime.fromtimestamp(entry_ts).date()
            directive = entry.get("directive", "n/a")
            by_day[d][directive] += 1
    return by_day


def per_day_commits(since: datetime, sha_filter: set[str] | None = None) -> dict[date, int]:
    """Use git log to count commits per day.

    Args:
        since: window start datetime.
        sha_filter: optional set of short SHAs (first 7 hex chars). When
            provided, only commits whose short SHA is in the set are
            counted. Used by Paper 03 §10 "author-filtered denominator":
            excludes founder direct commits and other harness-bypass
            traffic that auto_attest_commit.py never recorded.
    """
    cmd = [
        "git", "log",
        f"--since={since.isoformat()}",
        "--format=%h %ai",
    ]
    try:
        out = subprocess.check_output(cmd, cwd=REPO_ROOT, text=True)
    except subprocess.CalledProcessError:
        return {}
    counts: dict[date, int] = defaultdict(int)
    for line in out.splitlines():
        parts = line.split(" ", 1)
        if len(parts) < 2:
            continue
        sha = parts[0][:7]
        if sha_filter is not None and sha not in sha_filter:
            continue
        try:
            ts = parts[1].split(" ")[0]  # YYYY-MM-DD
            counts[date.fromisoformat(ts)] += 1
        except Exception:
            continue
    return counts


def attested_shas(sessions: list[dict]) -> set[str]:
    """SHAs of commits the auto_attest_commit.py hook saw and recorded.

    These are the commits the binding layer actually witnessed via the
    PostToolUse:Bash hook on `git commit`. Commits made outside Claude
    Code (founder terminal commits, wrapper-script commits that bypass
    the matcher, CI automation) are absent from this set.

    Returns short SHAs (first 7 hex chars) for comparison with `git log
    --format=%h` output.
    """
    shas: set[str] = set()
    for s in sessions:
        for entry in s.get("timeline", []):
            if entry.get("tool") == "commit_attestation":
                sha = entry.get("commit_sha", "")
                if sha:
                    shas.add(sha[:7])
    return shas


def render_report(
    since: datetime,
    sessions: list[dict],
    tool_counts: dict[date, Counter],
    directives: dict[date, Counter],
    commits: dict[date, int],
    commits_attested: dict[date, int] | None = None,
) -> str:
    all_days = sorted(set(list(tool_counts) + list(commits)), reverse=True)
    total_gate_calls = 0
    total_all_calls = 0
    total_commits = 0
    total_directives: Counter = Counter()
    rows: list[tuple[str, ...]] = []

    for d in all_days:
        tc = tool_counts.get(d, Counter())
        gate = sum(tc[t] for t in GATE_TOOLS)
        all_tools = sum(tc.values())
        c = commits.get(d, 0)
        total_gate_calls += gate
        total_all_calls += all_tools
        total_commits += c
        for k, v in directives.get(d, Counter()).items():
            total_directives[k] += v
        ratio_expected = c * 2  # 1 verify_claim + 1 response_gate per commit per CLAUDE.md
        coverage = (gate / ratio_expected * 100) if ratio_expected else 0.0
        rows.append((
            d.isoformat(),
            str(c),
            str(gate),
            str(all_tools),
            f"{coverage:5.1f}%",
        ))

    grand_expected = total_commits * 2
    grand_coverage = (total_gate_calls / grand_expected * 100) if grand_expected else 0.0

    # Author-filtered (attested-only) parallel metric, per Paper 03 §10.
    attested_total = sum(commits_attested.values()) if commits_attested else 0
    attested_expected = attested_total * 2
    attested_coverage = (
        (total_gate_calls / attested_expected * 100) if attested_expected else 0.0
    )

    lines = [
        f"# Runtime Evidence Self-Audit — {date.today().isoformat()}",
        "",
        f"**Window:** since {since.date().isoformat()} (last {(date.today() - since.date()).days} days)",
        "**Source:** `data/mcp_telemetry/session_*.json` + `git log`",
        "**Method:** [`scripts/active/runtime_evidence_self_audit.py`](../../scripts/active/runtime_evidence_self_audit.py) — re-run any time, deterministic.",
        "",
        "## Question this measures",
        "",
        "Manifesto v1.1 §2 commits: *\"AI ethics statements are not enough. Governance must be executable at runtime.\"*",
        "",
        "CLAUDE.md rule: *Before claiming 'fixed' or 'done', call `phionyx_verify_claim`. Before deploying or committing, call `phionyx_response_gate`.*",
        "",
        "**Expected gate calls per commit: 2** (one verify_claim, one response_gate).",
        "",
        "## Headline",
        "",
        f"- **{total_commits}** commits in window",
        f"- **{total_gate_calls}** gate calls ({', '.join(sorted(GATE_TOOLS))})",
        f"- **{total_all_calls}** pipeline-mcp calls total (all 6 tools)",
        f"- Expected gate calls per CLAUDE.md: **{grand_expected}** (= {total_commits} commits × 2)",
        f"- **Coverage: {grand_coverage:.1f}%**",
        "",
    ]
    if commits_attested is not None:
        lines += [
            "### Coverage — author-filtered (Paper 03 §10)",
            "",
            "Restricts the denominator to commits the `auto_attest_commit.py` hook",
            "actually recorded. Excludes founder direct commits, wrapper-script",
            "commits that bypass the matcher, and CI automation traffic.",
            "",
            f"- **{attested_total}** attested commits in window",
            f"- Expected gate calls (attested-only): **{attested_expected}**",
            f"- **Coverage (attested-only): {attested_coverage:.1f}%**",
            "",
            "Note: the attested-commit set is forward-looking. Entries exist only",
            "for commits made after the `auto_attest_commit.py` hook landed (commit",
            "`af45aec1`, 2026-05-26). Windows preceding that commit show 0 attested",
            "commits.",
            "",
        ]
    lines += [
        "## Per-day breakdown",
        "",
        "| Day | Commits | Gate calls | All mcp calls | Coverage |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} |")
    lines += [
        "",
        "## Directive distribution",
        "",
    ]
    if total_directives:
        lines.append("| Directive | Count |")
        lines.append("|---|---:|")
        for directive, n in total_directives.most_common():
            lines.append(f"| {directive} | {n} |")
    else:
        lines.append("_(no directives recorded — virtually no gate calls)_")
    lines += [
        "",
        "## Honest reading",
        "",
        f"This window covers {len(sessions)} MCP sessions. The advisory CLAUDE.md rule",
        "would have required at least 2 gate calls per commit; actual coverage is",
        f"**{grand_coverage:.1f}%**. The pattern is consistent across days: pipeline-mcp",
        "is installed, configured, and active, but Claude (this assistant) does not",
        "invoke it on most commits. This is the *stochastic input generation* gap",
        "CLAUDE.md itself names — only Claude Code hooks bind invocation deterministically.",
        "",
        "## What this gap blocks",
        "",
        "- Manifesto §5.1 (\"decisions are inspectable by a third party\") — infrastructure",
        "  exists (audit chain envelope), but most commits leave no envelope behind.",
        "- Manifesto §3.1 (\"evidence is reproducible or it is not evidence\") — git",
        "  history is reproducible, but the per-claim envelope chain that ties a commit",
        "  to its verification artefacts is mostly empty.",
        "",
        "## What closes this gap (sequenced)",
        "",
        "1. **Binding hooks (Katman A)** — pre-commit BLOCK on missing gate call,",
        "   PreToolUse Edit/Write threshold, PostToolUse commit auto-attestation,",
        "   session-idle timeout. Status: the binding hook layer shipped (v0.7.2) —",
        "   commit/push, Edit/Write, Agent-spawn and Stop-grounding hooks now bind",
        "   invocation deterministically rather than leaving it to discretion.",
        "",
        "2. **Founder Console MCP panel (Katman B)** — live dashboard showing the",
        "   numbers above per session, with per-commit attestation badges and",
        "   cross-session aggregates. Status: shipped — the /runtime-evidence",
        "   dashboard renders these per session (now lifecycle-led, not coverage-led).",
        "",
        "3. **Structural — conversation envelope wrapping (Katman C)** — every",
        "   assistant message produces an envelope automatically; gate invocation",
        "   becomes a property of the runtime, not of the assistant's discretion.",
        "   Status: partial — a signed envelope chain (RGE v0.2) now persists per",
        "   gated turn; automatic per-message wrapping remains in design.",
        "",
        "## Reproduction",
        "",
        "```bash",
        "python3 scripts/active/runtime_evidence_self_audit.py --days 30",
        "```",
        "",
        f"_Generated {datetime.now().isoformat(timespec='seconds')} by_",
        "_`scripts/active/runtime_evidence_self_audit.py` against `data/mcp_telemetry/`._",
        "",
    ]
    return "\n".join(lines)


def render_json_feed(
    since: datetime,
    sessions: list[dict],
    tool_counts: dict[date, Counter],
    directives: dict[date, Counter],
    commits: dict[date, int],
    window_days: int,
) -> dict:
    """Public-safe JSON shape for the daily feed at phionyx-research/case-studies/.

    Mirrors the /api/runtime-evidence shape so the public phionyx.ai page can
    render the same dashboard from static build-time fetch.
    """
    total_commits = sum(commits.values())
    total_gate_calls = sum(c for day, counter in tool_counts.items() for tool, c in counter.items() if tool in GATE_TOOLS)
    total_all_calls = sum(c for day, counter in tool_counts.items() for tool, c in counter.items() if tool in ALL_TOOLS)
    expected_gate_calls = total_commits * 2
    coverage_percent = (total_gate_calls / expected_gate_calls * 100) if expected_gate_calls else 0.0

    directives_total: Counter = Counter()
    for day_directives in directives.values():
        directives_total.update(day_directives)

    per_day = []
    all_days = sorted(set(tool_counts.keys()) | set(commits.keys()) | set(directives.keys()), reverse=True)
    for d in all_days:
        c = commits.get(d, 0)
        gc = sum(tool_counts.get(d, Counter()).get(t, 0) for t in GATE_TOOLS)
        ac = sum(tool_counts.get(d, Counter()).get(t, 0) for t in ALL_TOOLS)
        cov = (gc / (c * 2) * 100) if c > 0 else None
        per_day.append({
            "date": d.isoformat(),
            "commits": c,
            "gate_calls": gc,
            "all_calls": ac,
            "coverage_percent": cov,
        })

    # ── L3 self-governance signals (aggregate-only counts/mean; public-safe) ──────────
    import os as _os
    _dc = [e.get("declaration_coverage") for s in sessions for e in s.get("timeline", [])
           if isinstance(e.get("declaration_coverage"), (int, float))]
    faithfulness = {
        "n": len(_dc),
        "mean": round(sum(_dc) / len(_dc), 3) if _dc else None,
        "low": sum(1 for v in _dc if v < 0.5),
    }
    _envelopes = _traces = 0
    for _r in [_os.environ.get("PHIONYX_MCP_AUDIT_ROOT"), str(Path("~/.phionyx/mcp_audit").expanduser())]:
        if not _r:
            continue
        _rp = Path(_r)
        if not _rp.is_dir():
            continue
        for _td in _rp.iterdir():
            _chain = _td / "chain.jsonl"
            if _chain.exists():
                _traces += 1
                try:
                    _envelopes += sum(1 for ln in _chain.read_text().splitlines() if ln.strip())
                except OSError:
                    pass
        if _traces:
            break
    signed_chain = {"envelopes": _envelopes, "traces": _traces, "live": _traces > 0}
    _labels_path = Path("~/.phionyx/detector_labels.jsonl").expanduser()
    _n_labels = 0
    if _labels_path.exists():
        try:
            _n_labels = sum(1 for ln in _labels_path.read_text().splitlines() if ln.strip())
        except OSError:
            pass
    lifecycle = {
        "n_governed_claims": total_gate_calls,
        "n_signed_records": _envelopes,
        "n_real_outcome_labels": _n_labels,
        "note": (
            "Aggregate funnel — different scopes, do not divide. Per-claim lifecycle-completion "
            "(signed record AND a real observed outcome) is ~0 today because real outcomes "
            "accumulate forward; never fabricated."
        ),
    }

    return {
        "generated_at_iso": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window_days": window_days,
        "since_iso": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "headline": {
            "total_commits": total_commits,
            "total_gate_calls": total_gate_calls,
            "total_all_calls": total_all_calls,
            "expected_gate_calls": expected_gate_calls,
            "coverage_percent": round(coverage_percent, 2),
        },
        "directives": dict(directives_total),
        "per_day": per_day,
        "session_count": len(sessions),
        "source": "github.com/halvrenofviryel/phionyx-research",
        "reproduce": (
            f"python3 case-studies/agentic-development-2026-05/scripts/"
            f"runtime_evidence_self_audit.py --days {window_days}"
        ),
        "schema_version": "v1.1",
        "disclaimer": (
            "Public read-only feed. Per-day counts derive from local telemetry "
            "+ git log of the private dev monorepo. Numbers are aggregate; no "
            "claim content, file paths, or credentials surface."
        ),
        # ── L3 self-governance signals (aggregate-only; v1.1) ──
        "faithfulness": faithfulness,
        "signed_chain": signed_chain,
        "lifecycle": lifecycle,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=30, help="Window in days (default 30)")
    parser.add_argument("--out", type=Path, default=None, help="Output report path")
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help=(
            "Optional second output: write the public-safe JSON feed to this "
            "path. Used by publish_case_study_snapshot.sh to keep "
            "phionyx-research/case-studies/.../feed/latest.json in sync."
        ),
    )
    parser.add_argument(
        "--author-filter",
        action="store_true",
        help=(
            "Add a parallel coverage metric using only commits the "
            "auto_attest_commit.py hook recorded (excludes founder direct "
            "commits and other harness-bypass traffic). See Paper 03 §10."
        ),
    )
    args = parser.parse_args()

    since = datetime.now() - timedelta(days=args.days)
    sessions = load_sessions(since)
    tool_counts = per_day_tool_counts(sessions)
    directives = per_day_directives(sessions)
    commits = per_day_commits(since)

    commits_attested: dict[date, int] | None = None
    if args.author_filter:
        sha_filter = attested_shas(sessions)
        commits_attested = per_day_commits(since, sha_filter=sha_filter)

    report = render_report(
        since, sessions, tool_counts, directives, commits, commits_attested
    )
    out_path = args.out or (OUT_DIR / f"runtime_evidence_self_audit_{date.today().isoformat()}.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report)
    print(report)
    print(f"\n=== Written to: {out_path}")

    if args.json_out is not None:
        feed = render_json_feed(since, sessions, tool_counts, directives, commits, args.days)
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(feed, indent=2, ensure_ascii=False))
        print(f"=== JSON feed written to: {args.json_out}")


if __name__ == "__main__":
    main()
