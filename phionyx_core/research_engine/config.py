"""Research Engine configuration — lightweight dataclasses (no Pydantic dependency)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SessionConfig:
    """Bounds that govern a single research session.

    When any limit is hit the engine stops cleanly and writes a SessionReport.
    """

    max_experiments: int = 50
    max_session_seconds: float = 14400.0  # 4 hours
    max_cost_usd: float = 10.0
    max_consecutive_failures: int = 20
    benchmark_timeout_seconds: float = 300.0


@dataclass
class AcceptanceThresholds:
    """Gate criteria that an experiment must clear before it is marked 'keep'.

    complexity_tax maps (min_lines, max_lines) tuples to a minimum CQS delta
    that must be met on top of min_cqs_delta. Larger diffs must justify themselves
    with larger gains.
    """

    min_cqs_delta: float = 0.005
    max_latency_increase_pct: float = 20.0
    max_cost_increase_pct: float = 15.0
    complexity_tax: dict[str, float] = field(
        default_factory=lambda: {
            "1-10": 0.000,   # trivial one-liner — no extra bar
            "11-30": 0.002,  # small refactor
            "31-100": 0.005, # medium change — must earn its place
            "101-300": 0.010, # large change — high bar
            "301+": 0.020,   # very large — requires strong evidence
        }
    )

    def complexity_tax_for(self, lines_changed: int) -> float:
        """Return the additional CQS delta required for a diff of *lines_changed*."""
        if lines_changed <= 10:
            return self.complexity_tax.get("1-10", 0.000)
        if lines_changed <= 30:
            return self.complexity_tax.get("11-30", 0.002)
        if lines_changed <= 100:
            return self.complexity_tax.get("31-100", 0.005)
        if lines_changed <= 300:
            return self.complexity_tax.get("101-300", 0.010)
        return self.complexity_tax.get("301+", 0.020)

    def effective_min_cqs_delta(self, lines_changed: int) -> float:
        """min_cqs_delta + complexity_tax for the given diff size."""
        return self.min_cqs_delta + self.complexity_tax_for(lines_changed)


@dataclass
class CQSWeights:
    """Per-subsystem diagnostic weights.

    .. note::
        v1 CQS uses the geometric mean of the six primary metric components —
        these weights are retained for subsystem diagnostics and reporting only.
        They do **not** feed into the primary CQS score.
    """

    task_completion: float = 0.30
    determinism: float = 0.20
    reasoning: float = 0.15
    compliance: float = 0.15
    coherence: float = 0.10
    trace: float = 0.10

    def validate(self) -> None:
        """Assert weights sum to 1.0 within floating-point tolerance."""
        total = (
            self.task_completion
            + self.determinism
            + self.reasoning
            + self.compliance
            + self.coherence
            + self.trace
        )
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"CQSWeights must sum to 1.0, got {total:.6f}")


@dataclass
class EngineConfig:
    """Top-level configuration object consumed by ResearchEngine.__init__."""

    session: SessionConfig = field(default_factory=SessionConfig)
    thresholds: AcceptanceThresholds = field(default_factory=AcceptanceThresholds)
    weights: CQSWeights = field(default_factory=CQSWeights)
    data_dir: str = "data/research_engine"
    audit_dir: str = "data/research_engine/audit"
    experiment_branch_prefix: str = "research/"

    def validate(self) -> None:
        """Run consistency checks across all sub-configs."""
        self.weights.validate()
        if self.session.max_experiments < 1:
            raise ValueError("max_experiments must be >= 1")
        if self.session.max_cost_usd <= 0:
            raise ValueError("max_cost_usd must be positive")
