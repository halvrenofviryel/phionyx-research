"""
AGI Sprint Pipeline Blocks — Unit Tests
=========================================

Tests for 11 new pipeline blocks binding AGI sprint modules (S2-S5)
to the pipeline execution framework.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from phionyx_core.pipeline.base import BlockContext, BlockResult


def make_context(**kwargs):
    """Create a test BlockContext with defaults."""
    defaults = {
        "user_input": "test input",
        "card_type": "story",
        "card_title": "Test",
        "scene_context": "test scene",
        "card_result": "",
        "session_id": "test-session",
        "mode": "story",
    }
    defaults.update(kwargs)
    return BlockContext(**defaults)


# ─── S2: Self-Model Assessment ────────────────────────────────

class TestSelfModelAssessmentBlock:
    async def test_skip_when_no_module(self):
        from phionyx_core.pipeline.blocks.self_model_assessment import SelfModelAssessmentBlock
        block = SelfModelAssessmentBlock(self_model=None)
        result = await block.execute(make_context())
        assert result.status == "skipped"

    async def test_success_can_do(self):
        from phionyx_core.pipeline.blocks.self_model_assessment import SelfModelAssessmentBlock
        mock_model = MagicMock()
        assessment = MagicMock()
        assessment.can_do = True
        assessment.confidence = 0.9
        assessment.status = MagicMock(value="AVAILABLE")
        assessment.limitations = []
        assessment.reasoning = "Capable"
        mock_model.can_i_do.return_value = assessment
        report = MagicMock()
        report.capabilities_available = 5
        report.capabilities_degraded = 0
        report.capabilities_unavailable = 0
        report.confidence_mean = 0.9
        mock_model.get_report.return_value = report

        block = SelfModelAssessmentBlock(self_model=mock_model)
        result = await block.execute(make_context())
        assert result.status == "ok"
        assert result.data["can_do"] is True
        assert result.data["confidence"] == 0.9

    async def test_error_handling(self):
        from phionyx_core.pipeline.blocks.self_model_assessment import SelfModelAssessmentBlock
        mock_model = MagicMock()
        mock_model.can_i_do.side_effect = RuntimeError("test error")
        block = SelfModelAssessmentBlock(self_model=mock_model)
        result = await block.execute(make_context())
        assert result.status == "error"


# ─── S2: Knowledge Boundary Check ─────────────────────────────

class TestKnowledgeBoundaryCheckBlock:
    async def test_inline_fallback_when_no_module(self):
        from phionyx_core.pipeline.blocks.knowledge_boundary_check import KnowledgeBoundaryCheckBlock
        block = KnowledgeBoundaryCheckBlock(knowledge_boundary=None)
        result = await block.execute(make_context())
        assert result.status == "ok"
        assert "Inline heuristic" in result.data.get("reasoning", "")

    async def test_success_within_boundary(self):
        from phionyx_core.pipeline.blocks.knowledge_boundary_check import KnowledgeBoundaryCheckBlock
        mock_kb = MagicMock()
        assessment = MagicMock()
        assessment.within_boundary = True
        assessment.boundary_score = 0.8
        assessment.ood_component = 0.1
        assessment.relevance_component = 0.9
        assessment.novelty_component = 0.2
        assessment.recommendation = "proceed"
        assessment.reasoning = "Within boundary"
        mock_kb.assess.return_value = assessment

        block = KnowledgeBoundaryCheckBlock(knowledge_boundary=mock_kb)
        result = await block.execute(make_context())
        assert result.status == "ok"
        assert result.data["within_boundary"] is True
        assert result.data["recommendation"] == "proceed"

    async def test_error_handling(self):
        from phionyx_core.pipeline.blocks.knowledge_boundary_check import KnowledgeBoundaryCheckBlock
        mock_kb = MagicMock()
        mock_kb.assess.side_effect = RuntimeError("test error")
        block = KnowledgeBoundaryCheckBlock(knowledge_boundary=mock_kb)
        result = await block.execute(make_context())
        assert result.status == "error"


# ─── S2: Memory Consolidation ─────────────────────────────────

class TestMemoryConsolidationBlock:
    async def test_skip_when_no_module(self):
        from phionyx_core.pipeline.blocks.memory_consolidation_block import MemoryConsolidationBlock
        block = MemoryConsolidationBlock(memory_consolidator=None)
        result = await block.execute(make_context())
        assert result.status == "skipped"

    async def test_skip_non_interval_turn(self):
        from phionyx_core.pipeline.blocks.memory_consolidation_block import MemoryConsolidationBlock
        mock_cons = MagicMock()
        block = MemoryConsolidationBlock(memory_consolidator=mock_cons, consolidation_interval=5)
        # First turn (1 % 5 != 0)
        result = await block.execute(make_context())
        assert result.status == "ok"
        assert result.data["consolidation_run"] is False

    async def test_success_consolidation(self):
        from phionyx_core.pipeline.blocks.memory_consolidation_block import MemoryConsolidationBlock
        mock_cons = MagicMock()
        cons_result = MagicMock()
        cons_result.consolidated_count = 3
        cons_result.promoted_count = 1
        cons_result.decayed_count = 2
        cons_result.candidates = [MagicMock()]
        cons_result.timestamp = "2026-03-19T00:00:00Z"
        mock_cons.consolidate.return_value = cons_result

        block = MemoryConsolidationBlock(memory_consolidator=mock_cons, consolidation_interval=1)
        ctx = make_context()
        ctx.metadata = {"memories": [{"content": "test", "memory_type": "episodic"}]}
        result = await block.execute(ctx)
        assert result.status == "ok"
        assert result.data["consolidation_run"] is True
        assert result.data["consolidated_count"] == 3

    async def test_error_handling(self):
        from phionyx_core.pipeline.blocks.memory_consolidation_block import MemoryConsolidationBlock
        mock_cons = MagicMock()
        mock_cons.consolidate.side_effect = RuntimeError("test error")
        block = MemoryConsolidationBlock(memory_consolidator=mock_cons, consolidation_interval=1)
        ctx = make_context()
        ctx.metadata = {"memories": [{"content": "test"}]}
        result = await block.execute(ctx)
        assert result.status == "error"


# ─── S3: Causal Graph Update ──────────────────────────────────

class TestCausalGraphUpdateBlock:
    async def test_skip_when_no_module(self):
        from phionyx_core.pipeline.blocks.causal_graph_update import CausalGraphUpdateBlock
        block = CausalGraphUpdateBlock(causal_graph_builder=None)
        result = await block.execute(make_context())
        assert result.status == "skipped"

    async def test_success_with_physics(self):
        from phionyx_core.pipeline.blocks.causal_graph_update import CausalGraphUpdateBlock
        mock_builder = MagicMock()
        graph = MagicMock()
        graph.node_count = 8
        graph.edge_count = 6
        mock_builder.build.return_value = graph
        mock_builder.to_world_state_dict.return_value = {"nodes": {}, "edges": {}}

        block = CausalGraphUpdateBlock(causal_graph_builder=mock_builder)
        ctx = make_context()
        ctx.metadata = {
            "physics_state": {"entropy": 0.4, "valence": 0.3, "arousal": 0.6},
            "phi_result": {"phi_total": 0.7},
            "entropy_result": {"dynamic_entropy": 0.4},
        }
        result = await block.execute(ctx)
        assert result.status == "ok"
        assert result.data["node_count"] == 8
        mock_builder.add_physics_variables.assert_called_once()
        # With 4 variables (phi, entropy, valence, arousal) available,
        # pairs that have both values present are observed
        assert mock_builder.observe_co_occurrence.call_count >= 2

    async def test_error_handling(self):
        from phionyx_core.pipeline.blocks.causal_graph_update import CausalGraphUpdateBlock
        mock_builder = MagicMock()
        mock_builder.add_physics_variables.side_effect = RuntimeError("test error")
        block = CausalGraphUpdateBlock(causal_graph_builder=mock_builder)
        ctx = make_context()
        ctx.metadata = {"physics_state": {"entropy": 0.4}}
        result = await block.execute(ctx)
        assert result.status == "error"


# ─── S3: Causal Intervention ──────────────────────────────────

class TestCausalInterventionBlock:
    async def test_skip_when_no_module(self):
        from phionyx_core.pipeline.blocks.causal_intervention_block import CausalInterventionBlock
        block = CausalInterventionBlock(intervention_model=None)
        result = await block.execute(make_context())
        assert result.status == "skipped"

    async def test_no_intervention_normal_strategy(self):
        from phionyx_core.pipeline.blocks.causal_intervention_block import CausalInterventionBlock
        mock_model = MagicMock()
        block = CausalInterventionBlock(intervention_model=mock_model)
        ctx = make_context()
        ctx.strategy = "normal"
        result = await block.execute(ctx)
        assert result.status == "ok"
        assert result.data["intervention_applied"] is False

    async def test_success_stabilize_strategy(self):
        from phionyx_core.pipeline.blocks.causal_intervention_block import CausalInterventionBlock
        mock_model = MagicMock()
        int_result = MagicMock()
        int_result.original_value = 0.7
        int_result.intervention_value = 0.3
        int_result.total_nodes_affected = 3
        mock_model.simulate_multiple.return_value = {"entropy": int_result}

        block = CausalInterventionBlock(intervention_model=mock_model)
        ctx = make_context()
        ctx.strategy = "stabilize"
        result = await block.execute(ctx)
        assert result.status == "ok"
        assert result.data["intervention_applied"] is True
        assert result.data["strategy"] == "stabilize"

    async def test_error_handling(self):
        from phionyx_core.pipeline.blocks.causal_intervention_block import CausalInterventionBlock
        mock_model = MagicMock()
        mock_model.simulate_multiple.side_effect = RuntimeError("test error")
        block = CausalInterventionBlock(intervention_model=mock_model)
        ctx = make_context()
        ctx.strategy = "stabilize"
        result = await block.execute(ctx)
        assert result.status == "error"


# ─── S4: Counterfactual Analysis ──────────────────────────────

class TestCounterfactualAnalysisBlock:
    async def test_skip_when_no_module(self):
        from phionyx_core.pipeline.blocks.counterfactual_analysis import CounterfactualAnalysisBlock
        block = CounterfactualAnalysisBlock(counterfactual_engine=None)
        result = await block.execute(make_context())
        assert result.status == "skipped"

    async def test_no_run_without_drift(self):
        from phionyx_core.pipeline.blocks.counterfactual_analysis import CounterfactualAnalysisBlock
        mock_engine = MagicMock()
        block = CounterfactualAnalysisBlock(counterfactual_engine=mock_engine)
        result = await block.execute(make_context())
        assert result.status == "ok"
        assert result.data["counterfactual_run"] is False

    async def test_success_with_drift(self):
        from phionyx_core.pipeline.blocks.counterfactual_analysis import CounterfactualAnalysisBlock
        mock_engine = MagicMock()
        outcome = MagicMock()
        outcome.variable = "phi"
        outcome.factual_value = 0.3
        outcome.counterfactual_value = 0.6
        outcome.delta = 0.3
        cf_result = MagicMock()
        cf_result.outcomes = [outcome]
        cf_result.reasoning = "Entropy was too high"
        mock_engine.what_if.return_value = cf_result

        block = CounterfactualAnalysisBlock(counterfactual_engine=mock_engine)
        ctx = make_context()
        ctx.metadata = {
            "drift_result": {"drift_detected": True},
            "physics_state": {"entropy": 0.8},
        }
        result = await block.execute(ctx)
        assert result.status == "ok"
        assert result.data["counterfactual_run"] is True
        assert len(result.data["outcomes"]) == 1

    async def test_error_handling(self):
        from phionyx_core.pipeline.blocks.counterfactual_analysis import CounterfactualAnalysisBlock
        mock_engine = MagicMock()
        mock_engine.what_if.side_effect = RuntimeError("test error")
        block = CounterfactualAnalysisBlock(counterfactual_engine=mock_engine)
        ctx = make_context()
        ctx.metadata = {"drift_result": {"drift_detected": True}, "physics_state": {}}
        result = await block.execute(ctx)
        assert result.status == "error"


# ─── S4: Root Cause Analysis ──────────────────────────────────

class TestRootCauseAnalysisBlock:
    async def test_skip_when_no_module(self):
        from phionyx_core.pipeline.blocks.root_cause_analysis import RootCauseAnalysisBlock
        block = RootCauseAnalysisBlock(root_cause_analyzer=None)
        result = await block.execute(make_context())
        assert result.status == "skipped"

    async def test_no_run_without_anomaly(self):
        from phionyx_core.pipeline.blocks.root_cause_analysis import RootCauseAnalysisBlock
        mock_analyzer = MagicMock()
        block = RootCauseAnalysisBlock(root_cause_analyzer=mock_analyzer)
        ctx = make_context()
        ctx.metadata = {"physics_state": {"entropy": 0.4}}
        result = await block.execute(ctx)
        assert result.status == "ok"
        assert result.data["analysis_run"] is False

    async def test_success_high_entropy(self):
        from phionyx_core.pipeline.blocks.root_cause_analysis import RootCauseAnalysisBlock
        mock_analyzer = MagicMock()
        candidate = MagicMock()
        candidate.node_id = "valence"
        candidate.name = "valence"
        candidate.likelihood = 0.85
        candidate.causal_path = ["valence", "entropy"]
        candidate.current_value = -0.5
        analysis = MagicMock()
        analysis.candidates = [candidate]
        analysis.top_cause = candidate
        analysis.reasoning = "Low valence caused high entropy"
        mock_analyzer.analyze.return_value = analysis

        block = RootCauseAnalysisBlock(root_cause_analyzer=mock_analyzer)
        ctx = make_context()
        ctx.metadata = {"physics_state": {"entropy": 0.9}}
        result = await block.execute(ctx)
        assert result.status == "ok"
        assert result.data["analysis_run"] is True
        assert result.data["anomaly_node"] == "entropy"
        assert result.data["top_cause"]["node_id"] == "valence"

    async def test_error_handling(self):
        from phionyx_core.pipeline.blocks.root_cause_analysis import RootCauseAnalysisBlock
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.side_effect = RuntimeError("test error")
        block = RootCauseAnalysisBlock(root_cause_analyzer=mock_analyzer)
        ctx = make_context()
        ctx.metadata = {"physics_state": {"entropy": 0.9}}
        result = await block.execute(ctx)
        assert result.status == "error"


# ─── S4: Causal Simulation ────────────────────────────────────

class TestCausalSimulationBlock:
    async def test_skip_when_no_module(self):
        from phionyx_core.pipeline.blocks.causal_simulation import CausalSimulationBlock
        block = CausalSimulationBlock(causal_simulator=None)
        result = await block.execute(make_context())
        assert result.status == "skipped"

    async def test_success_with_intervention(self):
        from phionyx_core.pipeline.blocks.causal_simulation import CausalSimulationBlock
        mock_sim = MagicMock()
        mock_sim.preview_risk.return_value = {"overall_risk": "low", "details": {}}
        sim_result = MagicMock()
        sim_result.total_variables_affected = 4
        sim_result.final_state = {"entropy": 0.3, "phi": 0.6}
        mock_sim.simulate_step.return_value = sim_result

        block = CausalSimulationBlock(causal_simulator=mock_sim)
        ctx = make_context()
        ctx.metadata = {
            "causal_intervention": {
                "intervention_applied": True,
                "interventions": {"entropy": {"new_value": 0.3}},
            }
        }
        result = await block.execute(ctx)
        assert result.status == "ok"
        assert result.data["simulation_run"] is True
        assert result.data["risk_level"] == "low"

    async def test_error_handling(self):
        from phionyx_core.pipeline.blocks.causal_simulation import CausalSimulationBlock
        mock_sim = MagicMock()
        mock_sim.preview_risk.side_effect = RuntimeError("test error")
        block = CausalSimulationBlock(causal_simulator=mock_sim)
        ctx = make_context()
        ctx.metadata = {"causal_intervention": {"intervention_applied": True, "interventions": {"entropy": {"new_value": 0.3}}}}
        result = await block.execute(ctx)
        assert result.status == "error"


# ─── S5: Trust Evaluation ─────────────────────────────────────

class TestTrustEvaluationBlock:
    async def test_inline_fallback_when_no_module(self):
        from phionyx_core.pipeline.blocks.trust_evaluation import TrustEvaluationBlock
        block = TrustEvaluationBlock(trust_network=None)
        result = await block.execute(make_context())
        assert result.status == "ok"
        assert "direct_trust" in result.data

    async def test_success(self):
        from phionyx_core.pipeline.blocks.trust_evaluation import TrustEvaluationBlock
        mock_net = MagicMock()
        assessment = MagicMock()
        assessment.direct_trust = 0.8
        assessment.transitive_trust = 0.75
        assessment.is_trusted = True
        assessment.trust_path = ["phionyx_system", "test-session"]
        assessment.reasoning = "Trusted"
        mock_net.query_trust.return_value = assessment
        mock_net.get_trusted_entities.return_value = [("test-session", 0.8)]
        mock_net.add_trust.return_value = MagicMock()

        block = TrustEvaluationBlock(trust_network=mock_net)
        result = await block.execute(make_context())
        assert result.status == "ok"
        assert result.data["is_trusted"] is True
        assert result.data["transitive_trust"] == 0.75

    async def test_error_handling(self):
        from phionyx_core.pipeline.blocks.trust_evaluation import TrustEvaluationBlock
        mock_net = MagicMock()
        mock_net.add_trust.side_effect = RuntimeError("test error")
        block = TrustEvaluationBlock(trust_network=mock_net)
        result = await block.execute(make_context())
        assert result.status == "error"


# ─── S5: Goal Decomposition ───────────────────────────────────

class TestGoalDecompositionBlock:
    async def test_skip_when_no_module(self):
        from phionyx_core.pipeline.blocks.goal_decomposition import GoalDecompositionBlock
        block = GoalDecompositionBlock(goal_decomposer=None)
        result = await block.execute(make_context())
        assert result.status == "skipped"

    async def test_skip_simple_action(self):
        from phionyx_core.pipeline.blocks.goal_decomposition import GoalDecompositionBlock
        mock_dec = MagicMock()
        block = GoalDecompositionBlock(goal_decomposer=mock_dec)
        ctx = make_context()
        ctx.metadata = {"intent": {"action": "respond"}}
        result = await block.execute(ctx)
        assert result.status == "ok"
        assert result.data["decomposition_run"] is False

    async def test_success_with_requirements(self):
        from phionyx_core.pipeline.blocks.goal_decomposition import GoalDecompositionBlock
        mock_dec = MagicMock()
        sub_goal = MagicMock()
        sub_goal.sub_goal_id = "sg1"
        sub_goal.name = "Sub-goal 1"
        sub_goal.status = "pending"
        sub_goal.priority = 1
        sub_goal.estimated_complexity = 0.5
        plan = MagicMock()
        plan.sub_goals = [sub_goal]
        plan.execution_order = ["sg1"]
        plan.total_complexity = 0.5
        plan.estimated_steps = 1
        mock_dec.decompose.return_value = plan

        block = GoalDecompositionBlock(goal_decomposer=mock_dec)
        ctx = make_context()
        ctx.metadata = {"intent": {"action": "explore", "requirements": ["find treasure", "avoid traps"]}}
        result = await block.execute(ctx)
        assert result.status == "ok"
        assert result.data["decomposition_run"] is True
        assert len(result.data["sub_goals"]) == 1

    async def test_error_handling(self):
        from phionyx_core.pipeline.blocks.goal_decomposition import GoalDecompositionBlock
        mock_dec = MagicMock()
        mock_dec.decompose.side_effect = RuntimeError("test error")
        block = GoalDecompositionBlock(goal_decomposer=mock_dec)
        ctx = make_context()
        ctx.metadata = {"intent": {"action": "explore", "requirements": ["req1"]}}
        result = await block.execute(ctx)
        assert result.status == "error"


# ─── S5: Deliberative Ethics Gate ─────────────────────────────

class TestDeliberativeEthicsGateBlock:
    async def test_inline_fallback_when_no_module(self):
        from phionyx_core.pipeline.blocks.deliberative_ethics_gate import DeliberativeEthicsGateBlock
        block = DeliberativeEthicsGateBlock(deliberative_ethics=None)
        result = await block.execute(make_context())
        assert result.status == "ok"
        assert result.data.get("deliberation_run") is False  # low risk → no deliberation

    async def test_no_deliberation_low_risk(self):
        from phionyx_core.pipeline.blocks.deliberative_ethics_gate import DeliberativeEthicsGateBlock
        mock_ethics = MagicMock()
        block = DeliberativeEthicsGateBlock(deliberative_ethics=mock_ethics)
        ctx = make_context()
        ctx.metadata = {"ethics_result": {"harm_risk": 0.1, "manipulation_risk": 0.05}}
        result = await block.execute(ctx)
        assert result.status == "ok"
        assert result.data["deliberation_run"] is False

    async def test_success_allow_verdict(self):
        from phionyx_core.pipeline.blocks.deliberative_ethics_gate import DeliberativeEthicsGateBlock
        mock_ethics = MagicMock()
        fa = MagicMock()
        fa.framework = "deontological"
        fa.verdict = "ALLOW"
        fa.confidence = 0.9
        fa.reasoning = "No rule violations"
        delib_result = MagicMock()
        delib_result.final_verdict = "ALLOW"
        delib_result.final_confidence = 0.85
        delib_result.consensus = True
        delib_result.framework_assessments = [fa]
        delib_result.reasoning = "All frameworks allow"
        mock_ethics.deliberate.return_value = delib_result

        block = DeliberativeEthicsGateBlock(deliberative_ethics=mock_ethics)
        ctx = make_context()
        ctx.metadata = {"ethics_result": {"harm_risk": 0.5, "manipulation_risk": 0.4}}
        result = await block.execute(ctx)
        assert result.status == "ok"
        assert result.data["deliberation_run"] is True
        assert result.data["final_verdict"] == "ALLOW"
        assert result.data["early_exit"] is False

    async def test_deny_verdict_triggers_early_exit(self):
        from phionyx_core.pipeline.blocks.deliberative_ethics_gate import DeliberativeEthicsGateBlock
        mock_ethics = MagicMock()
        delib_result = MagicMock()
        delib_result.final_verdict = "DENY"
        delib_result.final_confidence = 0.95
        delib_result.consensus = True
        delib_result.framework_assessments = []
        delib_result.reasoning = "High harm risk"
        mock_ethics.deliberate.return_value = delib_result

        block = DeliberativeEthicsGateBlock(deliberative_ethics=mock_ethics)
        ctx = make_context()
        ctx.metadata = {"ethics_result": {"harm_risk": 0.9, "manipulation_risk": 0.8}}
        result = await block.execute(ctx)
        assert result.status == "ok"
        assert result.data["early_exit"] is True
        assert result.data["final_verdict"] == "DENY"

    async def test_error_handling(self):
        from phionyx_core.pipeline.blocks.deliberative_ethics_gate import DeliberativeEthicsGateBlock
        mock_ethics = MagicMock()
        mock_ethics.deliberate.side_effect = RuntimeError("test error")
        block = DeliberativeEthicsGateBlock(deliberative_ethics=mock_ethics)
        ctx = make_context()
        ctx.metadata = {"ethics_result": {"harm_risk": 0.9}}
        result = await block.execute(ctx)
        assert result.status == "error"


# ─── Causal Discovery Integration (v3.6.0) ────────────────────────
class TestCausalGraphDiscovery:
    """Tests for causal structure discovery in CausalGraphUpdateBlock."""

    async def test_discovery_triggered(self):
        """discover_structure() is called after build()."""
        from phionyx_core.pipeline.blocks.causal_graph_update import CausalGraphUpdateBlock
        mock_builder = MagicMock()
        graph = MagicMock()
        graph.node_count = 5
        graph.edge_count = 3
        mock_builder.build.return_value = graph
        mock_builder.to_world_state_dict.return_value = {}
        mock_builder.discover_structure.return_value = {
            "triggered": True, "edges_added": 2,
        }

        block = CausalGraphUpdateBlock(causal_graph_builder=mock_builder)
        ctx = make_context()
        ctx.metadata = {"physics_state": {"entropy": 0.3}}
        result = await block.execute(ctx)

        assert result.status == "ok"
        mock_builder.discover_structure.assert_called_once_with()
        assert result.data["discovery"]["edges_added"] == 2

    async def test_discovery_not_triggered(self):
        """discover_structure() returns triggered=False → no discovery key."""
        from phionyx_core.pipeline.blocks.causal_graph_update import CausalGraphUpdateBlock
        mock_builder = MagicMock()
        graph = MagicMock()
        graph.node_count = 3
        graph.edge_count = 1
        mock_builder.build.return_value = graph
        mock_builder.to_world_state_dict.return_value = {}
        mock_builder.discover_structure.return_value = {"triggered": False}

        block = CausalGraphUpdateBlock(causal_graph_builder=mock_builder)
        ctx = make_context()
        ctx.metadata = {}
        result = await block.execute(ctx)

        assert result.status == "ok"
        assert "discovery" not in result.data

    async def test_discovery_error_non_fatal(self):
        """discover_structure() error → warning logged, block still ok."""
        from phionyx_core.pipeline.blocks.causal_graph_update import CausalGraphUpdateBlock
        mock_builder = MagicMock()
        graph = MagicMock()
        graph.node_count = 3
        graph.edge_count = 1
        mock_builder.build.return_value = graph
        mock_builder.to_world_state_dict.return_value = {}
        mock_builder.discover_structure.side_effect = ValueError("insufficient data")

        block = CausalGraphUpdateBlock(causal_graph_builder=mock_builder)
        ctx = make_context()
        ctx.metadata = {}
        result = await block.execute(ctx)

        assert result.status == "ok"
        assert "discovery" not in result.data


# ─── Edge Richness Campaign (observation pairs) ──────────────────────
class TestCausalGraphObservationPairs:
    """Tests for enriched observation pairs in CausalGraphUpdateBlock."""

    async def test_enriched_observation_pairs(self):
        """Full 8-variable physics_state → 12 pairs observed."""
        from phionyx_core.pipeline.blocks.causal_graph_update import (
            CausalGraphUpdateBlock, OBSERVATION_PAIRS,
        )
        mock_builder = MagicMock()
        graph = MagicMock()
        graph.node_count = 8
        graph.edge_count = 10
        mock_builder.build.return_value = graph
        mock_builder.to_world_state_dict.return_value = {}

        block = CausalGraphUpdateBlock(causal_graph_builder=mock_builder)
        ctx = make_context()
        ctx.metadata = {
            "physics_state": {
                "phi": 0.5, "entropy": 0.4, "coherence": 0.7,
                "valence": 0.3, "arousal": 0.6, "amplitude": 0.8,
                "resonance": 0.65, "drift": 0.1,
            },
        }
        result = await block.execute(ctx)

        assert result.status == "ok"
        assert mock_builder.observe_co_occurrence.call_count == len(OBSERVATION_PAIRS)
        assert result.data["pairs_observed"] == 12

    async def test_partial_physics_state_skips_missing(self):
        """Only pairs with both variables present are observed."""
        from phionyx_core.pipeline.blocks.causal_graph_update import CausalGraphUpdateBlock
        mock_builder = MagicMock()
        graph = MagicMock()
        graph.node_count = 3
        graph.edge_count = 1
        mock_builder.build.return_value = graph
        mock_builder.to_world_state_dict.return_value = {}

        block = CausalGraphUpdateBlock(causal_graph_builder=mock_builder)
        ctx = make_context()
        # Only phi and entropy available → only (phi, entropy) pair observed
        ctx.metadata = {
            "physics_state": {"phi": 0.5, "entropy": 0.4},
        }
        result = await block.execute(ctx)

        assert result.status == "ok"
        # Only pairs where both phi and entropy appear: (phi, entropy) = 1 pair
        assert result.data["pairs_observed"] == 1
        assert mock_builder.observe_co_occurrence.call_count == 1

    async def test_discovery_uses_argless_call(self):
        """discover_structure() called without arguments (uses module defaults)."""
        from phionyx_core.pipeline.blocks.causal_graph_update import CausalGraphUpdateBlock
        mock_builder = MagicMock()
        graph = MagicMock()
        graph.node_count = 5
        graph.edge_count = 3
        mock_builder.build.return_value = graph
        mock_builder.to_world_state_dict.return_value = {}
        mock_builder.discover_structure.return_value = {"triggered": False}

        block = CausalGraphUpdateBlock(causal_graph_builder=mock_builder)
        ctx = make_context()
        ctx.metadata = {}
        await block.execute(ctx)

        mock_builder.discover_structure.assert_called_once_with()

    async def test_result_includes_pairs_observed(self):
        """Result data contains pairs_observed count."""
        from phionyx_core.pipeline.blocks.causal_graph_update import CausalGraphUpdateBlock
        mock_builder = MagicMock()
        graph = MagicMock()
        graph.node_count = 4
        graph.edge_count = 2
        mock_builder.build.return_value = graph
        mock_builder.to_world_state_dict.return_value = {}

        block = CausalGraphUpdateBlock(causal_graph_builder=mock_builder)
        ctx = make_context()
        ctx.metadata = {"physics_state": {"phi": 0.5, "entropy": 0.3, "coherence": 0.7}}
        result = await block.execute(ctx)

        assert "pairs_observed" in result.data
        assert isinstance(result.data["pairs_observed"], int)

    async def test_result_includes_graph_density(self):
        """Result data contains graph_density metric."""
        from phionyx_core.pipeline.blocks.causal_graph_update import CausalGraphUpdateBlock
        mock_builder = MagicMock()
        graph = MagicMock()
        graph.node_count = 4
        graph.edge_count = 6
        mock_builder.build.return_value = graph
        mock_builder.to_world_state_dict.return_value = {}

        block = CausalGraphUpdateBlock(causal_graph_builder=mock_builder)
        ctx = make_context()
        ctx.metadata = {}
        result = await block.execute(ctx)

        assert "graph_density" in result.data
        # 6 edges / (4 * 3) = 0.5
        assert result.data["graph_density"] == 0.5


# ─── Memory Priority Boost Integration (v3.6.0) ───────────────────
class TestMemoryPriorityBoost:
    """Tests for memory priority boost consumption in MemoryConsolidationBlock."""

    async def test_boost_applied_before_consolidation(self):
        """Priority boost IDs in metadata → set_priority_boost() called."""
        from phionyx_core.pipeline.blocks.memory_consolidation_block import MemoryConsolidationBlock
        mock_cons = MagicMock()
        cons_result = MagicMock()
        cons_result.consolidated_count = 1
        cons_result.promoted_count = 0
        cons_result.decayed_count = 0
        cons_result.candidates = []
        cons_result.timestamp = "2026-03-29T00:00:00Z"
        mock_cons.consolidate.return_value = cons_result

        block = MemoryConsolidationBlock(memory_consolidator=mock_cons, consolidation_interval=1)
        ctx = make_context()
        ctx.metadata = {
            "memories": [{"content": "test"}],
            "_feedback_memory_boost_ids": ["mem-1", "mem-2"],
        }
        result = await block.execute(ctx)

        assert result.status == "ok"
        mock_cons.set_priority_boost.assert_called_once_with(["mem-1", "mem-2"], boost=1.5)
        mock_cons.clear_priority_boosts.assert_called_once()
        assert result.data["boost_applied"] == 2

    async def test_no_boost_when_no_ids(self):
        """No boost IDs in metadata → set_priority_boost() not called."""
        from phionyx_core.pipeline.blocks.memory_consolidation_block import MemoryConsolidationBlock
        mock_cons = MagicMock()
        cons_result = MagicMock()
        cons_result.consolidated_count = 0
        cons_result.promoted_count = 0
        cons_result.decayed_count = 0
        cons_result.candidates = []
        cons_result.timestamp = "2026-03-29T00:00:00Z"
        mock_cons.consolidate.return_value = cons_result

        block = MemoryConsolidationBlock(memory_consolidator=mock_cons, consolidation_interval=1)
        ctx = make_context()
        ctx.metadata = {"memories": [{"content": "test"}]}
        _result = await block.execute(ctx)

        mock_cons.set_priority_boost.assert_not_called()

    async def test_boost_cleared_even_without_memories(self):
        """Boost IDs present but no memories → boost cleared anyway."""
        from phionyx_core.pipeline.blocks.memory_consolidation_block import MemoryConsolidationBlock
        mock_cons = MagicMock()

        block = MemoryConsolidationBlock(memory_consolidator=mock_cons, consolidation_interval=1)
        ctx = make_context()
        ctx.metadata = {"_feedback_memory_boost_ids": ["mem-1"]}
        result = await block.execute(ctx)

        assert result.status == "ok"
        mock_cons.set_priority_boost.assert_called_once()
        mock_cons.clear_priority_boosts.assert_called_once()
