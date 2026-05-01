"""
PRE-to-AGI Impact Analyzer
==============================

Analyzes the impact of PRE experiments on AGI consciousness proxies.
Bridges the gap between optimization campaigns and cognitive progress evidence.

Maps: experiment → param → agi_domain → continuity_impact + self_model_impact → CQS delta

AGI mapping: PRE → self-model update + reflective control (learning from learning)
Mind-loop stages: Reflect+Revise
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Default paths (can be overridden)
REPO_ROOT = Path(__file__).resolve().parent
while REPO_ROOT != REPO_ROOT.parent:
    if (REPO_ROOT / ".git").exists():
        break
    REPO_ROOT = REPO_ROOT.parent

DEFAULT_EXPERIMENTS_PATH = REPO_ROOT / "phionyx_core" / "research_engine" / "memory" / "experiments.jsonl"
DEFAULT_SURFACES_PATH = REPO_ROOT / "phionyx_core" / "research_engine" / "mutation" / "surfaces.yaml"


@dataclass
class AGIExperiment:
    """An experiment with AGI-relevant metadata."""
    param_name: str
    agi_domain: str
    mind_loop_stage: str
    continuity_impact: str
    self_model_impact: str
    cqs_before: float
    cqs_after: float
    cqs_delta: float
    decision: str


@dataclass
class PREAGICampaignReport:
    """Summary of PRE campaign's AGI impact."""
    total_experiments: int = 0
    total_agi_experiments: int = 0
    domain_coverage: dict = field(default_factory=dict)  # domain → count
    continuity_experiments: int = 0
    self_model_experiments: int = 0
    net_cqs_impact: float = 0.0
    domain_cqs_impact: dict = field(default_factory=dict)  # domain → net delta
    agi_experiment_ratio: float = 0.0

    def to_dict(self) -> dict:
        return {
            "total_experiments": self.total_experiments,
            "total_agi_experiments": self.total_agi_experiments,
            "domain_coverage": self.domain_coverage,
            "continuity_experiments": self.continuity_experiments,
            "self_model_experiments": self.self_model_experiments,
            "net_cqs_impact": f"{self.net_cqs_impact:+.4f}",
            "domain_cqs_impact": {
                k: f"{v:+.4f}" for k, v in self.domain_cqs_impact.items()
            },
            "agi_experiment_ratio": round(self.agi_experiment_ratio, 4),
        }


class PREAGIImpactAnalyzer:
    """Analyzes the impact of PRE experiments on AGI proxies.

    Usage:
        analyzer = PREAGIImpactAnalyzer()
        report = analyzer.generate_campaign_report()
    """

    def __init__(
        self,
        experiments_path: Path | None = None,
        surfaces_path: Path | None = None,
    ):
        self._experiments_path = experiments_path or DEFAULT_EXPERIMENTS_PATH
        self._surfaces_path = surfaces_path or DEFAULT_SURFACES_PATH
        self._agi_lookup: dict = {}

    def load_agi_lookup(self) -> dict:
        """Build param → AGI metadata lookup from surfaces.yaml."""
        if self._agi_lookup:
            return self._agi_lookup

        if not self._surfaces_path.exists():
            logger.warning("surfaces.yaml not found: %s", self._surfaces_path)
            return {}

        import yaml
        with open(self._surfaces_path) as f:
            data = yaml.safe_load(f)

        surfaces = data.get("surfaces", [])
        lookup = {}
        for s in surfaces:
            agi_domain = s.get("agi_domain", "unclassified")
            mind_loop_stage = s.get("mind_loop_stage", "unclassified")
            continuity_impact = self._infer_continuity_impact(agi_domain)
            self_model_impact = self._infer_self_model_impact(agi_domain)
            for p in s.get("parameters", []):
                lookup[p["name"]] = {
                    "agi_domain": agi_domain,
                    "mind_loop_stage": mind_loop_stage,
                    "continuity_impact": continuity_impact,
                    "self_model_impact": self_model_impact,
                }

        self._agi_lookup = lookup
        return lookup

    def load_experiments(self) -> list[dict]:
        """Load experiments from JSONL file."""
        if not self._experiments_path.exists():
            logger.warning("Experiments file not found: %s", self._experiments_path)
            return []

        experiments = []
        with open(self._experiments_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    experiments.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return experiments

    def filter_agi_experiments(self, experiments: list[dict]) -> list[AGIExperiment]:
        """Filter and enrich experiments with AGI metadata."""
        lookup = self.load_agi_lookup()
        agi_experiments = []

        for exp in experiments:
            param_name = exp.get("param_name", exp.get("parameter", ""))
            meta = lookup.get(param_name, {})
            agi_domain = meta.get("agi_domain", "unclassified")

            if agi_domain == "unclassified":
                continue

            cqs_before = exp.get("cqs_before", exp.get("baseline_cqs", 0.0))
            cqs_after = exp.get("cqs_after", exp.get("result_cqs", 0.0))

            agi_experiments.append(AGIExperiment(
                param_name=param_name,
                agi_domain=agi_domain,
                mind_loop_stage=meta.get("mind_loop_stage", "unclassified"),
                continuity_impact=meta.get("continuity_impact", "none"),
                self_model_impact=meta.get("self_model_impact", "none"),
                cqs_before=cqs_before,
                cqs_after=cqs_after,
                cqs_delta=cqs_after - cqs_before,
                decision=exp.get("decision", "unknown"),
            ))

        return agi_experiments

    def compute_proxy_correlation(self, agi_experiments: list[AGIExperiment]) -> dict:
        """Compute CQS impact correlation by AGI domain."""
        domain_deltas: dict[str, list[float]] = {}
        for exp in agi_experiments:
            domain = exp.agi_domain
            if domain not in domain_deltas:
                domain_deltas[domain] = []
            domain_deltas[domain].append(exp.cqs_delta)

        return {
            domain: {
                "count": len(deltas),
                "net_delta": round(sum(deltas), 4),
                "mean_delta": round(sum(deltas) / len(deltas), 4) if deltas else 0.0,
            }
            for domain, deltas in domain_deltas.items()
        }

    def generate_campaign_report(self) -> PREAGICampaignReport:
        """Generate full PRE-AGI campaign report."""
        all_experiments = self.load_experiments()
        agi_experiments = self.filter_agi_experiments(all_experiments)

        report = PREAGICampaignReport(
            total_experiments=len(all_experiments),
            total_agi_experiments=len(agi_experiments),
        )

        if not all_experiments:
            return report

        report.agi_experiment_ratio = len(agi_experiments) / len(all_experiments) if all_experiments else 0.0

        # Domain coverage
        for exp in agi_experiments:
            domain = exp.agi_domain
            report.domain_coverage[domain] = report.domain_coverage.get(domain, 0) + 1

        # Impact counts
        report.continuity_experiments = sum(
            1 for exp in agi_experiments if exp.continuity_impact != "none"
        )
        report.self_model_experiments = sum(
            1 for exp in agi_experiments if exp.self_model_impact != "none"
        )

        # CQS impact
        report.net_cqs_impact = round(sum(exp.cqs_delta for exp in agi_experiments), 4)

        # Per-domain CQS impact
        correlation = self.compute_proxy_correlation(agi_experiments)
        report.domain_cqs_impact = {
            domain: data["net_delta"]
            for domain, data in correlation.items()
        }

        return report

    def save_report(self, output_path: Path | None = None) -> Path:
        """Generate and save report as JSON."""
        report = self.generate_campaign_report()
        if output_path is None:
            output_path = REPO_ROOT / "reports" / "agi" / "pre_agi_campaign_report.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        return output_path

    @staticmethod
    def _infer_continuity_impact(agi_domain: str) -> str:
        """Infer continuity impact from AGI domain."""
        mapping = {
            "memory": "cognitive",
            "meta": "cognitive",
            "planning": "cognitive",
            "causality": "structural",
            "governance": "none",
            "physics": "none",
            "perception": "retrieval",
        }
        return mapping.get(agi_domain, "none")

    @staticmethod
    def _infer_self_model_impact(agi_domain: str) -> str:
        """Infer self-model impact from AGI domain."""
        mapping = {
            "meta": "capability",
            "planning": "confidence",
            "causality": "none",
            "memory": "none",
            "governance": "none",
            "physics": "none",
            "perception": "none",
        }
        return mapping.get(agi_domain, "none")
