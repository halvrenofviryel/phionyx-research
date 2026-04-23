"""Promotion pipeline manager — candidate -> promoted -> gold.

Manages experiment lifecycle beyond the initial keep/revert/park decision.
Reads from experiments.jsonl, maintains its own promotion_registry.json.

Promotion criteria (PROGRAM.md Section 9):
  - candidate: passed all guardrails, CQS improved, decision="keep"
  - promoted: human review approved, re-verified against baseline
  - gold: shadow evaluation confirms stability over time
"""
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PromotionRecord:
    experiment_id: str
    promotion_status: str  # "candidate", "promoted", "gold"
    promoted_at: str | None = None
    promoted_by: str | None = None
    gold_at: str | None = None
    gold_reason: str | None = None
    shadow_cqs: float | None = None
    notes: str = ""


class PromotionManager:
    """Manages the experiment promotion pipeline.

    Separate from the experiment store (Tier D) — this is a Tier B
    component that can be modified by the research engine.
    """

    def __init__(self, data_dir: str = "data/research_engine"):
        self._data_dir = Path(data_dir)
        self._registry_path = self._data_dir / "promotion_registry.json"
        self._experiments_path = self._data_dir / "experiments.jsonl"
        self._registry: dict[str, dict[str, Any]] = self._load_registry()

    def _load_registry(self) -> dict[str, dict[str, Any]]:
        if not self._registry_path.exists():
            return {}
        try:
            with open(self._registry_path) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_registry(self) -> None:
        self._data_dir.mkdir(parents=True, exist_ok=True)
        with open(self._registry_path, "w") as f:
            json.dump(self._registry, f, indent=2)

    def _load_experiments(self) -> list[dict[str, Any]]:
        if not self._experiments_path.exists():
            return []
        experiments = []
        with open(self._experiments_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    experiments.append(json.loads(line))
        return experiments

    def get_candidates(self) -> list[dict[str, Any]]:
        """Get experiments eligible for promotion (status=candidate, decision=keep)."""
        experiments = self._load_experiments()
        candidates = []
        for exp in experiments:
            exp_id = exp.get("experiment_id", "")
            if exp.get("decision") == "keep" and exp.get("status") == "candidate":
                reg = self._registry.get(exp_id, {})
                promo_status = reg.get("promotion_status", "candidate")
                candidates.append({**exp, "promotion_status": promo_status})
            elif exp_id in self._registry:
                # Already promoted/gold
                reg = self._registry[exp_id]
                candidates.append({**exp, "promotion_status": reg["promotion_status"]})
        return candidates

    def get_promoted(self) -> list[dict[str, Any]]:
        """Get experiments in 'promoted' status."""
        return self._get_by_promo_status("promoted")

    def get_gold(self) -> list[dict[str, Any]]:
        """Get experiments in 'gold' status."""
        return self._get_by_promo_status("gold")

    def _get_by_promo_status(self, status: str) -> list[dict[str, Any]]:
        experiments = self._load_experiments()
        exp_map = {e["experiment_id"]: e for e in experiments}
        result = []
        for exp_id, reg in self._registry.items():
            if reg.get("promotion_status") == status and exp_id in exp_map:
                result.append({**exp_map[exp_id], **reg})
        return result

    def promote(
        self,
        experiment_id: str,
        promoted_by: str = "founder",
        notes: str = "",
    ) -> dict[str, Any]:
        """Promote experiment: candidate -> promoted.

        Requires human review approval.
        """
        # Verify experiment exists and is a candidate
        experiments = self._load_experiments()
        exp = None
        for e in experiments:
            if e.get("experiment_id") == experiment_id:
                exp = e
                break

        if exp is None:
            return {"error": f"Experiment {experiment_id} not found"}

        if exp.get("decision") != "keep":
            return {"error": f"Only 'keep' experiments can be promoted (got: {exp.get('decision')})"}

        current = self._registry.get(experiment_id, {})
        current_status = current.get("promotion_status", "candidate")

        if current_status == "gold":
            return {"error": "Already at gold status"}

        if current_status == "promoted":
            return {"error": "Already promoted — use promote_to_gold()"}

        self._registry[experiment_id] = {
            "promotion_status": "promoted",
            "promoted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "promoted_by": promoted_by,
            "notes": notes,
        }
        self._save_registry()

        return {"ok": True, "experiment_id": experiment_id, "status": "promoted"}

    def promote_to_gold(
        self,
        experiment_id: str,
        shadow_cqs: float | None = None,
        shadow_verdict: str | None = None,
        reason: str = "",
        force: bool = False,
    ) -> dict[str, Any]:
        """Promote experiment: promoted -> gold.

        Requires shadow evaluation confirmation. The shadow_verdict must be
        "pass" or "partial" (unless force=True). This prevents gold promotion
        without independent validation.
        """
        current = self._registry.get(experiment_id)
        if current is None:
            return {"error": f"Experiment {experiment_id} not in promotion registry"}

        if current.get("promotion_status") != "promoted":
            return {"error": f"Must be 'promoted' to advance to gold (got: {current.get('promotion_status')})"}

        # Shadow eval gate: require verdict unless forced
        if not force:
            if shadow_verdict is None:
                return {"error": "Shadow evaluation required for gold promotion. Run shadow eval first or use force=True."}
            if shadow_verdict not in ("pass", "partial"):
                return {"error": f"Shadow verdict '{shadow_verdict}' does not qualify for gold. Must be 'pass' or 'partial'."}

        current["promotion_status"] = "gold"
        current["gold_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        current["gold_reason"] = reason or f"Shadow evaluation: {shadow_verdict or 'forced'}"
        current["shadow_verdict"] = shadow_verdict
        if shadow_cqs is not None:
            current["shadow_cqs"] = shadow_cqs

        self._save_registry()

        return {"ok": True, "experiment_id": experiment_id, "status": "gold", "shadow_verdict": shadow_verdict}

    def demote(self, experiment_id: str, reason: str = "") -> dict[str, Any]:
        """Demote experiment back to candidate (e.g., regression detected)."""
        if experiment_id not in self._registry:
            return {"error": f"Experiment {experiment_id} not in registry"}

        self._registry[experiment_id] = {
            "promotion_status": "candidate",
            "demoted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "demote_reason": reason,
        }
        self._save_registry()

        return {"ok": True, "experiment_id": experiment_id, "status": "candidate"}

    def get_summary(self) -> dict[str, int]:
        """Get promotion pipeline summary counts."""
        experiments = self._load_experiments()
        total_kept = sum(1 for e in experiments if e.get("decision") == "keep")

        counts = {"candidate": 0, "promoted": 0, "gold": 0}
        for reg in self._registry.values():
            status = reg.get("promotion_status", "candidate")
            if status in counts:
                counts[status] += 1

        # Candidates = kept experiments not yet in registry
        unregistered = total_kept - sum(counts.values())
        counts["candidate"] += max(0, unregistered)

        return counts

    def get_registry(self) -> dict[str, dict[str, Any]]:
        """Get the full promotion registry."""
        return dict(self._registry)
