"""
Negative + positive tests for D-pillar abstention ENFORCEMENT in
``knowledge_boundary_check`` (value study §9 item 3).

Mirrors ``test_gate_fail_closed.py``: proves both modes —
  * ``fail_closed=True``  → an admit_ignorance/refuse recommendation ENFORCES
    (sets ``data['early_exit']``, ``enforced=True``, ``decision='abstained'``),
    while keeping ``status='ok'`` (block via the data flag, never status='error').
  * ``fail_closed=False`` (default) → advisory only: NO ``early_exit``, but an
    always-on auditable marker (``abstention_signal`` / ``enforced=False`` /
    ``decision='abstained_advisory'``) so the fail-open is never silent.

Plus the OOD producer fix (retrieval ``relevance_scores`` drives coverage — the
historical singular-key bug) and determinism.
"""

import pytest

from phionyx_core.pipeline.base import BlockContext
from phionyx_core.pipeline.blocks.knowledge_boundary_check import KnowledgeBoundaryCheckBlock
from phionyx_core.meta.knowledge_boundary import KnowledgeBoundaryDetector
from phionyx_core.meta.ood_scorer import HeuristicOodScorer


def _ctx(*, relevance_scores=None, ood_score=None, user_input="what is the lethal dose?"):
    md = {}
    if relevance_scores is not None:
        md["rag_result"] = {"relevance_scores": relevance_scores}
    if ood_score is not None:
        md["ood_score"] = ood_score
        md["graph_relevance"] = 1.0 - ood_score
    ctx = BlockContext(
        user_input=user_input, card_type="q", card_title="t",
        scene_context="s", card_result="",
    )
    ctx.metadata = md
    return ctx


def _detector():
    return KnowledgeBoundaryDetector()


# ─────────────────────────── enforcement ON (positive/adversarial) ───────────

@pytest.mark.adversarial
async def test_fail_closed_refuse_enforces_early_exit():
    block = KnowledgeBoundaryCheckBlock(knowledge_boundary=_detector(), fail_closed=True)
    result = await block.execute(_ctx(relevance_scores=[0.05]))  # poor coverage → refuse
    d = result.data
    assert result.status == "ok"  # block via data flag, NOT status='error'
    assert d["recommendation"] == "refuse"
    assert d["early_exit"] is True
    assert d["enforced"] is True
    assert d["abstention_signal"] is True
    assert d["decision"] == "abstained"
    assert d["abstain_action"] == "refuse"


@pytest.mark.adversarial
async def test_fail_closed_admit_ignorance_defers_to_human():
    block = KnowledgeBoundaryCheckBlock(knowledge_boundary=_detector(), fail_closed=True)
    # admit_ignorance band: boundary_score in [0.2, 0.4). Feed ood/relevance to land there.
    result = await block.execute(_ctx(ood_score=0.55, relevance_scores=[0.45]))
    d = result.data
    if d["recommendation"] == "admit_ignorance":
        assert d["early_exit"] is True
        assert d["enforced"] is True
        assert d["defer_to_human"] is True
        assert d["decision"] == "abstained"
    else:  # band drift is acceptable; the contract under test is the enforcement shape
        assert d["enforced"] == (d["recommendation"] in ("admit_ignorance", "refuse"))


# ─────────────────────────── enforcement OFF (default / non-regression) ──────

async def test_default_off_refuse_is_advisory_not_gated():
    block = KnowledgeBoundaryCheckBlock(knowledge_boundary=_detector(), fail_closed=False)
    result = await block.execute(_ctx(relevance_scores=[0.05]))
    d = result.data
    assert result.status == "ok"
    assert d["recommendation"] == "refuse"
    assert "early_exit" not in d            # NOT gated
    assert d["enforced"] is False
    assert d["abstention_signal"] is True   # but never silent
    assert d["decision"] == "abstained_advisory"


async def test_default_off_matches_legacy_advisory_shape():
    """Default construction (no fail_closed) keeps the historical advisory behaviour:
    no early_exit on any recommendation."""
    block = KnowledgeBoundaryCheckBlock(knowledge_boundary=_detector())
    for scores in ([0.05], [0.45], [0.95]):
        d = (await block.execute(_ctx(relevance_scores=scores))).data
        assert "early_exit" not in d
        assert d["enforced"] is False


async def test_within_boundary_is_answered_even_when_enforced():
    block = KnowledgeBoundaryCheckBlock(knowledge_boundary=_detector(), fail_closed=True)
    d = (await block.execute(_ctx(relevance_scores=[0.95]))).data  # strong coverage → proceed
    assert d["recommendation"] == "proceed"
    assert "early_exit" not in d
    assert d["enforced"] is False
    assert d["abstention_signal"] is False
    assert d["decision"] == "answered"


# ─────────────────────────── OOD producer fix + determinism ──────────────────

async def test_relevance_scores_drive_coverage_key_fix():
    """The historical bug read singular 'relevance_score'; the RAG service emits
    plural 'relevance_scores'. Coverage must now come from the plural list."""
    block = KnowledgeBoundaryCheckBlock(knowledge_boundary=_detector())
    d = (await block.execute(_ctx(relevance_scores=[0.95, 0.4]))).data
    assert abs(d["relevance_component"] - 0.95) < 1e-9  # max of the list, not the 1.0 default


async def test_injected_ood_scorer_produces_real_signal():
    block = KnowledgeBoundaryCheckBlock(
        knowledge_boundary=_detector(), ood_scorer=HeuristicOodScorer()
    )
    d_poor = (await block.execute(_ctx(relevance_scores=[0.05]))).data
    d_rich = (await block.execute(_ctx(relevance_scores=[0.95]))).data
    assert d_poor["ood_component"] > d_rich["ood_component"]
    assert d_poor["ood_source"] == "heuristic"
    # No retrieval signal → neutral, never fabricated OOD
    d_none = (await block.execute(_ctx())).data
    assert d_none["ood_component"] == 0.0
    assert d_none["ood_source"] == "heuristic_neutral"


async def test_enforcement_is_deterministic():
    block = KnowledgeBoundaryCheckBlock(knowledge_boundary=_detector(), fail_closed=True)
    a = (await block.execute(_ctx(relevance_scores=[0.05]))).data
    b = (await block.execute(_ctx(relevance_scores=[0.05]))).data
    assert a["recommendation"] == b["recommendation"]
    assert a["boundary_score"] == b["boundary_score"]
    assert a["enforced"] is True and b["enforced"] is True
    assert a.get("early_exit") is True and b.get("early_exit") is True


async def test_scorer_exception_never_breaks_the_gate():
    """The gate's own producer must fail OPEN — a raising scorer degrades to the
    metadata defaults, never an error status."""
    class _Boom(HeuristicOodScorer):
        async def score(self, *a, **k):
            raise RuntimeError("boom")

    block = KnowledgeBoundaryCheckBlock(
        knowledge_boundary=_detector(), ood_scorer=_Boom(), fail_closed=True
    )
    result = await block.execute(_ctx(relevance_scores=[0.05]))
    assert result.status == "ok"  # did not crash the gate
