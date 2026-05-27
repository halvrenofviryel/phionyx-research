"""Reasoning Memory Graph — typed Pydantic view over pipeline-MCP telemetry.

v0.7.1 F-RM1.

Phionyx pipeline-MCP telemetry already collects everything Iusztin (2026-05-26
*Designing Your Agents' Unified Memory*) and Pachaar (2026-05-26 *Pydantic
fixed my Agent's Memory*) describe as "reasoning memory" — which tools were
used, what decisions succeeded, what failed, which reasoning paths worked.
The data lives in ``data/mcp_telemetry/session_*.json`` (per-session
timeline arrays). It is collected, but not queryable as a typed graph.

This module is the typed view. It does NOT collect new data. It reads the
existing telemetry, projects it into a typed graph of nodes + edges, and
exposes ``query_*`` functions for the canonical multi-hop queries the
roadmap (v0.7.1 F-RM1) declares as the acceptance criterion.

Design rules:

  * **Pydantic-typed.** Every node and every edge is a Pydantic model.
    No untyped dicts cross the public surface. Mirrors the schema discipline
    Phionyx already applies to RGE v0.2 envelopes.

  * **Pure read.** This module never writes anywhere except the in-memory
    graph object. Telemetry on disk is the authoritative record.

  * **Stdlib + pydantic only.** No graph database, no external store.
    `agi-architecture.md` Invariant 3 applies: retrieval-only changes are
    NOT AGI progress — this is an audit-surface expansion.

Public surface (used by the Founder Console panel + tests):

  * :class:`ReasoningMemoryGraph` — the graph dataclass.
  * :func:`build_from_telemetry` — read disk → typed graph.
  * :func:`query_evidence_type_pass_rate` — Q1 multi-hop query.
  * :func:`query_commits_by_directive` — Q2 multi-hop query.
  * :func:`query_passed_despite_no_evidence` — Q3 outlier query.
  * :func:`query_gate_to_commit_lag` — Q4 temporal query.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────
# Node types
# ─────────────────────────────────────────────────────────────────────────

class SessionNode(BaseModel):
    """A Claude Code session — root of one telemetry file."""

    session_id: str
    started_iso: str
    last_update_iso: str
    call_count: int = 0
    claude_session_id: Optional[str] = None


class ClaimNode(BaseModel):
    """A `phionyx_response_gate` or `phionyx_verify_claim` invocation.

    The claim is the input. The verdict (linked via produced_verdict) is
    the output. Together they form one reasoning event.
    """

    claim_id: str  # session_id + "::" + call_number
    session_id: str
    call_number: int
    iso_time: str
    tool: str  # phionyx_response_gate | phionyx_verify_claim | ...
    evidence_type: Optional[str] = None
    confidence: Optional[float] = None


class VerdictNode(BaseModel):
    """The deterministic gate's output for one claim.

    `directive` is one of {pass, damp, rewrite, regenerate, reject,
    auto_attest, n/a, checkpoint, ok, solid}. The first five are the gate
    directives proper (see `phionyx_core.pipeline.blocks.response_revision_gate`).
    The others are observability or hook-emitted attestations.
    """

    verdict_id: str  # mirror of the claim_id
    directive: str
    drift_severity: str = "none"
    phi: Optional[float] = None
    w_final: Optional[float] = None


class CommitNode(BaseModel):
    """A `commit_attestation` entry written by the post-commit hook."""

    commit_sha: str  # 40-char SHA
    session_id: str
    iso_time: str


class ToolCallNode(BaseModel):
    """A `mcp_tool_invocation` (third-party MCP tool) record."""

    tool_call_id: str
    session_id: str
    iso_time: str
    mcp_tool_name: str
    args_hash: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────
# Edge types
# ─────────────────────────────────────────────────────────────────────────

EdgeKind = Literal[
    "produced_verdict",       # ClaimNode → VerdictNode
    "had_evidence_type",      # ClaimNode → evidence_type literal
    "led_to_commit",          # ClaimNode → CommitNode (temporal proximity)
    "belongs_to_session",     # any → SessionNode
    "preceded_commit",        # VerdictNode → CommitNode
    "triggered_revision",     # VerdictNode → ClaimNode (when directive in revise set)
]


class Edge(BaseModel):
    """An untyped-value Pydantic edge.

    `kind` is the typed verb; `source` and `target` are opaque node IDs.
    The schema is strict on `kind` but lets node-ID type-checking happen
    in the graph (which knows the catalogue).
    """

    kind: EdgeKind
    source: str
    target: str
    metadata: dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────
# Graph container
# ─────────────────────────────────────────────────────────────────────────

class ReasoningMemoryGraph(BaseModel):
    """The unified graph view of pipeline-MCP telemetry.

    Mirrors the *three-memory-types-on-one-graph* design from Iusztin's
    article: short-term (sessions in progress, distilled into long-term),
    long-term (claims + verdicts + commits + tool calls), reasoning (the
    edges between them). All three live in one container; the separation
    is conceptual, not structural.
    """

    sessions: dict[str, SessionNode] = Field(default_factory=dict)
    claims: dict[str, ClaimNode] = Field(default_factory=dict)
    verdicts: dict[str, VerdictNode] = Field(default_factory=dict)
    commits: dict[str, CommitNode] = Field(default_factory=dict)
    tool_calls: dict[str, ToolCallNode] = Field(default_factory=dict)
    edges: list[Edge] = Field(default_factory=list)

    # convenience counters (computed at build time)
    built_at_iso: str = ""
    source_file_count: int = 0
    timeline_entry_count: int = 0

    # ── basic graph operations ──────────────────────────────────────

    def edges_of_kind(self, kind: EdgeKind) -> list[Edge]:
        return [e for e in self.edges if e.kind == kind]

    def neighbors(self, node_id: str, kind: Optional[EdgeKind] = None) -> list[str]:
        out: list[str] = []
        for e in self.edges:
            if kind is not None and e.kind != kind:
                continue
            if e.source == node_id:
                out.append(e.target)
            elif e.target == node_id:
                out.append(e.source)
        return out


# ─────────────────────────────────────────────────────────────────────────
# Builder
# ─────────────────────────────────────────────────────────────────────────

_GATE_TOOLS = {
    "phionyx_response_gate",
    "phionyx_verify_claim",
    "phionyx_verify_paths",
    "phionyx_causal_trace",
}

# Directives that the response_revision_gate emits as a non-pass verdict
# and that the assistant is expected to re-author against.
_REVISION_DIRECTIVES = {"damp", "rewrite", "regenerate", "reject"}


def build_from_telemetry(
    telemetry_dir: str | Path,
    git_root: Optional[str | Path] = None,
) -> ReasoningMemoryGraph:
    """Build the reasoning-memory graph from a telemetry directory.

    Reads every ``session_*.json`` under ``telemetry_dir`` and projects
    each timeline entry into the typed graph. Optional ``git_root`` is
    accepted for symmetry with future commit-enrichment passes; not used
    in the v0.7.1 baseline (commit_attestation entries carry their own
    SHA already).
    """
    tdir = Path(telemetry_dir)
    if not tdir.is_dir():
        return ReasoningMemoryGraph(
            built_at_iso=datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
            source_file_count=0,
            timeline_entry_count=0,
        )

    g = ReasoningMemoryGraph(
        built_at_iso=datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
    )

    session_files = sorted(tdir.glob("session_*.json"))
    g.source_file_count = len(session_files)

    for sf in session_files:
        try:
            payload = json.loads(sf.read_text())
        except Exception:
            # A corrupted session file should not break the whole build;
            # the failing file is silently skipped (counts as 0 entries).
            continue

        sid = str(payload.get("session_id") or sf.stem.replace("session_", ""))
        session = SessionNode(
            session_id=sid,
            started_iso=str(payload.get("session_start_iso", "")),
            last_update_iso=str(payload.get("last_update_iso", "")),
            call_count=int(payload.get("call_count", 0) or 0),
            claude_session_id=payload.get("claude_session_id"),
        )
        g.sessions[sid] = session

        for entry in payload.get("timeline", []) or []:
            g.timeline_entry_count += 1
            _ingest_entry(g, sid, entry)

    return g


def _ingest_entry(g: ReasoningMemoryGraph, sid: str, entry: dict) -> None:
    """Project a single timeline entry into the graph."""
    tool = str(entry.get("tool") or "")
    iso = str(entry.get("iso_time") or "")
    call_no = int(entry.get("call_number") or 0)

    # Gate-class tools → ClaimNode + VerdictNode
    if tool in _GATE_TOOLS:
        cid = f"{sid}::{call_no}"
        claim = ClaimNode(
            claim_id=cid,
            session_id=sid,
            call_number=call_no,
            iso_time=iso,
            tool=tool,
            evidence_type=_safe_str(entry.get("evidence_type")),
            confidence=_safe_float(entry.get("confidence")),
        )
        g.claims[cid] = claim

        directive = str(entry.get("directive") or "n/a")
        verdict = VerdictNode(
            verdict_id=cid,
            directive=directive,
            drift_severity=str(entry.get("drift_severity") or "none"),
            phi=_safe_float(entry.get("phi")),
            w_final=_safe_float(entry.get("w_final")),
        )
        g.verdicts[cid] = verdict

        g.edges.append(Edge(kind="produced_verdict", source=cid, target=cid))
        g.edges.append(Edge(kind="belongs_to_session", source=cid, target=sid))
        if claim.evidence_type:
            g.edges.append(
                Edge(
                    kind="had_evidence_type",
                    source=cid,
                    target=f"evidence_type::{claim.evidence_type}",
                )
            )
        if directive in _REVISION_DIRECTIVES:
            g.edges.append(
                Edge(
                    kind="triggered_revision",
                    source=cid,
                    target=cid,
                    metadata={"directive": directive},
                )
            )

    # Commit attestation → CommitNode
    elif tool == "commit_attestation":
        sha = str(entry.get("commit_sha") or "")
        if sha:
            commit = CommitNode(commit_sha=sha, session_id=sid, iso_time=iso)
            g.commits[sha] = commit
            g.edges.append(
                Edge(kind="belongs_to_session", source=sha, target=sid)
            )
            # Heuristic preceded_commit edge: the most recent verdict in
            # this session that fired before this commit and inside a
            # 5-minute window is treated as a precursor. Distance-bounded
            # so we don't link unrelated turns.
            precursor = _most_recent_verdict_before(g, sid, iso, max_age_sec=300)
            if precursor is not None:
                g.edges.append(
                    Edge(kind="preceded_commit", source=precursor.verdict_id, target=sha)
                )
                g.edges.append(
                    Edge(kind="led_to_commit", source=precursor.verdict_id, target=sha)
                )

    # mcp_tool_invocation → ToolCallNode
    elif tool == "mcp_tool_invocation":
        tcid = f"{sid}::{call_no}::tool"
        tc = ToolCallNode(
            tool_call_id=tcid,
            session_id=sid,
            iso_time=iso,
            mcp_tool_name=str(entry.get("mcp_tool_name") or ""),
            args_hash=_safe_str(entry.get("args_hash")),
        )
        g.tool_calls[tcid] = tc
        g.edges.append(Edge(kind="belongs_to_session", source=tcid, target=sid))


# ─────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────

def _safe_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _safe_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _parse_iso(iso: str) -> Optional[datetime]:
    """Parse an ISO timestamp into a tz-aware UTC datetime.

    Some telemetry entries carry tz suffixes (``+00:00``, ``Z``), some
    do not. We normalise everything to UTC-aware so downstream
    comparisons cannot raise the offset-naive/aware mixing TypeError.
    """
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _most_recent_verdict_before(
    g: ReasoningMemoryGraph, sid: str, iso: str, max_age_sec: int = 300
) -> Optional[VerdictNode]:
    """Walk session's verdicts and return the latest one strictly before
    `iso` and within `max_age_sec` seconds."""
    commit_dt = _parse_iso(iso)
    if commit_dt is None:
        return None
    best: Optional[VerdictNode] = None
    best_dt: Optional[datetime] = None
    for cid, claim in g.claims.items():
        if claim.session_id != sid:
            continue
        v = g.verdicts.get(cid)
        if v is None:
            continue
        dt = _parse_iso(claim.iso_time)
        if dt is None or dt >= commit_dt:
            continue
        if (commit_dt - dt).total_seconds() > max_age_sec:
            continue
        if best_dt is None or dt > best_dt:
            best = v
            best_dt = dt
    return best


# ─────────────────────────────────────────────────────────────────────────
# Canonical multi-hop queries (the 4 F-RM1 acceptance queries)
# ─────────────────────────────────────────────────────────────────────────

def query_evidence_type_pass_rate(g: ReasoningMemoryGraph) -> dict[str, dict]:
    """Q1 — *Which evidence_type most often produces a pass verdict?*

    Traversal: evidence_type ← had_evidence_type ← claim → produced_verdict
    → verdict (filter directive=pass).

    NOTE (2026-05-27): Current pipeline-MCP telemetry only persists the
    *output* of each gate call (directive, phi, w_final, trust, integrity)
    and not the *input* (claim text, evidence_type, evidence_count). Until
    the telemetry write is extended to capture evidence_type — which is a
    v0.8.0 candidate, tracked separately — this query returns an empty
    mapping. The query is kept in place (rather than removed) so the F-RM1
    panel can show "no data" *honestly*: the panel surfaces what the
    instrument can measure, and what it cannot.

    Returns a mapping ``{evidence_type: {pass_count, total, pass_rate}}``,
    typically empty against the current telemetry shape.
    """
    by_type: dict[str, list[str]] = defaultdict(list)
    for cid, claim in g.claims.items():
        if not claim.evidence_type:
            continue
        v = g.verdicts.get(cid)
        if v is None:
            continue
        by_type[claim.evidence_type].append(v.directive)
    result: dict[str, dict] = {}
    for et, dirs in by_type.items():
        total = len(dirs)
        pass_n = sum(1 for d in dirs if d == "pass")
        result[et] = {
            "pass_count": pass_n,
            "total": total,
            "pass_rate": round(pass_n / total, 3) if total else 0.0,
        }
    return result


def query_tool_pass_rate(g: ReasoningMemoryGraph) -> dict[str, dict]:
    """Q1' — *Which gate tool most often produces a pass verdict?*

    Pragmatic substitute for query_evidence_type_pass_rate while
    evidence_type is not yet persisted in telemetry. Uses
    ``claim.tool`` (the actual MCP tool name) as the grouping key.

    Returns a mapping ``{tool_name: {pass_count, total, pass_rate, directive_breakdown}}``.
    """
    by_tool: dict[str, list[str]] = defaultdict(list)
    for cid, claim in g.claims.items():
        v = g.verdicts.get(cid)
        if v is None:
            continue
        by_tool[claim.tool].append(v.directive)
    result: dict[str, dict] = {}
    for tool, dirs in by_tool.items():
        total = len(dirs)
        pass_n = sum(1 for d in dirs if d == "pass")
        breakdown: dict[str, int] = {}
        for d in dirs:
            breakdown[d] = breakdown.get(d, 0) + 1
        result[tool] = {
            "pass_count": pass_n,
            "total": total,
            "pass_rate": round(pass_n / total, 3) if total else 0.0,
            "directive_breakdown": breakdown,
        }
    return result


def query_phi_bucket_pass_rate(g: ReasoningMemoryGraph) -> dict[str, dict]:
    """Q1'' — *How does the pass rate vary across phi (φ) buckets?*

    Buckets: low (φ < 0.20), mid (0.20 ≤ φ < 0.40), high (φ ≥ 0.40).
    These ranges match the phi-collapse / phi-min thresholds discussed
    in `phionyx_core/pipeline/blocks/response_revision_gate.py`.

    Returns a mapping ``{bucket: {pass_count, total, pass_rate}}``.
    """
    def _bucket(phi: Optional[float]) -> str:
        if phi is None:
            return "unknown"
        if phi < 0.20:
            return "low"
        if phi < 0.40:
            return "mid"
        return "high"

    by_bucket: dict[str, list[str]] = defaultdict(list)
    for cid, claim in g.claims.items():
        v = g.verdicts.get(cid)
        if v is None:
            continue
        by_bucket[_bucket(v.phi)].append(v.directive)
    result: dict[str, dict] = {}
    for bucket, dirs in by_bucket.items():
        total = len(dirs)
        pass_n = sum(1 for d in dirs if d == "pass")
        result[bucket] = {
            "pass_count": pass_n,
            "total": total,
            "pass_rate": round(pass_n / total, 3) if total else 0.0,
        }
    return result


def query_commits_by_directive(g: ReasoningMemoryGraph) -> dict[str, dict]:
    """Q2 — *Which commits got the most non-pass directives?*

    Traversal: commit ← preceded_commit ← verdict (count by directive).
    A commit is linked here only if a verdict fired in the 5-minute
    window before the commit_attestation timestamp (see _most_recent_…).

    Returns ``{commit_sha: {<directive>: count, ...}}``.
    """
    by_commit: dict[str, Counter] = defaultdict(Counter)
    for e in g.edges_of_kind("preceded_commit"):
        v = g.verdicts.get(e.source)
        if v is None:
            continue
        by_commit[e.target][v.directive] += 1
    return {sha: dict(c) for sha, c in by_commit.items()}


def query_passed_despite_no_evidence(g: ReasoningMemoryGraph) -> list[dict]:
    """Q3 — *Which claims received a pass verdict despite no declared evidence_type?*

    Outlier query — surfaces gate-passes that the discipline says should
    have included an evidence taxonomy entry (claim_fixed / deploy paths
    in particular). Useful for tightening the rule over time.

    Returns a list of ``{claim_id, session_id, iso_time, tool, confidence}``.
    """
    out: list[dict] = []
    for cid, claim in g.claims.items():
        if claim.evidence_type:
            continue
        v = g.verdicts.get(cid)
        if v is None or v.directive != "pass":
            continue
        out.append(
            {
                "claim_id": cid,
                "session_id": claim.session_id,
                "iso_time": claim.iso_time,
                "tool": claim.tool,
                "confidence": claim.confidence,
            }
        )
    out.sort(key=lambda x: x["iso_time"])
    return out


def query_gate_to_commit_lag(g: ReasoningMemoryGraph) -> list[dict]:
    """Q4 — *For each commit, how long after the closest preceding gate call did it land?*

    Temporal query. Helps spot commits made without a recent gate
    invocation (the structural gap CLAUDE.md is trying to close).

    Returns a list of ``{commit_sha, gate_iso, commit_iso, lag_seconds,
    gate_directive}`` sorted by lag.
    """
    out: list[dict] = []
    for e in g.edges_of_kind("preceded_commit"):
        sha = e.target
        commit = g.commits.get(sha)
        v = g.verdicts.get(e.source)
        if commit is None or v is None:
            continue
        claim = g.claims.get(v.verdict_id)
        if claim is None:
            continue
        gate_dt = _parse_iso(claim.iso_time)
        commit_dt = _parse_iso(commit.iso_time)
        if gate_dt is None or commit_dt is None:
            continue
        lag = (commit_dt - gate_dt).total_seconds()
        out.append(
            {
                "commit_sha": sha,
                "gate_iso": claim.iso_time,
                "commit_iso": commit.iso_time,
                "lag_seconds": round(lag, 1),
                "gate_directive": v.directive,
            }
        )
    out.sort(key=lambda x: x["lag_seconds"])
    return out


__all__ = [
    "SessionNode",
    "ClaimNode",
    "VerdictNode",
    "CommitNode",
    "ToolCallNode",
    "Edge",
    "EdgeKind",
    "ReasoningMemoryGraph",
    "build_from_telemetry",
    "query_evidence_type_pass_rate",
    "query_tool_pass_rate",
    "query_phi_bucket_pass_rate",
    "query_commits_by_directive",
    "query_passed_despite_no_evidence",
    "query_gate_to_commit_lag",
]
