"""
Unified Consciousness Proxy Aggregator
========================================

**Honesty note:** Despite the name "consciousness", this module computes
pipeline quality metrics, not consciousness measurements. The name is
retained for backward compatibility. These are engineering quality proxies
that measure determinism, coverage, and stability — not cognitive awareness.

Aggregates 5 pipeline quality proxies into AGI_READINESS_SCORE.
This score is SEPARATE from CQS (Composite Quality Score).

5 Proxies:
1. state_hash_consistency — Pipeline state determinism (hash chain integrity)
2. trace_integrity — Pipeline block trace completeness (46-block coverage)
3. counterfactual_self_coherence — Self-model stability under perturbation
4. identity_persistence — Behavioral identity stability over time
5. drift_stability — Self-model drift detection quality

AGI_READINESS_SCORE = geometric_mean(5 proxies)

Geometric mean chosen for same reason as CQS: any zero collapses the score,
preventing metric hacking by excelling on one proxy while ignoring others.
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ConsciousnessProxyReport:
    """Report of all 5 consciousness proxies."""
    state_hash_consistency: float = 0.0  # [0,1]
    trace_integrity: float = 0.0         # [0,1]
    counterfactual_self_coherence: float = 0.0  # [0,1]
    identity_persistence: float = 0.0    # [0,1]
    drift_stability: float = 0.0         # [0,1]
    agi_readiness_score: float = 0.0     # geometric mean
    details: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, float]:
        return {
            "state_hash_consistency": round(self.state_hash_consistency, 4),
            "trace_integrity": round(self.trace_integrity, 4),
            "counterfactual_self_coherence": round(self.counterfactual_self_coherence, 4),
            "identity_persistence": round(self.identity_persistence, 4),
            "drift_stability": round(self.drift_stability, 4),
            "agi_readiness_score": round(self.agi_readiness_score, 4),
        }


class ConsciousnessProxyAggregator:
    """Aggregates consciousness proxies into AGI_READINESS_SCORE.

    Usage:
        aggregator = ConsciousnessProxyAggregator()
        report = aggregator.compute(
            state_hash=0.95,
            trace=0.90,
            cf_self=0.85,
            identity=0.92,
            drift=0.88,
        )
        print(report.agi_readiness_score)  # geometric mean
    """

    @staticmethod
    def compute(
        state_hash: float = 0.0,
        trace: float = 0.0,
        cf_self: float = 0.0,
        identity: float = 0.0,
        drift: float = 0.0,
        details: dict[str, str] | None = None,
    ) -> ConsciousnessProxyReport:
        """Compute AGI readiness score from 5 proxies.

        All inputs should be [0, 1]. Values are clamped.

        Returns ConsciousnessProxyReport with geometric mean as agi_readiness_score.
        """
        values = [
            max(0.0, min(1.0, state_hash)),
            max(0.0, min(1.0, trace)),
            max(0.0, min(1.0, cf_self)),
            max(0.0, min(1.0, identity)),
            max(0.0, min(1.0, drift)),
        ]

        # Geometric mean: (product of values)^(1/n)
        # Any zero → score = 0 (intentional: prevents metric hacking)
        product = 1.0
        for v in values:
            product *= v

        if product <= 0:
            agi_score = 0.0
        else:
            agi_score = product ** (1.0 / len(values))

        return ConsciousnessProxyReport(
            state_hash_consistency=values[0],
            trace_integrity=values[1],
            counterfactual_self_coherence=values[2],
            identity_persistence=values[3],
            drift_stability=values[4],
            agi_readiness_score=round(agi_score, 4),
            details=details or {},
        )

    @staticmethod
    def compute_from_dict(proxies: dict[str, float]) -> ConsciousnessProxyReport:
        """Compute from a dict of proxy name → value."""
        return ConsciousnessProxyAggregator.compute(
            state_hash=proxies.get("state_hash_consistency", 0.0),
            trace=proxies.get("trace_integrity", 0.0),
            cf_self=proxies.get("counterfactual_self_coherence", 0.0),
            identity=proxies.get("identity_persistence", 0.0),
            drift=proxies.get("drift_stability", 0.0),
        )
