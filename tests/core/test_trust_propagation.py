"""
Tests for TrustNetwork — v4 §5 (AGI Layer 5)
==============================================
"""

import pytest
from phionyx_core.social.trust_propagation import (
    TrustNetwork,
    TrustEdge,
    TrustAssessment,
)


# ── Direct Trust ──

def test_add_trust():
    net = TrustNetwork()
    edge = net.add_trust("A", "B", 0.8)
    assert edge.trust_level == pytest.approx(0.8)

def test_get_direct_trust():
    net = TrustNetwork()
    net.add_trust("A", "B", 0.8)
    assert net.get_direct_trust("A", "B") == pytest.approx(0.8)

def test_self_trust():
    net = TrustNetwork()
    assert net.get_direct_trust("A", "A") == 1.0

def test_no_direct_trust():
    net = TrustNetwork()
    assert net.get_direct_trust("A", "B") is None

def test_update_trust_ema():
    net = TrustNetwork()
    net.add_trust("A", "B", 0.5)
    net.add_trust("A", "B", 0.8)
    # EMA: 0.3*0.8 + 0.7*0.5 = 0.59
    assert net.get_direct_trust("A", "B") == pytest.approx(0.59)

def test_trust_clamping():
    net = TrustNetwork()
    edge = net.add_trust("A", "B", 1.5)
    assert edge.trust_level == 1.0
    edge2 = net.add_trust("C", "D", -0.5)
    assert edge2.trust_level == 0.0


# ── Transitive Trust ──

def test_transitive_trust_chain():
    net = TrustNetwork(decay_factor=1.0)
    net.add_trust("A", "B", 0.8)
    net.add_trust("B", "C", 0.7)
    result = net.query_trust("A", "C")
    # 0.8 * 0.7 * 1.0 = 0.56
    assert result.transitive_trust == pytest.approx(0.56)

def test_transitive_trust_with_decay():
    net = TrustNetwork(decay_factor=0.9)
    net.add_trust("A", "B", 0.8)
    net.add_trust("B", "C", 0.7)
    result = net.query_trust("A", "C")
    # 0.8 * 0.9 * 0.7 * 0.9 = 0.4536
    assert result.transitive_trust == pytest.approx(0.4536)

def test_transitive_no_path():
    net = TrustNetwork()
    net.add_trust("A", "B", 0.8)
    result = net.query_trust("A", "C")
    assert result.transitive_trust == pytest.approx(0.0)
    assert result.is_trusted is False

def test_direct_overrides_transitive():
    net = TrustNetwork(decay_factor=0.5)
    net.add_trust("A", "B", 0.5)
    net.add_trust("B", "C", 0.5)
    net.add_trust("A", "C", 0.9)  # Direct is stronger
    result = net.query_trust("A", "C")
    assert result.transitive_trust >= 0.9


# ── Self Trust ──

def test_query_self():
    net = TrustNetwork()
    result = net.query_trust("A", "A")
    assert result.transitive_trust == 1.0
    assert result.is_trusted is True
    assert result.trust_path == ["A"]


# ── Trust Threshold ──

def test_is_trusted():
    net = TrustNetwork(trust_threshold=0.5)
    net.add_trust("A", "B", 0.8)
    assert net.query_trust("A", "B").is_trusted is True

def test_not_trusted():
    net = TrustNetwork(trust_threshold=0.5)
    net.add_trust("A", "B", 0.3)
    assert net.query_trust("A", "B").is_trusted is False


# ── Trust Path ──

def test_trust_path_recorded():
    net = TrustNetwork(decay_factor=1.0)
    net.add_trust("A", "B", 0.8)
    net.add_trust("B", "C", 0.7)
    result = net.query_trust("A", "C")
    assert result.trust_path == ["A", "B", "C"]


# ── Get Trusted Entities ──

def test_get_trusted_entities():
    net = TrustNetwork(trust_threshold=0.5, decay_factor=1.0)
    net.add_trust("A", "B", 0.9)
    net.add_trust("A", "C", 0.3)
    trusted = net.get_trusted_entities("A")
    names = [t[0] for t in trusted]
    assert "B" in names
    assert "C" not in names

def test_get_trusted_entities_empty():
    net = TrustNetwork()
    assert net.get_trusted_entities("A") == []


# ── Serialization ──

def test_get_trust_graph():
    net = TrustNetwork()
    net.add_trust("A", "B", 0.8, context="system")
    d = net.get_trust_graph()
    assert d["entity_count"] == 2
    assert len(d["edges"]) == 1
    assert d["edges"][0]["trust"] == pytest.approx(0.8)


# ── Reasoning ──

def test_reasoning_direct():
    net = TrustNetwork()
    net.add_trust("A", "B", 0.8)
    result = net.query_trust("A", "B")
    assert "Direct trust" in result.reasoning

def test_reasoning_transitive():
    net = TrustNetwork(decay_factor=1.0)
    net.add_trust("A", "B", 0.8)
    net.add_trust("B", "C", 0.7)
    result = net.query_trust("A", "C")
    assert "Transitive" in result.reasoning or "trust" in result.reasoning

def test_reasoning_no_path():
    net = TrustNetwork()
    result = net.query_trust("A", "Z")
    assert "No trust path" in result.reasoning


# ── Max Path Length ──

def test_max_path_length():
    net = TrustNetwork(decay_factor=1.0, max_path_length=2)
    net.add_trust("A", "B", 0.9)
    net.add_trust("B", "C", 0.9)
    net.add_trust("C", "D", 0.9)
    # Path A→B→C is 2 hops (OK), A→B→C→D is 3 hops (exceeds max)
    result = net.query_trust("A", "D")
    assert result.transitive_trust < 0.5  # Should not find full path
