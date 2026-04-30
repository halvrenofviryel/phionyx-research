"""
UKF Measurement Integration - Measurement Mapper for UKF
=========================================================

Integration between MeasurementMapper and UKF EchoStateEstimator.

Ensures:
- UKF update uses measurement from mapper (not direct state)
- R matrix is dynamically adjusted based on confidence
- CEP metrics remain separate (quality layer, not measurement)
"""

from __future__ import annotations

from typing import Any

import numpy as np

from phionyx_core.state.measurement_mapper import MeasurementMapper, MeasurementVector

# Import UKF if available
try:
    from echo_state_estimator import EchoStateEstimator, EchoStateVector
    UKF_AVAILABLE = True
except ImportError:
    UKF_AVAILABLE = False
    EchoStateEstimator = None
    EchoStateVector = None


class UKFMeasurementIntegration:
    """
    Integration between MeasurementMapper and UKF.

    Responsibilities:
    - Convert LLM output to measurement vector
    - Adjust R matrix based on confidence
    - Update UKF with measurement
    """

    def __init__(self, measurement_mapper: MeasurementMapper | None = None):
        """
        Initialize UKF measurement integration.

        Args:
            measurement_mapper: MeasurementMapper instance (default: create new)
        """
        self.mapper = measurement_mapper or MeasurementMapper()

    def create_measurement_from_llm(
        self,
        llm_text: str,
        llm_output: dict[str, Any] | None = None
    ) -> MeasurementVector:
        """
        Create measurement vector from LLM output.

        Args:
            llm_text: LLM output text
            llm_output: Optional structured LLM output

        Returns:
            MeasurementVector
        """
        return self.mapper.map_text_to_measurement(llm_text, llm_output)

    def convert_measurement_to_ukf_state(
        self,
        measurement: MeasurementVector,
        current_state: EchoStateVector | None = None
    ) -> EchoStateVector:
        """
        Convert measurement vector to UKF state vector.

        UKF state: [phi, entropy, valence, arousal, trust, regulation]
        Measurement: [A_meas, V_meas, H_meas, confidence]

        Mapping:
        - valence <- V_meas
        - arousal <- A_meas
        - entropy <- H_meas
        - phi: computed from A, V, H (or use current if available)
        - trust: use current or default
        - regulation: use current or default

        Args:
            measurement: MeasurementVector
            current_state: Current UKF state (for phi, trust, regulation)

        Returns:
            EchoStateVector for UKF update
        """
        if not UKF_AVAILABLE:
            raise ImportError("UKF not available")

        # Extract from measurement
        V_meas = measurement.V_meas
        A_meas = measurement.A_meas
        H_meas = measurement.H_meas

        # Use current state for phi, trust, regulation if available
        if current_state:
            phi = current_state.phi
            trust = current_state.trust
            regulation = current_state.regulation
        else:
            # Default values
            phi = 0.5
            trust = 0.5
            regulation = 0.5

        return EchoStateVector(
            phi=phi,
            entropy=H_meas,
            valence=V_meas,
            arousal=A_meas,
            trust=trust,
            regulation=regulation
        )

    def update_ukf_with_measurement(
        self,
        ukf_estimator: EchoStateEstimator,
        measurement: MeasurementVector,
        current_state: EchoStateVector | None = None
    ) -> EchoStateVector:
        """
        Update UKF with measurement from mapper.

        Steps:
        1. Convert measurement to UKF state vector
        2. Adjust R matrix based on confidence (Echoism Core v1.0: Dynamic R adaptation)
        3. Update UKF with measurement

        Per Echoism Core v1.0:
        - Low confidence -> High noise (R increases)
        - High confidence -> Low noise (R decreases)
        - R matrix is dynamically adjusted: R = base_noise / confidence

        Args:
            ukf_estimator: UKF EchoStateEstimator instance
            measurement: MeasurementVector from mapper
            current_state: Current UKF state (for mapping)

        Returns:
            Updated state vector
        """
        if not UKF_AVAILABLE:
            raise ImportError("UKF not available")

        # Convert measurement to UKF state
        measurement_state = self.convert_measurement_to_ukf_state(measurement, current_state)

        # Echoism Core v1.0: Dynamically adjust R matrix based on confidence
        # R = base_noise / confidence (with bounds)
        R_matrix = self.mapper.create_measurement_noise_matrix(
            confidence=measurement.confidence,
            base_noise=ukf_estimator.config.measurement_noise,
            state_dim=ukf_estimator.n
        )

        # Store R_noise_before for logging
        R_noise_before = ukf_estimator.R[0][0] if hasattr(ukf_estimator, 'R') and ukf_estimator.R is not None else None

        # Update UKF R matrix (dynamic adaptation based on confidence)
        ukf_estimator.R = np.array(R_matrix)

        R_noise_after = ukf_estimator.R[0][0]

        # Log R matrix adaptation (if logging available)
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(
            f"UKF R Matrix Adaptation (Echoism Core v1.0): "
            f"confidence={measurement.confidence:.3f} → "
            f"R_noise: {R_noise_before:.4f} -> {R_noise_after:.4f} "
            f"(low confidence={measurement.confidence < 0.5} → high noise={R_noise_after > 0.1})"
        )

        # Update UKF with measurement
        updated_state = ukf_estimator.update(measurement_state)

        return updated_state

    def process_llm_output_for_ukf(
        self,
        ukf_estimator: EchoStateEstimator,
        llm_text: str,
        llm_output: dict[str, Any] | None = None,
        current_state: EchoStateVector | None = None
    ) -> tuple[MeasurementVector, EchoStateVector]:
        """
        Process LLM output and update UKF in one step.

        Args:
            ukf_estimator: UKF EchoStateEstimator instance
            llm_text: LLM output text
            llm_output: Optional structured LLM output
            current_state: Current UKF state

        Returns:
            Tuple of (MeasurementVector, updated EchoStateVector)
        """
        # Create measurement from LLM
        measurement = self.create_measurement_from_llm(llm_text, llm_output)

        # Update UKF with measurement
        updated_state = self.update_ukf_with_measurement(
            ukf_estimator,
            measurement,
            current_state
        )

        return measurement, updated_state

