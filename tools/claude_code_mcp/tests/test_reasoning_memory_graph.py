"""Tests for tools/claude_code_mcp/reasoning_memory_graph.py (v0.7.1 F-RM1).

These tests build a synthetic ReasoningMemoryGraph from a hand-rolled
session payload — no fixtures on disk, no dependency on the real
telemetry directory. The synthetic payload exercises every node type
and every edge type the module declares.
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

# tests-in-monorepo style
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reasoning_memory_graph import (  # noqa: E402
    Edge,
    ReasoningMemoryGraph,
    build_from_telemetry,
    query_commits_by_directive,
    query_evidence_type_pass_rate,
    query_gate_to_commit_lag,
    query_passed_despite_no_evidence,
    query_phi_bucket_pass_rate,
    query_tool_pass_rate,
)


# ── helpers ─────────────────────────────────────────────────────────

def _ts(iso: str) -> float:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def _session(timeline: list[dict], session_id: str = "test-session") -> dict:
    start_iso = "2026-05-26T13:48:00+00:00"
    return {
        "session_id": session_id,
        "session_start": _ts(start_iso),
        "session_start_iso": start_iso,
        "call_count": len(timeline),
        "last_update": timeline[-1]["timestamp"] if timeline else _ts(start_iso),
        "last_update_iso": (
            timeline[-1]["iso_time"] if timeline else start_iso
        ),
        "current_state": {},
        "current_phi": 0.0,
        "drift_metrics": {},
        "claims_total": 0,
        "timeline": timeline,
    }


def _gate_entry(call_number: int, iso: str, directive: str, phi: float = 0.30,
                evidence_type: str | None = None, tool: str = "phionyx_response_gate") -> dict:
    e: dict = {
        "call_number": call_number,
        "tool": tool,
        "timestamp": _ts(iso),
        "iso_time": iso,
        "directive": directive,
        "drift_severity": "none",
        "phi": phi,
        "w_final": 0.65,
    }
    if evidence_type is not None:
        e["evidence_type"] = evidence_type
    return e


def _commit_entry(call_number: int, iso: str, sha: str) -> dict:
    return {
        "call_number": call_number,
        "tool": "commit_attestation",
        "timestamp": _ts(iso),
        "iso_time": iso,
        "directive": "auto_attest",
        "drift_severity": "none",
        "commit_sha": sha,
    }


def _write_telemetry(payloads: list[dict], tmp: Path) -> Path:
    tdir = tmp / "mcp_telemetry"
    tdir.mkdir(parents=True, exist_ok=True)
    for p in payloads:
        f = tdir / f"session_{p['session_id']}.json"
        f.write_text(json.dumps(p))
    return tdir


# ── tests ──────────────────────────────────────────────────────────

def test_build_empty_when_directory_missing():
    g = build_from_telemetry("/no/such/dir/xyz")
    assert g.timeline_entry_count == 0
    assert g.source_file_count == 0
    assert len(g.sessions) == 0


def test_build_basic_graph_shape():
    """One session with 2 gate calls + 1 commit → expected node/edge counts."""
    payload = _session(
        [
            _gate_entry(1, "2026-05-26T14:00:00+00:00", "pass"),
            _gate_entry(2, "2026-05-26T14:01:00+00:00", "regenerate"),
            _commit_entry(3, "2026-05-26T14:02:00+00:00", "abc1234"),
        ],
        session_id="sess-a",
    )
    with tempfile.TemporaryDirectory() as tmp:
        tdir = _write_telemetry([payload], Path(tmp))
        g = build_from_telemetry(tdir)

    assert len(g.sessions) == 1
    assert len(g.claims) == 2
    assert len(g.verdicts) == 2
    assert len(g.commits) == 1

    # Two produced_verdict edges (one per claim)
    assert len(g.edges_of_kind("produced_verdict")) == 2
    # Two belongs_to_session edges from claims + 1 from commit = 3
    assert len(g.edges_of_kind("belongs_to_session")) == 3
    # The regenerate verdict produced a triggered_revision edge
    assert len(g.edges_of_kind("triggered_revision")) == 1
    # The commit followed a gate call within 5 min → preceded_commit + led_to_commit
    assert len(g.edges_of_kind("preceded_commit")) == 1
    assert len(g.edges_of_kind("led_to_commit")) == 1


def test_commit_outside_5min_window_not_linked():
    """A commit emitted >5min after any gate call doesn't get linked."""
    payload = _session(
        [
            _gate_entry(1, "2026-05-26T14:00:00+00:00", "pass"),
            # 6 minutes later
            _commit_entry(2, "2026-05-26T14:06:00+00:00", "deadbeef"),
        ],
        session_id="sess-b",
    )
    with tempfile.TemporaryDirectory() as tmp:
        tdir = _write_telemetry([payload], Path(tmp))
        g = build_from_telemetry(tdir)
    assert len(g.commits) == 1
    assert len(g.edges_of_kind("preceded_commit")) == 0
    assert len(g.edges_of_kind("led_to_commit")) == 0


def test_query_tool_pass_rate():
    """Tool-level pass rate counts directives per tool."""
    payload = _session(
        [
            _gate_entry(1, "2026-05-26T14:00:00+00:00", "pass", tool="phionyx_response_gate"),
            _gate_entry(2, "2026-05-26T14:01:00+00:00", "pass", tool="phionyx_response_gate"),
            _gate_entry(3, "2026-05-26T14:02:00+00:00", "reject", tool="phionyx_verify_claim"),
            _gate_entry(4, "2026-05-26T14:03:00+00:00", "regenerate", tool="phionyx_verify_claim"),
            _gate_entry(5, "2026-05-26T14:04:00+00:00", "pass", tool="phionyx_verify_claim"),
        ],
        session_id="sess-c",
    )
    with tempfile.TemporaryDirectory() as tmp:
        tdir = _write_telemetry([payload], Path(tmp))
        g = build_from_telemetry(tdir)
    out = query_tool_pass_rate(g)
    assert out["phionyx_response_gate"]["total"] == 2
    assert out["phionyx_response_gate"]["pass_count"] == 2
    assert out["phionyx_response_gate"]["pass_rate"] == 1.0
    assert out["phionyx_verify_claim"]["total"] == 3
    assert out["phionyx_verify_claim"]["pass_count"] == 1
    assert out["phionyx_verify_claim"]["pass_rate"] == round(1 / 3, 3)
    # Breakdown carries every directive
    assert out["phionyx_verify_claim"]["directive_breakdown"] == {
        "reject": 1, "regenerate": 1, "pass": 1,
    }


def test_query_phi_bucket_pass_rate():
    """Phi buckets: low <0.20, mid <0.40, high ≥0.40."""
    payload = _session(
        [
            _gate_entry(1, "2026-05-26T14:00:00+00:00", "regenerate", phi=0.10),  # low
            _gate_entry(2, "2026-05-26T14:01:00+00:00", "pass", phi=0.30),        # mid
            _gate_entry(3, "2026-05-26T14:02:00+00:00", "pass", phi=0.50),        # high
            _gate_entry(4, "2026-05-26T14:03:00+00:00", "reject", phi=0.50),      # high
        ],
        session_id="sess-d",
    )
    with tempfile.TemporaryDirectory() as tmp:
        tdir = _write_telemetry([payload], Path(tmp))
        g = build_from_telemetry(tdir)
    out = query_phi_bucket_pass_rate(g)
    assert out["low"]["pass_rate"] == 0.0
    assert out["mid"]["pass_rate"] == 1.0
    assert out["high"]["pass_rate"] == 0.5


def test_query_evidence_type_pass_rate_empty_when_not_persisted():
    """Current telemetry shape doesn't persist evidence_type — Q1 returns empty.

    This is documented behaviour: the query is preserved so the panel can
    *honestly* show "no data" rather than fabricating one.
    """
    payload = _session(
        [_gate_entry(1, "2026-05-26T14:00:00+00:00", "pass")],
        session_id="sess-e",
    )
    with tempfile.TemporaryDirectory() as tmp:
        tdir = _write_telemetry([payload], Path(tmp))
        g = build_from_telemetry(tdir)
    assert query_evidence_type_pass_rate(g) == {}


def test_query_evidence_type_pass_rate_works_when_field_populated():
    """If/when telemetry starts persisting evidence_type, the query works."""
    payload = _session(
        [
            _gate_entry(1, "2026-05-26T14:00:00+00:00", "pass", evidence_type="unit_test"),
            _gate_entry(2, "2026-05-26T14:01:00+00:00", "pass", evidence_type="unit_test"),
            _gate_entry(3, "2026-05-26T14:02:00+00:00", "reject", evidence_type="none"),
        ],
        session_id="sess-f",
    )
    with tempfile.TemporaryDirectory() as tmp:
        tdir = _write_telemetry([payload], Path(tmp))
        g = build_from_telemetry(tdir)
    out = query_evidence_type_pass_rate(g)
    assert out["unit_test"]["pass_rate"] == 1.0
    assert out["none"]["pass_rate"] == 0.0


def test_query_commits_by_directive():
    """Each commit links to the closest preceding verdict's directive."""
    payload = _session(
        [
            _gate_entry(1, "2026-05-26T14:00:00+00:00", "pass"),
            _commit_entry(2, "2026-05-26T14:01:00+00:00", "sha1111"),
            _gate_entry(3, "2026-05-26T14:02:00+00:00", "regenerate"),
            _commit_entry(4, "2026-05-26T14:03:00+00:00", "sha2222"),
        ],
        session_id="sess-g",
    )
    with tempfile.TemporaryDirectory() as tmp:
        tdir = _write_telemetry([payload], Path(tmp))
        g = build_from_telemetry(tdir)
    out = query_commits_by_directive(g)
    assert out["sha1111"] == {"pass": 1}
    assert out["sha2222"] == {"regenerate": 1}


def test_query_passed_despite_no_evidence():
    """Outliers: pass verdict + missing evidence_type."""
    payload = _session(
        [
            _gate_entry(1, "2026-05-26T14:00:00+00:00", "pass"),  # no evidence_type → outlier
            _gate_entry(2, "2026-05-26T14:01:00+00:00", "pass", evidence_type="unit_test"),  # not outlier
            _gate_entry(3, "2026-05-26T14:02:00+00:00", "reject"),  # not pass → not outlier
        ],
        session_id="sess-h",
    )
    with tempfile.TemporaryDirectory() as tmp:
        tdir = _write_telemetry([payload], Path(tmp))
        g = build_from_telemetry(tdir)
    outliers = query_passed_despite_no_evidence(g)
    assert len(outliers) == 1
    assert outliers[0]["claim_id"].endswith("::1")


def test_query_gate_to_commit_lag():
    """Lag is computed in seconds; sorted ascending."""
    payload = _session(
        [
            _gate_entry(1, "2026-05-26T14:00:00+00:00", "pass"),
            _commit_entry(2, "2026-05-26T14:00:30+00:00", "fastsha"),  # 30s lag
            _gate_entry(3, "2026-05-26T14:01:00+00:00", "pass"),
            _commit_entry(4, "2026-05-26T14:03:00+00:00", "slowsha"),  # 120s lag
        ],
        session_id="sess-i",
    )
    with tempfile.TemporaryDirectory() as tmp:
        tdir = _write_telemetry([payload], Path(tmp))
        g = build_from_telemetry(tdir)
    out = query_gate_to_commit_lag(g)
    assert [r["commit_sha"] for r in out] == ["fastsha", "slowsha"]
    assert out[0]["lag_seconds"] == 30.0
    assert out[1]["lag_seconds"] == 120.0


def test_real_telemetry_smoke():
    """The module builds against real on-disk telemetry without raising.

    Skips silently if the telemetry directory is empty (CI environment).
    """
    real_dir = Path(__file__).resolve().parents[3] / "data" / "mcp_telemetry"
    if not real_dir.is_dir():
        return
    g = build_from_telemetry(real_dir)
    # Just confirm the build did not raise and returns a typed object.
    assert isinstance(g, ReasoningMemoryGraph)
    assert g.source_file_count >= 0
    assert g.timeline_entry_count >= 0
    # Every node has the right type
    for s in g.sessions.values():
        assert s.session_id
    for c in g.claims.values():
        assert c.tool
    for v in g.verdicts.values():
        assert v.directive
