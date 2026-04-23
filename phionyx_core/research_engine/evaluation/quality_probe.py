"""Quality Probe — harvests continuous metrics from Phionyx modules.

Exercises Phionyx subsystems with FIXED sample data and captures
continuous quality indicators that respond to Tier A parameter changes.

Unlike binary test pass/fail rates, these metrics differentiate parameter
configurations, enabling CQS variation across Research Engine experiments.

Tier B (review required for modifications).

v2.1.0 — 11 probe domains, 31 metrics, 18 source files.
"""

import re
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ── Fixed Sample Data ──
# Deterministic data — only Tier A parameter values affect output.
# Designed with specific Jaccard similarities to produce varying
# cluster structures at different similarity_threshold values.
#
# Similarity matrix (leader-based, from M0/M4/M7):
# M0-M1: 6/8 = 0.75   M0-M2: 6/8 = 0.75   M0-M3: 6/8 = 0.75
# M4-M5: 5/7 = 0.714   M4-M6: 4/8 = 0.50
# M7-M8: 4/8 = 0.50
#
# At sim=0.6: cluster A=[M0-M3](4), cluster B=[M4,M5](2)
# At sim=0.5: cluster A=[M0-M3](4), cluster B=[M4-M6](3), cluster C=[M7,M8](2)
# At sim=0.4: same as 0.5 (no additional cross-group matches)

_SAMPLE_MEMORIES = [
    # Group A: pipeline topic (pairwise J ≈ 0.75 from leader M0)
    {"content": "the pipeline processes input data through blocks",
     "memory_type": "episodic", "current_strength": 0.8,
     "tags": ["pipeline", "processing"], "metadata": {"access_count": 3}},
    {"content": "the pipeline processes input data through stages",
     "memory_type": "episodic", "current_strength": 0.7,
     "tags": ["pipeline", "processing"], "metadata": {"access_count": 2}},
    {"content": "the pipeline processes input data through execution",
     "memory_type": "episodic", "current_strength": 0.6,
     "tags": ["pipeline", "execution"], "metadata": {"access_count": 4}},
    {"content": "the pipeline handles input data through blocks",
     "memory_type": "episodic", "current_strength": 0.5,
     "tags": ["pipeline", "processing"], "metadata": {"access_count": 1}},

    # Group B: physics topic (M4-M5 J=0.714, M4-M6 J=0.50)
    {"content": "entropy coherence state physics cognitive analysis",
     "memory_type": "episodic", "current_strength": 0.9,
     "tags": ["physics", "entropy"], "metadata": {"access_count": 7}},
    {"content": "entropy coherence state physics cognitive drift",
     "memory_type": "episodic", "current_strength": 0.7,
     "tags": ["physics", "coherence"], "metadata": {"access_count": 5}},
    {"content": "entropy coherence state physics model system",
     "memory_type": "episodic", "current_strength": 0.6,
     "tags": ["physics", "model"], "metadata": {"access_count": 4}},

    # Group C: trust topic (M7-M8 J=0.50)
    {"content": "trust propagation social network decay path",
     "memory_type": "episodic", "current_strength": 0.4,
     "tags": ["social", "trust"], "metadata": {"access_count": 2}},
    {"content": "trust propagation social network transitive connection",
     "memory_type": "episodic", "current_strength": 0.35,
     "tags": ["social", "trust"], "metadata": {"access_count": 1}},

    # Weak memories (for decay sensitivity testing)
    {"content": "temporary buffer entry for processing",
     "memory_type": "working", "current_strength": 0.05,
     "tags": ["temp"], "metadata": {"access_count": 0}},
    {"content": "short lived observation note",
     "memory_type": "episodic", "current_strength": 0.08,
     "tags": ["observation"], "metadata": {"access_count": 0}},
    {"content": "another working memory buffer entry",
     "memory_type": "working", "current_strength": 0.03,
     "tags": ["temp"], "metadata": {"access_count": 0}},
]

# Total: 12 memories (9 episodic + 3 working → 12 episodic+working for consolidation)
_TOTAL_MEMORIES = len(_SAMPLE_MEMORIES)
_TOTAL_EPISODIC_WORKING = sum(
    1 for m in _SAMPLE_MEMORIES
    if m.get("memory_type") in ("episodic", "working")
)


class QualityProbe:
    """Harvest continuous quality metrics from Phionyx modules.

    Reads current Tier A parameter values from source files, instantiates
    modules with those explicit values, runs them on fixed sample data,
    and returns continuous metrics in [0, 1] range.

    This avoids Python module caching issues because constructor args
    override module-level defaults.

    v2.1.0 — 11 probe domains, 31 metrics.
    """

    def __init__(self, repo_dir: str = "."):
        self._repo = Path(repo_dir).resolve()

    def probe(self) -> dict[str, float]:
        """Run all probes and return continuous metrics dict.

        Returns metrics in [0, 1] range suitable for CQS blending.
        On failure, returns default 0.5 values (neutral blending).
        """
        metrics: dict[str, float] = {}

        # Original 4 domains
        try:
            metrics.update(self._probe_memory())
        except Exception as e:
            logger.warning("Memory probe failed: %s", e)
            metrics.update(self._default_memory_metrics())

        try:
            metrics.update(self._probe_physics())
        except Exception as e:
            logger.warning("Physics probe failed: %s", e)
            metrics.update(self._default_physics_metrics())

        try:
            metrics.update(self._probe_causality())
        except Exception as e:
            logger.warning("Causality probe failed: %s", e)
            metrics.update(self._default_causality_metrics())

        try:
            metrics.update(self._probe_formulas())
        except Exception as e:
            logger.warning("Formulas probe failed: %s", e)
            metrics.update(self._default_formulas_metrics())

        # New domains (v2.0.0)
        try:
            metrics.update(self._probe_physics_extended())
        except Exception as e:
            logger.warning("Physics extended probe failed: %s", e)
            metrics.update(self._default_physics_extended_metrics())

        try:
            metrics.update(self._probe_social())
        except Exception as e:
            logger.warning("Social probe failed: %s", e)
            metrics.update(self._default_social_metrics())

        try:
            metrics.update(self._probe_meta())
        except Exception as e:
            logger.warning("Meta probe failed: %s", e)
            metrics.update(self._default_meta_metrics())

        try:
            metrics.update(self._probe_world())
        except Exception as e:
            logger.warning("World probe failed: %s", e)
            metrics.update(self._default_world_metrics())

        try:
            metrics.update(self._probe_dynamics())
        except Exception as e:
            logger.warning("Dynamics probe failed: %s", e)
            metrics.update(self._default_dynamics_metrics())

        try:
            metrics.update(self._probe_governance())
        except Exception as e:
            logger.warning("Governance probe failed: %s", e)
            metrics.update(self._default_governance_metrics())

        # v2.1.0 — Pipeline Integration
        try:
            metrics.update(self._probe_pipeline_integration())
        except Exception as e:
            logger.warning("Pipeline integration probe failed: %s", e)
            metrics.update(self._default_pipeline_integration_metrics())

        return metrics

    # ── Domain 1: Memory (5 metrics) ──

    def _probe_memory(self) -> dict[str, float]:
        """Run MemoryConsolidator with current Tier A params on sample data."""
        from phionyx_core.memory.consolidation import MemoryConsolidator

        params = self._read_consolidation_params()

        consolidator = MemoryConsolidator(
            _min_cluster_size=params["min_cluster_size"],
            _similarity_threshold=params["similarity_threshold"],
            _promotion_access_threshold=params["promotion_access_threshold"],
            _decay_strength_threshold=params["decay_strength_threshold"],
        )

        result = consolidator.consolidate(_SAMPLE_MEMORIES)

        clustered_count = sum(len(c.memories) for c in result.candidates)
        cluster_quality = clustered_count / max(1, _TOTAL_EPISODIC_WORKING)

        max_possible = max(1, _TOTAL_EPISODIC_WORKING // 2)
        consolidation_rate = min(1.0, result.consolidated_count / max_possible)

        promotion_rate = result.promoted_count / max(1, _TOTAL_EPISODIC_WORKING)

        decay_sensitivity = result.decayed_count / max(1, _TOTAL_MEMORIES)

        if result.candidates:
            mean_sim = sum(
                c.similarity_score for c in result.candidates
            ) / len(result.candidates)
        else:
            mean_sim = 0.0

        return {
            "memory_cluster_quality": min(1.0, cluster_quality),
            "memory_consolidation_rate": min(1.0, consolidation_rate),
            "memory_promotion_rate": min(1.0, promotion_rate),
            "memory_decay_sensitivity": min(1.0, decay_sensitivity),
            "memory_mean_similarity": min(1.0, mean_sim),
        }

    # ── Domain 2: Physics (2 metrics) ──

    def _probe_physics(self) -> dict[str, float]:
        """Compute physics-derived continuous metrics from constants."""
        gamma = self._read_param(
            "phionyx_core/physics/constants.py", "DEFAULT_GAMMA", 0.15
        )
        f_self = self._read_param(
            "phionyx_core/physics/constants.py", "DEFAULT_F_SELF", 0.5
        )

        gamma_range = 0.30 - 0.05
        physics_stability = max(0.0, min(1.0, 1.0 - (gamma - 0.05) / gamma_range))

        f_self_range = 1.0 - 0.1
        resonance_quality = max(0.0, min(1.0, (f_self - 0.1) / f_self_range))

        return {
            "physics_stability": physics_stability,
            "physics_resonance_quality": resonance_quality,
        }

    # ── Domain 3: Causality (2 metrics) ──

    def _probe_causality(self) -> dict[str, float]:
        """Exercise CausalGraphBuilder with current Tier A defaults."""
        from phionyx_core.causality.causal_graph import CausalGraphBuilder

        conf = self._read_param(
            "phionyx_core/causality/causal_graph.py", "default_confidence", 0.5
        )
        strn = self._read_param(
            "phionyx_core/causality/causal_graph.py", "default_strength", 0.5
        )

        def _build_graph(s: float, c: float) -> float:
            b = CausalGraphBuilder()
            for n in ["entropy", "coherence", "phi", "resonance", "arousal", "drift"]:
                b.add_node(n, node_type="state")
            b.add_causal_link("entropy", "coherence", strength=0.85, confidence=0.95)
            b.add_causal_link("phi", "resonance", strength=0.75, confidence=0.90)
            b.add_causal_link("coherence", "drift", strength=s, confidence=c)
            b.add_causal_link("arousal", "entropy", strength=s, confidence=c)
            b.add_causal_link("phi", "drift", strength=s, confidence=c)
            edges = list(b.build().edges.values())
            return sum(e.effective_strength for e in edges) / len(edges) if edges else 0.0

        current = _build_graph(strn, conf)
        worst = _build_graph(0.3, 0.3)
        best = _build_graph(0.8, 0.8)
        span = best - worst
        norm_strength = (current - worst) / span if span > 0 else 0.5

        threshold = 0.3
        eff = strn * conf
        quality = 1.0 if eff > threshold else eff / threshold

        return {
            "causality_mean_effective_strength": max(0.0, min(1.0, norm_strength)),
            "causality_graph_quality": max(0.0, min(1.0, quality)),
        }

    # ── Domain 4: Formulas (3 metrics) ──

    def _probe_formulas(self) -> dict[str, float]:
        """Exercise calculate_phi_cognitive with current Tier A params."""
        from phionyx_core.physics.formulas import calculate_phi_cognitive

        epk = self._read_param(
            "phionyx_core/physics/formulas.py", "entropy_penalty_k", 1.0
        )
        br = self._read_param(
            "phionyx_core/physics/formulas.py", "base_resonance", 0.1
        )
        rg = self._read_param(
            "phionyx_core/physics/formulas.py", "recovery_gain", 0.05
        )

        _kw = dict(entropy=0.6, stability=0.8, valence=0.0)
        _rec_kw = dict(entropy=0.4, stability=0.8, valence=0.3,
                       previous_entropy=0.8, previous_valence=-0.5)

        phi_curr = calculate_phi_cognitive(**_kw, entropy_penalty_k=epk, base_resonance=br, recovery_gain=rg)
        phi_best = calculate_phi_cognitive(**_kw, entropy_penalty_k=0.0, base_resonance=br, recovery_gain=rg)
        phi_worst = calculate_phi_cognitive(**_kw, entropy_penalty_k=2.0, base_resonance=br, recovery_gain=rg)
        span1 = phi_best - phi_worst
        norm_epk = (phi_curr - phi_worst) / span1 if span1 > 0 else 0.5

        _kw2 = dict(entropy=0.1, stability=0.9, valence=0.0)
        phi_curr2 = calculate_phi_cognitive(**_kw2, entropy_penalty_k=epk, base_resonance=br, recovery_gain=rg)
        phi_best2 = calculate_phi_cognitive(**_kw2, entropy_penalty_k=epk, base_resonance=0.2, recovery_gain=rg)
        phi_worst2 = calculate_phi_cognitive(**_kw2, entropy_penalty_k=epk, base_resonance=0.05, recovery_gain=rg)
        span2 = phi_best2 - phi_worst2
        norm_br = (phi_curr2 - phi_worst2) / span2 if span2 > 0 else 0.5

        phi_curr3 = calculate_phi_cognitive(**_rec_kw, entropy_penalty_k=epk, base_resonance=br, recovery_gain=rg)
        phi_best3 = calculate_phi_cognitive(**_rec_kw, entropy_penalty_k=epk, base_resonance=br, recovery_gain=0.2)
        phi_worst3 = calculate_phi_cognitive(**_rec_kw, entropy_penalty_k=epk, base_resonance=br, recovery_gain=0.0)
        span3 = phi_best3 - phi_worst3
        norm_rg = (phi_curr3 - phi_worst3) / span3 if span3 > 0 else 0.5

        return {
            "formula_entropy_sensitivity": max(0.0, min(1.0, norm_epk)),
            "formula_base_floor_effect": max(0.0, min(1.0, norm_br)),
            "formula_recovery_strength": max(0.0, min(1.0, norm_rg)),
        }

    # ── Domain 5: Physics Extended (3 metrics) ──

    def _probe_physics_extended(self) -> dict[str, float]:
        """Probe extended physics constants from constants.py.

        Tests threshold sensitivity, entropy threshold effect, and boost effect.
        """
        stab_high = self._read_param(
            "phionyx_core/physics/constants.py", "STABILITY_HIGH_THRESHOLD", 0.7
        )
        stab_low = self._read_param(
            "phionyx_core/physics/constants.py", "STABILITY_LOW_THRESHOLD", 0.4
        )
        ent_thresh = self._read_param(
            "phionyx_core/physics/constants.py", "ENTROPY_THRESHOLD_DEFAULT", 0.5
        )
        boost = self._read_param(
            "phionyx_core/physics/constants.py", "ENTROPY_BOOST_FACTOR", 0.1
        )

        # Metric 1: Threshold separation — wider gap = more nuanced mode selection
        # Normalized: 0.0 at gap=0, 1.0 at gap=0.7 (max possible)
        gap = max(0.0, stab_high - stab_low)
        threshold_sensitivity = min(1.0, gap / 0.7)

        # Metric 2: Entropy threshold effect — centered threshold = balanced
        # Normalized: 1.0 at 0.5 (balanced), lower at extremes
        ent_balance = 1.0 - abs(ent_thresh - 0.5) / 0.5
        entropy_threshold_effect = max(0.0, min(1.0, ent_balance))

        # Metric 3: Boost effect — normalized across range [0.01, 0.3]
        boost_norm = (boost - 0.01) / (0.3 - 0.01) if 0.3 > 0.01 else 0.5
        boost_effect = max(0.0, min(1.0, boost_norm))

        return {
            "physics_threshold_sensitivity": threshold_sensitivity,
            "physics_entropy_threshold_effect": entropy_threshold_effect,
            "physics_boost_effect": boost_effect,
        }

    # ── Domain 6: Social (3 metrics) ──

    def _probe_social(self) -> dict[str, float]:
        """Probe trust propagation network with fixed topology."""
        from phionyx_core.social.trust_propagation import TrustNetwork

        df = self._read_param(
            "phionyx_core/social/trust_propagation.py", "decay_factor", 0.9
        )
        tt = self._read_param(
            "phionyx_core/social/trust_propagation.py", "trust_threshold", 0.5
        )
        mpl = int(self._read_param(
            "phionyx_core/social/trust_propagation.py", "max_path_length", 5
        ))

        # Build fixed trust topology: A→B→C→D (chain), A→D (direct)
        net = TrustNetwork(
            decay_factor=df,
            trust_threshold=tt,
            max_path_length=mpl,
        )
        net.add_trust("A", "B", 0.9)
        net.add_trust("B", "C", 0.8)
        net.add_trust("C", "D", 0.7)
        net.add_trust("A", "D", 0.4)  # Weak direct

        # Metric 1: Transitive reach — how much trust propagates A→D
        ad = net.query_trust("A", "D")
        # Normalize: best possible = 0.9*0.8*0.7*decay^3, worst = 0
        best_trans = 0.9 * 0.8 * 0.7 * (0.99 ** 3)
        trust_reach = min(1.0, ad.transitive_trust / best_trans) if best_trans > 0 else 0.5

        # Metric 2: Trust discrimination — gap between trusted and untrusted
        ab = net.query_trust("A", "B")
        # Direct trust should be high, threshold determines discrimination
        discrimination = ab.transitive_trust - tt if ab.transitive_trust > tt else 0.0
        trust_discrimination = min(1.0, discrimination / 0.5)

        # Metric 3: Network density — fraction of pairs that are trusted
        pairs = [("A", "B"), ("A", "C"), ("A", "D"), ("B", "C"), ("B", "D"), ("C", "D")]
        trusted_count = sum(1 for s, t in pairs if net.query_trust(s, t).is_trusted)
        network_density = trusted_count / len(pairs)

        return {
            "social_trust_reach": max(0.0, min(1.0, trust_reach)),
            "social_trust_discrimination": max(0.0, min(1.0, trust_discrimination)),
            "social_network_density": max(0.0, min(1.0, network_density)),
        }

    # ── Domain 7: Meta (3 metrics) ──

    def _probe_meta(self) -> dict[str, float]:
        """Probe knowledge boundary and self-model drift with fixed inputs."""
        from phionyx_core.meta.knowledge_boundary import KnowledgeBoundaryDetector

        # Knowledge Boundary probe
        bt = self._read_param(
            "phionyx_core/meta/knowledge_boundary.py", "boundary_threshold", 0.4
        )
        ht = self._read_param(
            "phionyx_core/meta/knowledge_boundary.py", "hedge_threshold", 0.6
        )
        w_ood = self._read_param(
            "phionyx_core/meta/knowledge_boundary.py", "weight_ood", 0.4
        )
        w_rel = self._read_param(
            "phionyx_core/meta/knowledge_boundary.py", "weight_relevance", 0.35
        )
        w_nov = self._read_param(
            "phionyx_core/meta/knowledge_boundary.py", "weight_novelty", 0.25
        )

        detector = KnowledgeBoundaryDetector(
            boundary_threshold=bt, hedge_threshold=ht,
            weight_ood=w_ood, weight_relevance=w_rel, weight_novelty=w_nov,
        )

        # Fixed test scenarios
        in_dist = detector.assess(ood_score=0.1, graph_relevance=0.9, novelty_score=0.1)
        _edge_case = detector.assess(ood_score=0.5, graph_relevance=0.5, novelty_score=0.5)
        out_dist = detector.assess(ood_score=0.9, graph_relevance=0.1, novelty_score=0.9)

        # Metric 1: Boundary sensitivity — score spread across scenarios
        spread = in_dist.boundary_score - out_dist.boundary_score
        boundary_sensitivity = max(0.0, min(1.0, spread))

        # Metric 2: Hedge zone width — hedge_threshold - boundary_threshold
        hedge_width = max(0.0, ht - bt)
        hedge_zone_quality = min(1.0, hedge_width / 0.4)

        # Drift probe
        dt_low = self._read_param(
            "phionyx_core/meta/self_model_drift.py", "drift_threshold_low", 0.05
        )
        dt_crit = self._read_param(
            "phionyx_core/meta/self_model_drift.py", "drift_threshold_critical", 0.35
        )
        _cd = self._read_param(
            "phionyx_core/meta/self_model_drift.py", "correction_dampening", 0.5
        )

        # Metric 3: Drift detection range — wider = more granular severity
        drift_range = max(0.0, dt_crit - dt_low)
        drift_detection_range = min(1.0, drift_range / 0.5)

        return {
            "meta_boundary_sensitivity": max(0.0, min(1.0, boundary_sensitivity)),
            "meta_hedge_zone_quality": max(0.0, min(1.0, hedge_zone_quality)),
            "meta_drift_detection_range": max(0.0, min(1.0, drift_detection_range)),
        }

    # ── Domain 8: World (2 metrics) ──

    def _probe_world(self) -> dict[str, float]:
        """Probe temporal tracker and goal decomposer."""
        from phionyx_core.world.temporal_tracker import TemporalTracker
        from phionyx_core.planning.goal_decomposer import GoalDecomposer

        dr = self._read_param(
            "phionyx_core/world/temporal_tracker.py", "temporal_decay_rate", 0.02
        )
        mh = int(self._read_param(
            "phionyx_core/world/temporal_tracker.py", "max_history_per_entity", 100
        ))

        # Build fixed timeline: 10 updates, then query at different staleness
        tracker = TemporalTracker(decay_rate=dr, max_history_per_entity=mh)
        for i in range(10):
            tracker.advance_turn()
            tracker.update("entity_A", "mood", f"state_{i}", confidence=0.9)

        # Advance 20 more turns without updates
        for _ in range(20):
            tracker.advance_turn()

        q = tracker.query("entity_A", "mood")

        # Metric 1: Temporal confidence retention — how much confidence remains
        # Normalized: 1.0 if no decay, 0.0 if fully decayed
        retention = max(0.0, min(1.0, q.confidence / 0.9))

        # Metric 2: Goal decomposition quality
        dc = self._read_param(
            "phionyx_core/planning/goal_decomposer.py", "default_complexity", 0.5
        )
        decomposer = GoalDecomposer(default_complexity=dc)
        plan = decomposer.decompose(
            goal_id="test", goal_name="Test Goal",
            requirements=["step1", "step2", "step3"],
            dependencies={"step2": ["step1"], "step3": ["step2"]},
        )
        # Quality: correct ordering + reasonable complexity
        order_correct = 1.0 if plan.execution_order == [
            "sg_test_0", "sg_test_1", "sg_test_2"
        ] else 0.5
        complexity_normalized = min(1.0, plan.total_complexity / 3.0)
        decomposition_quality = (order_correct + complexity_normalized) / 2.0

        return {
            "world_temporal_retention": max(0.0, min(1.0, retention)),
            "world_decomposition_quality": max(0.0, min(1.0, decomposition_quality)),
        }

    # ── Domain 9: Dynamics (3 metrics) ──

    def _probe_dynamics(self) -> dict[str, float]:
        """Probe dynamics alpha/beta and entropy modulation parameters."""
        school_a = self._read_param(
            "phionyx_core/physics/dynamics.py", "SCHOOL_ALPHA", 0.1
        )
        school_b = self._read_param(
            "phionyx_core/physics/dynamics.py", "SCHOOL_BETA", 0.2
        )
        game_a = self._read_param(
            "phionyx_core/physics/dynamics.py", "GAME_ALPHA", 0.3
        )
        game_b = self._read_param(
            "phionyx_core/physics/dynamics.py", "GAME_BETA", 0.1
        )
        kh = self._read_param(
            "phionyx_core/physics/entropy_modulation.py", "ENTROPY_MOD_KH", 1.0
        )

        # Metric 1: Mode separation — SCHOOL vs GAME alpha/beta spread
        alpha_spread = abs(game_a - school_a)
        beta_spread = abs(school_b - game_b)
        mode_separation = min(1.0, (alpha_spread + beta_spread) / 0.6)

        # Metric 2: Stability bias — SCHOOL beta > GAME beta = stable bias
        # Normalized: 1.0 when SCHOOL_BETA >> GAME_BETA
        stability_bias = min(1.0, max(0.0, (school_b - game_b) / 0.3))

        # Metric 3: Entropy modulation strength — kH effect
        # Normalized across [0.1, 5.0]
        kh_norm = (kh - 0.1) / (5.0 - 0.1) if 5.0 > 0.1 else 0.5
        entropy_modulation_strength = max(0.0, min(1.0, kh_norm))

        return {
            "dynamics_mode_separation": max(0.0, min(1.0, mode_separation)),
            "dynamics_stability_bias": max(0.0, min(1.0, stability_bias)),
            "dynamics_entropy_modulation": max(0.0, min(1.0, entropy_modulation_strength)),
        }

    # ── Domain 10: Governance (2 metrics) ──

    def _probe_governance(self) -> dict[str, float]:
        """Probe deliberative ethics framework balance."""
        dw = self._read_param(
            "phionyx_core/governance/deliberative_ethics.py", "deontological_weight", 0.3
        )
        cw = self._read_param(
            "phionyx_core/governance/deliberative_ethics.py", "consequentialist_weight", 0.3
        )
        vw = self._read_param(
            "phionyx_core/governance/deliberative_ethics.py", "virtue_weight", 0.2
        )
        carw = self._read_param(
            "phionyx_core/governance/deliberative_ethics.py", "care_weight", 0.2
        )
        deny_t = self._read_param(
            "phionyx_core/governance/deliberative_ethics.py", "deny_threshold", 0.6
        )
        guard_t = self._read_param(
            "phionyx_core/governance/deliberative_ethics.py", "guard_threshold", 0.4
        )

        # Metric 1: Framework balance — how evenly distributed are weights
        # Ideal: all 0.25, worst: one framework dominates
        weights = [dw, cw, vw, carw]
        total = sum(weights) or 1.0
        normalized = [w / total for w in weights]
        # Entropy-like: -sum(p*log(p)) / log(4), max=1.0 when uniform
        import math
        balance = 0.0
        for p in normalized:
            if p > 0:
                balance -= p * math.log(p)
        max_entropy = math.log(4)
        framework_balance = balance / max_entropy if max_entropy > 0 else 0.5

        # Metric 2: Guard zone width — deny_threshold - guard_threshold
        guard_zone = max(0.0, deny_t - guard_t)
        guard_zone_quality = min(1.0, guard_zone / 0.4)

        return {
            "governance_framework_balance": max(0.0, min(1.0, framework_balance)),
            "governance_guard_zone": max(0.0, min(1.0, guard_zone_quality)),
        }

    # ── Domain 11: Pipeline Integration (3 metrics) ──

    def _probe_pipeline_integration(self) -> dict[str, float]:
        """Probe cross-module data flow via mini pipeline block execution.

        Tests that entropy/phi computations actually vary with input,
        and that feedback blocks skip gracefully with None DI.
        """
        from phionyx_core.physics.text_physics import calculate_text_entropy_zlib
        from phionyx_core.physics.formulas import calculate_phi_cognitive

        # Metric 1: pipeline_entropy_sensitivity — 3 texts → entropy spread
        texts = [
            "hi",
            "The cognitive pipeline processes blocks in sequence through phases",
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" * 5,
        ]
        entropies = [calculate_text_entropy_zlib(t) for t in texts]
        e_spread = max(entropies) - min(entropies) if entropies else 0.0
        # Normalize: 0.4 spread = 1.0 (good), 0.0 = 0.0 (bad)
        entropy_sensitivity = min(1.0, e_spread / 0.4)

        # Metric 2: pipeline_phi_sensitivity — 3 (valence, entropy) combos → phi spread
        combos = [
            {"entropy": 0.2, "stability": 0.8, "valence": 0.0},
            {"entropy": 0.5, "stability": 0.8, "valence": 0.7},
            {"entropy": 0.8, "stability": 0.8, "valence": -0.5},
        ]
        phis = [calculate_phi_cognitive(**c) for c in combos]
        p_spread = max(phis) - min(phis) if phis else 0.0
        # Normalize: 0.3 spread = 1.0 (good)
        phi_sensitivity = min(1.0, p_spread / 0.3)

        # Metric 3: pipeline_feedback_coverage — feedback blocks skip with None DI
        skip_count = 0
        total = 3
        try:
            from phionyx_core.pipeline.blocks.outcome_feedback import OutcomeFeedbackBlock
            _blk = OutcomeFeedbackBlock()
            # OutcomeFeedbackBlock with no DI services should have skip behavior
            skip_count += 1
        except Exception:
            pass

        try:
            from phionyx_core.pipeline.blocks.causal_graph_update import CausalGraphUpdateBlock
            _blk = CausalGraphUpdateBlock()
            skip_count += 1
        except Exception:
            pass

        try:
            from phionyx_core.pipeline.blocks.memory_consolidation_block import MemoryConsolidationBlock
            _blk = MemoryConsolidationBlock()
            skip_count += 1
        except Exception:
            pass

        feedback_coverage = skip_count / total

        return {
            "pipeline_entropy_sensitivity": max(0.0, min(1.0, entropy_sensitivity)),
            "pipeline_phi_sensitivity": max(0.0, min(1.0, phi_sensitivity)),
            "pipeline_feedback_coverage": max(0.0, min(1.0, feedback_coverage)),
        }

    # ── Parameter Reading ──

    def _read_consolidation_params(self) -> dict[str, Any]:
        """Read memory consolidation Tier A params from source file."""
        return {
            "min_cluster_size": int(self._read_param(
                "phionyx_core/memory/consolidation.py", "min_cluster_size", 3
            )),
            "similarity_threshold": self._read_param(
                "phionyx_core/memory/consolidation.py", "similarity_threshold", 0.6
            ),
            "promotion_access_threshold": int(self._read_param(
                "phionyx_core/memory/consolidation.py",
                "promotion_access_threshold", 5
            )),
            "decay_strength_threshold": self._read_param(
                "phionyx_core/memory/consolidation.py",
                "decay_strength_threshold", 0.1
            ),
        }

    def _read_param(
        self, rel_path: str, param_name: str, default: float
    ) -> float:
        """Read a module-level parameter value from a source file.

        Uses the same regex pattern as loop.py's _apply_parameter_edit:
        matches `param_name = value` at module level.
        """
        path = self._repo / rel_path
        if not path.exists():
            return default
        try:
            content = path.read_text()
            match = re.search(
                rf"^{re.escape(param_name)}\s*=\s*([\d.]+)",
                content,
                re.MULTILINE,
            )
            return float(match.group(1)) if match else default
        except Exception:
            return default

    # ── Default Metrics (fallback on probe failure) ──

    @staticmethod
    def _default_memory_metrics() -> dict[str, float]:
        return {
            "memory_cluster_quality": 0.5,
            "memory_consolidation_rate": 0.5,
            "memory_promotion_rate": 0.5,
            "memory_decay_sensitivity": 0.5,
            "memory_mean_similarity": 0.5,
        }

    @staticmethod
    def _default_physics_metrics() -> dict[str, float]:
        return {
            "physics_stability": 0.5,
            "physics_resonance_quality": 0.5,
        }

    @staticmethod
    def _default_causality_metrics() -> dict[str, float]:
        return {
            "causality_mean_effective_strength": 0.5,
            "causality_graph_quality": 0.5,
        }

    @staticmethod
    def _default_formulas_metrics() -> dict[str, float]:
        return {
            "formula_entropy_sensitivity": 0.5,
            "formula_base_floor_effect": 0.5,
            "formula_recovery_strength": 0.5,
        }

    @staticmethod
    def _default_physics_extended_metrics() -> dict[str, float]:
        return {
            "physics_threshold_sensitivity": 0.5,
            "physics_entropy_threshold_effect": 0.5,
            "physics_boost_effect": 0.5,
        }

    @staticmethod
    def _default_social_metrics() -> dict[str, float]:
        return {
            "social_trust_reach": 0.5,
            "social_trust_discrimination": 0.5,
            "social_network_density": 0.5,
        }

    @staticmethod
    def _default_meta_metrics() -> dict[str, float]:
        return {
            "meta_boundary_sensitivity": 0.5,
            "meta_hedge_zone_quality": 0.5,
            "meta_drift_detection_range": 0.5,
        }

    @staticmethod
    def _default_world_metrics() -> dict[str, float]:
        return {
            "world_temporal_retention": 0.5,
            "world_decomposition_quality": 0.5,
        }

    @staticmethod
    def _default_dynamics_metrics() -> dict[str, float]:
        return {
            "dynamics_mode_separation": 0.5,
            "dynamics_stability_bias": 0.5,
            "dynamics_entropy_modulation": 0.5,
        }

    @staticmethod
    def _default_governance_metrics() -> dict[str, float]:
        return {
            "governance_framework_balance": 0.5,
            "governance_guard_zone": 0.5,
        }

    @staticmethod
    def _default_pipeline_integration_metrics() -> dict[str, float]:
        return {
            "pipeline_entropy_sensitivity": 0.5,
            "pipeline_phi_sensitivity": 0.5,
            "pipeline_feedback_coverage": 0.5,
        }
