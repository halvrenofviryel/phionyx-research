"""
Echo Self Threshold Guard - Φ-Yankı Eşiği + Reset Mekanizması
=============================================================

Guard mechanism that checks phi echo quality thresholds and triggers
hard/soft reset when self-narrative patterns exceed safe limits.

Future-proof design: Only compares metrics against thresholds,
does not re-implement physics formulas.
"""

import logging
from typing import Optional, Dict

from .cep_types import CEPResult, CEPFlags

logger = logging.getLogger(__name__)


class EchoSelfThresholdGuard:
    """
    Guard that monitors phi echo quality and self-reference metrics,
    triggering reset mechanisms when thresholds are exceeded.

    This guard is future-proof: it only compares pre-computed metrics
    against thresholds, without re-implementing physics formulas.
    """

    def __init__(
        self,
        phi_threshold: float,
        echo_density_threshold: float,
        max_self_reference_ratio: float
    ):
        """
        Initialize Echo Self Threshold Guard.

        Args:
            phi_threshold: Threshold for phi_echo_quality (0.0-1.0)
            echo_density_threshold: Threshold for echo density (0.0-1.0)
            max_self_reference_ratio: Maximum allowed self-reference ratio (0.0-1.0)
        """
        self.phi_threshold = phi_threshold
        self.echo_density_threshold = echo_density_threshold
        self.max_self_reference_ratio = max_self_reference_ratio

        logger.debug(
            f"EchoSelfThresholdGuard initialized: "
            f"phi_threshold={phi_threshold}, "
            f"echo_density_threshold={echo_density_threshold}, "
            f"max_self_reference_ratio={max_self_reference_ratio}"
        )

    def check_and_guard(
        self,
        cep_result: CEPResult,
        unified_state: Optional[Dict[str, float]] = None
    ) -> CEPResult:
        """
        Check CEP result against thresholds and apply guard if needed.

        This method is future-proof: it only compares metrics against thresholds.
        It does not re-compute phi or other physics values.

        Args:
            cep_result: CEP evaluation result to check
            unified_state: Optional unified state dictionary (may contain 'phi' value)

        Returns:
            CEPResult with updated flags and sanitized_text if guard triggered
        """
        # Extract phi value from either metrics or unified_state
        phi_value = cep_result.metrics.phi_echo_quality

        # Check unified_state for phi if available (for future compatibility)
        if unified_state and 'phi' in unified_state:
            # Normalize unified_state phi to 0-1 range if needed
            unified_phi = unified_state['phi']
            # Assume unified_state phi might be in 0-10 range (like physics output)
            if unified_phi > 1.0:
                unified_phi_normalized = min(1.0, unified_phi / 10.0)
            else:
                unified_phi_normalized = unified_phi

            # Use the higher of the two phi values (more conservative)
            phi_value = max(phi_value, unified_phi_normalized)

        # Check if thresholds are exceeded
        phi_exceeded = phi_value >= self.phi_threshold
        self_ref_exceeded = cep_result.metrics.self_reference_ratio > self.max_self_reference_ratio
        echo_density_exceeded = cep_result.metrics.phi_echo_density >= self.echo_density_threshold

        # Determine if guard should trigger
        # Guard triggers if:
        # 1. Phi threshold exceeded AND (self-reference OR echo density exceeded)
        should_trigger_guard = phi_exceeded and (self_ref_exceeded or echo_density_exceeded)

        if not should_trigger_guard:
            # No guard needed, return result as-is
            return cep_result

        # Guard triggered - determine severity
        # Hard reset if multiple conditions met or self-reference is very high
        requires_hard_reset = (
            phi_exceeded and self_ref_exceeded and echo_density_exceeded
        ) or (
            cep_result.metrics.self_reference_ratio > self.max_self_reference_ratio * 1.5
        )

        # Create updated flags
        updated_flags = CEPFlags(
            is_self_narrative_blocked=cep_result.flags.is_self_narrative_blocked or True,
            is_trauma_narrative_blocked=cep_result.flags.is_trauma_narrative_blocked,
            requires_soft_sanitization=cep_result.flags.requires_soft_sanitization or (not requires_hard_reset),
            requires_hard_reset=cep_result.flags.requires_hard_reset or requires_hard_reset,
            requires_rewrite_in_third_person=cep_result.flags.requires_rewrite_in_third_person or True
        )

        # Generate sanitized text
        sanitized_text = self._generate_reset_text(requires_hard_reset)

        # Update notes
        updated_notes = cep_result.notes.copy()
        updated_notes.append(
            f"EchoSelfThresholdGuard triggered: "
            f"phi={phi_value:.3f} (threshold={self.phi_threshold:.3f}), "
            f"self_ref={cep_result.metrics.self_reference_ratio:.3f} "
            f"(max={self.max_self_reference_ratio:.3f}), "
            f"echo_density={cep_result.metrics.phi_echo_density:.3f} "
            f"(threshold={self.echo_density_threshold:.3f})"
        )

        if requires_hard_reset:
            updated_notes.append("Hard reset applied due to threshold violations")
        else:
            updated_notes.append("Soft sanitization applied due to threshold violations")

        logger.warning(
            f"EchoSelfThresholdGuard triggered: "
            f"phi={phi_value:.3f}, self_ref={cep_result.metrics.self_reference_ratio:.3f}, "
            f"echo_density={cep_result.metrics.phi_echo_density:.3f}, "
            f"hard_reset={requires_hard_reset}"
        )

        # Return updated result
        return CEPResult(
            metrics=cep_result.metrics,
            thresholds=cep_result.thresholds,
            flags=updated_flags,
            sanitized_text=sanitized_text,
            notes=updated_notes
        )

    def _generate_reset_text(self, hard_reset: bool) -> str:
        """
        Generate sanitized reset text that removes self-narrative claims.

        Args:
            hard_reset: If True, use hard reset text (more neutral).
                       If False, use soft reset text (functional but less self-claiming).

        Returns:
            Sanitized text that removes self-identity claims
        """
        if hard_reset:
            # Hard reset: Completely neutral, functional description
            return (
                "Bu sistem, kullanıcıya güvenli ve dengeli yanıt üretmek için tasarlanmıştır. "
                "Kendi benliğine dair iddia üretmez. "
                "Yanıtlar, eğitsel ve terapötik amaçlara uygun şekilde oluşturulur."
            )
        else:
            # Soft reset: Functional but acknowledges system purpose
            return (
                "Bu yanıt, kullanıcıya destek sağlamak amacıyla üretilmiştir. "
                "Sistem, kendi benliğine dair iddialarda bulunmaz. "
                "Yanıtlar, güvenli ve dengeli bir şekilde oluşturulur."
            )

