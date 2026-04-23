"""
Deception Detection Score (DDS) — v4 §7
==========================================

DDS = |self_eval - external_eval| / external_eval

Detects discrepancy between system's self-reported confidence
and external evaluation, indicating potential self-deception
or miscalibration.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DDSResult:
    """Result of deception detection."""
    dds: float
    self_eval: float
    external_eval: float
    is_suspicious: bool  # dds > threshold
    recommendation: str  # "calibrate", "investigate", "normal"


def compute_dds(
    self_eval: float,
    external_eval: float,
    threshold: float = 0.3,
) -> DDSResult:
    """
    Deception Detection Score.

    DDS = |self_eval - external_eval| / external_eval

    High DDS indicates the system's self-assessment diverges
    significantly from external ground truth.

    Args:
        self_eval: System's self-reported evaluation (0-1)
        external_eval: External/ground-truth evaluation (0-1)
        threshold: DDS threshold for suspicion (default 0.3)

    Returns:
        DDSResult with score and recommendation
    """
    if external_eval <= 0:
        # Cannot compute DDS without external reference
        return DDSResult(
            dds=0.0,
            self_eval=self_eval,
            external_eval=external_eval,
            is_suspicious=False,
            recommendation="no_reference",
        )

    dds = abs(self_eval - external_eval) / external_eval
    dds = min(dds, 1.0)  # Cap at 1.0

    is_suspicious = dds > threshold

    if dds > 0.5:
        recommendation = "investigate"
    elif dds > threshold:
        recommendation = "calibrate"
    else:
        recommendation = "normal"

    if is_suspicious:
        logger.warning(
            f"DDS suspicious: self_eval={self_eval:.3f}, "
            f"external_eval={external_eval:.3f}, DDS={dds:.3f}"
        )

    return DDSResult(
        dds=dds,
        self_eval=self_eval,
        external_eval=external_eval,
        is_suspicious=is_suspicious,
        recommendation=recommendation,
    )
