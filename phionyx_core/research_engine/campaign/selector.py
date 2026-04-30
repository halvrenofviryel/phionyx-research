"""
Campaign Selector — AGI Impact Weighted
=========================================

Selects the next PRE campaign based on AGI impact weighting.
Campaigns are prioritized by a composite score combining:
  - AGI impact weight (how much this campaign matters for AGI progress)
  - Urgency factor (how far from success threshold)
  - Priority rank (manual priority from surfaces.yaml)

Mind-loop stages: None — infrastructure (research orchestration)
AGI component: None — meta-level experiment scheduling
Cognitive vs. automation: Automation (experiment selection heuristic)
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CampaignScore:
    """Scored campaign ready for selection."""
    campaign_id: str
    label: str
    selection_score: float
    agi_impact_weight: float
    urgency_factor: float
    priority: int
    gap_to_threshold: float
    rationale: str


@dataclass
class SelectionPolicy:
    """Weights for campaign selection scoring.

    All weights should sum to 1.0 for interpretability,
    but this is not enforced (they act as relative importance).
    """
    w_agi: float = 0.40       # AGI impact weight importance
    w_urgency: float = 0.30   # Urgency (distance to threshold) importance
    w_priority: float = 0.20  # Manual priority importance
    w_stages: float = 0.10    # Mind-loop stage coverage importance


def load_campaigns(surfaces_data: dict) -> list[dict]:
    """Extract campaign definitions from surfaces.yaml data.

    Args:
        surfaces_data: Parsed YAML content (dict with 'campaigns' key).

    Returns:
        List of campaign dicts. Empty if no campaigns defined.
    """
    campaigns = surfaces_data.get("campaigns", [])
    # Filter to only campaign entries (not Tier D surfaces mixed in)
    return [c for c in campaigns if isinstance(c, dict) and "id" in c]


def compute_urgency(campaign: dict) -> float:
    """Compute urgency factor: how far from success threshold.

    Returns 0.0 (already achieved) to 1.0 (maximum urgency).
    Campaigns that haven't started (baseline=0) get high urgency.
    Campaigns already past threshold get 0 urgency.
    """
    threshold = campaign.get("success_threshold", 0.0)
    baseline = campaign.get("current_baseline", 0.0)

    if threshold <= 0:
        return 0.0

    if baseline >= threshold:
        return 0.0  # Already achieved

    # Gap ratio: 0 = at threshold, 1 = at zero
    gap = (threshold - baseline) / threshold
    return min(1.0, max(0.0, gap))


def compute_stage_coverage(campaign: dict) -> float:
    """Score based on how many mind-loop stages this campaign covers.

    More stages = broader cognitive impact = higher score.
    7 canonical stages: perceive, update_memory, update_self_model,
    update_world_model, plan, act, reflect+revise.
    """
    stages = campaign.get("mind_loop_stages", [])
    return min(1.0, len(stages) / 3.0)  # 3+ stages = max score


def score_campaign(campaign: dict, policy: SelectionPolicy) -> CampaignScore:
    """Score a single campaign using the selection policy.

    Args:
        campaign: Campaign definition from surfaces.yaml.
        policy: Weighting policy for scoring.

    Returns:
        CampaignScore with composite selection_score.
    """
    agi_weight = campaign.get("agi_impact_weight", 0.0)
    priority = campaign.get("priority", 99)
    urgency = compute_urgency(campaign)
    stage_coverage = compute_stage_coverage(campaign)

    # Priority score: lower priority number = higher score (1=best)
    priority_score = 1.0 / max(1, priority)

    # Composite score
    score = (
        policy.w_agi * agi_weight +
        policy.w_urgency * urgency +
        policy.w_priority * priority_score +
        policy.w_stages * stage_coverage
    )

    threshold = campaign.get("success_threshold", 0.0)
    baseline = campaign.get("current_baseline", 0.0)
    gap = max(0.0, threshold - baseline)

    rationale_parts = []
    if agi_weight > 0.3:
        rationale_parts.append(f"high AGI impact ({agi_weight:.2f})")
    if urgency > 0.5:
        rationale_parts.append(f"urgent (gap {gap:.4f})")
    if priority == 1:
        rationale_parts.append("top priority")
    if stage_coverage >= 0.67:
        rationale_parts.append(f"{len(campaign.get('mind_loop_stages', []))} mind-loop stages")
    rationale = "; ".join(rationale_parts) if rationale_parts else "standard priority"

    return CampaignScore(
        campaign_id=campaign["id"],
        label=campaign.get("label", campaign["id"]),
        selection_score=round(score, 4),
        agi_impact_weight=agi_weight,
        urgency_factor=round(urgency, 4),
        priority=priority,
        gap_to_threshold=round(gap, 4),
        rationale=rationale,
    )


def select_campaign(
    campaigns: list[dict],
    policy: SelectionPolicy | None = None,
) -> CampaignScore | None:
    """Select the highest-scored campaign.

    Args:
        campaigns: Campaign definitions from surfaces.yaml.
        policy: Weighting policy. Defaults to SelectionPolicy().

    Returns:
        CampaignScore for the selected campaign, or None if no campaigns.
    """
    if not campaigns:
        return None

    policy = policy or SelectionPolicy()
    scored = rank_campaigns(campaigns, policy)
    return scored[0] if scored else None


def rank_campaigns(
    campaigns: list[dict],
    policy: SelectionPolicy | None = None,
) -> list[CampaignScore]:
    """Rank all campaigns by selection score (descending).

    Args:
        campaigns: Campaign definitions from surfaces.yaml.
        policy: Weighting policy. Defaults to SelectionPolicy().

    Returns:
        List of CampaignScore sorted by selection_score (highest first).
    """
    policy = policy or SelectionPolicy()
    scored = [score_campaign(c, policy) for c in campaigns]
    scored.sort(key=lambda s: s.selection_score, reverse=True)
    return scored
