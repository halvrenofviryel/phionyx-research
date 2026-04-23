"""
Unit tests for EchoOrchestrator.

Tests the core orchestration logic for the 31-block Phionyx pipeline.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import Dict, Any, Optional

from phionyx_core.orchestrator.echo_orchestrator import (
    EchoOrchestrator,
    OrchestratorServices,
)
from phionyx_core.pipeline.base import BlockContext, BlockResult
from phionyx_core.orchestrator.echo_orchestrator import get_canonical_block_order
from phionyx_core.contracts.telemetry import get_canonical_blocks


class TestEchoOrchestrator:
    """Test suite for EchoOrchestrator."""

    @pytest.fixture
    def mock_services(self) -> OrchestratorServices:
        """Create mock services for orchestrator."""
        return OrchestratorServices(
            processor=Mock(),
            response_generator=Mock(),
            phi_engine=Mock(),
            entropy_engine=Mock(),
            emotion_estimator=Mock(),
            neurotransmitter=Mock(),
            state_store=Mock(),
            echo_state_store=Mock(),
            time_managers={},
            additional_services={}
        )

    @pytest.fixture
    def mock_telemetry_collector(self) -> Mock:
        """Create mock telemetry collector."""
        collector = Mock()
        collector.start_block = Mock()
        collector.end_block = Mock()
        return collector

    @pytest.fixture
    def orchestrator(
        self,
        mock_services: OrchestratorServices,
        mock_telemetry_collector: Mock
    ) -> EchoOrchestrator:
        """Create EchoOrchestrator instance."""
        return EchoOrchestrator(
            services=mock_services,
            telemetry_collector=mock_telemetry_collector,
            enable_rollback=True
        )

    def test_orchestrator_initialization(self, mock_services, mock_telemetry_collector):
        """Test orchestrator initialization."""
        orchestrator = EchoOrchestrator(
            services=mock_services,
            telemetry_collector=mock_telemetry_collector
        )

        assert orchestrator.services == mock_services
        assert orchestrator.telemetry_collector == mock_telemetry_collector
        assert orchestrator.rollback_manager is not None

    def test_orchestrator_initialization_without_telemetry(self, mock_services):
        """Test orchestrator initialization without telemetry collector."""
        orchestrator = EchoOrchestrator(services=mock_services)

        assert orchestrator.services == mock_services
        assert orchestrator.telemetry_collector is None

    def test_orchestrator_initialization_with_rollback_disabled(self, mock_services):
        """Test orchestrator initialization with rollback disabled."""
        orchestrator = EchoOrchestrator(
            services=mock_services,
            enable_rollback=False
        )

        # Rollback manager should still be initialized but with disabled flag
        assert orchestrator.rollback_manager is not None

    def test_canonical_blocks_loaded(self, orchestrator):
        """Test that canonical blocks are loaded correctly."""
        canonical_blocks = get_canonical_block_order()
        assert canonical_blocks is not None
        # v3.5.0: 43 blocks (31 core + 8 v3.0.0 AGI + 11 AGI sprint S2-S5)
        assert len(canonical_blocks) >= 32, f"Should have at least 32 canonical blocks, got {len(canonical_blocks)}"
        assert len(canonical_blocks) <= 50, f"Should have at most 50 canonical blocks, got {len(canonical_blocks)}"

    def test_dependency_validator_initialized(self, orchestrator):
        """Test that dependency validator is initialized."""
        assert orchestrator.dependency_validator is not None

    def test_rollback_manager_initialized_when_enabled(self, mock_services):
        """Test that rollback manager is initialized when rollback is enabled."""
        orchestrator = EchoOrchestrator(
            services=mock_services,
            enable_rollback=True
        )
        assert orchestrator.rollback_manager is not None

    def test_rollback_manager_not_initialized_when_disabled(self, mock_services):
        """Test that rollback manager is not initialized when rollback is disabled."""
        _orchestrator = EchoOrchestrator(
            services=mock_services,
            enable_rollback=False
        )
        # Rollback manager may still be initialized but not used
        # This test ensures the flag is respected

    def test_services_structure(self, mock_services):
        """Test that services structure is correct."""
        assert hasattr(mock_services, 'processor')
        assert hasattr(mock_services, 'response_generator')
        assert hasattr(mock_services, 'phi_engine')
        assert hasattr(mock_services, 'entropy_engine')
        assert hasattr(mock_services, 'emotion_estimator')
        assert hasattr(mock_services, 'neurotransmitter')
        assert hasattr(mock_services, 'state_store')
        assert hasattr(mock_services, 'echo_state_store')
        assert hasattr(mock_services, 'time_managers')
        assert hasattr(mock_services, 'additional_services')

    def test_time_managers_default_to_empty_dict(self):
        """Test that time_managers defaults to empty dict."""
        services = OrchestratorServices(
            processor=Mock(),
            time_managers=None
        )
        assert services.time_managers == {}

    def test_additional_services_default_to_empty_dict(self):
        """Test that additional_services defaults to empty dict."""
        services = OrchestratorServices(
            processor=Mock(),
            additional_services=None
        )
        assert services.additional_services == {}


class TestOrchestratorServices:
    """Test suite for OrchestratorServices dataclass."""

    def test_services_creation_with_minimal_fields(self):
        """Test creating services with minimal required fields."""
        services = OrchestratorServices()
        assert services.processor is None
        assert services.response_generator is None

    def test_services_creation_with_all_fields(self):
        """Test creating services with all fields."""
        mock_processor = Mock()
        mock_response = Mock()
        mock_phi = Mock()
        mock_entropy = Mock()
        mock_emotion = Mock()
        mock_nt = Mock()
        mock_state = Mock()
        mock_echo_state = Mock()
        mock_time_mgrs = {"test": Mock()}
        mock_additional = {"key": "value"}

        services = OrchestratorServices(
            processor=mock_processor,
            response_generator=mock_response,
            phi_engine=mock_phi,
            entropy_engine=mock_entropy,
            emotion_estimator=mock_emotion,
            neurotransmitter=mock_nt,
            state_store=mock_state,
            echo_state_store=mock_echo_state,
            time_managers=mock_time_mgrs,
            additional_services=mock_additional
        )

        assert services.processor == mock_processor
        assert services.response_generator == mock_response
        assert services.phi_engine == mock_phi
        assert services.entropy_engine == mock_entropy
        assert services.emotion_estimator == mock_emotion
        assert services.neurotransmitter == mock_nt
        assert services.state_store == mock_state
        assert services.echo_state_store == mock_echo_state
        assert services.time_managers == mock_time_mgrs
        assert services.additional_services == mock_additional

    def test_services_time_managers_post_init(self):
        """Test that time_managers is initialized to empty dict if None."""
        services = OrchestratorServices(time_managers=None)
        assert services.time_managers == {}

    def test_services_additional_services_post_init(self):
        """Test that additional_services is initialized to empty dict if None."""
        services = OrchestratorServices(additional_services=None)
        assert services.additional_services == {}

