"""
Block Factory
=============

Factory for creating all 46 pipeline blocks with their dependencies.
Includes 31 core blocks + 8 v3.0.0 AGI blocks + 12 AGI sprint blocks (S2-S5 + feedback).
Contract v3.8.0.
"""

import logging
from typing import Dict, Any, Optional

from ..pipeline.blocks import (
    # Core blocks (31)
    TimeUpdateSotBlock,
    EchoOntologyEventTraceBlock,
    EmotionFromNeurotransmitterBlock,
    EmotionEstimationBlock,
    CreateScenarioFrameBlock,
    InitializeUnifiedStateBlock,
    UkfPredictBlock,
    CognitiveLayerBlock,
    EchoOntologyTransformationBlock,
    InputSafetyGateBlock,  # Combined: low_input_gate + safety_layer_pre_cep
    IntentClassificationBlock,  # Intent classification block
    ContextRetrievalRagBlock,  # Context retrieval RAG block
    EntropyAmplitudePreGateBlock,
    CepEvaluationBlock,
    EthicsPreResponseBlock,
    NarrativeLayerBlock,
    EthicsPostResponseBlock,
    BehavioralDriftDetectionBlock,  # Silent Failure Firewall
    UnifiedStateUpdateEscBlock,
    PhiPublishBlock,
    EscStateHelperUpdateBlock,
    DriveCoherenceUpdateBlock,
    CoherenceQaBlock,
    EntropyAmplitudePostGateBlock,
    NeurotransmitterMemoryGrowthBlock,
    AuditLayerBlock,
    PhiFinalizeBlock,
    StateUpdatePhysicsBlock,
    ResponseBuildBlock,
    PhiComputationBlock,
    EntropyComputationBlock,
    # v3.0.0 AGI World Model blocks (8)
    KillSwitchGateBlock,
    PerceptualFrameEmitBlock,
    GoalEvaluationBlock,
    WorldStateSnapshotBlock,
    ConfidenceFusionBlock,
    ArbitrationResolveBlock,
    ActionIntentGateBlock,
    LearningGateBlock,
    WorkspaceBroadcastBlock,
    # AGI Sprint Pipeline Binding blocks S2-S5 (11)
    SelfModelAssessmentBlock,
    KnowledgeBoundaryCheckBlock,
    MemoryConsolidationBlock,
    CausalGraphUpdateBlock,
    CausalInterventionBlock,
    CounterfactualAnalysisBlock,
    RootCauseAnalysisBlock,
    CausalSimulationBlock,
    TrustEvaluationBlock,
    GoalDecompositionBlock,
    DeliberativeEthicsGateBlock,
    # Feedback Loop Block (v3.6.0)
    OutcomeFeedbackBlock,
)

from .echo_orchestrator import OrchestratorServices

logger = logging.getLogger(__name__)

# Import EmotionCache here to avoid circular imports
try:
    from phionyx_core.memory.emotion_cache import EmotionCache as _EmotionCacheClass
    _EMOTION_CACHE_AVAILABLE = True
except ImportError:
    _EmotionCacheClass = None
    _EMOTION_CACHE_AVAILABLE = False
    logger.warning("EmotionCache not available, emotion_estimation will create its own cache")


def create_all_blocks(
    services: OrchestratorServices,
    engine_instance: Optional[Any] = None,
    participant_id: Optional[str] = None,
    emotion_cache: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Create all 43 pipeline blocks with their dependencies.

    Includes: 31 core + 8 v3.0.0 AGI + 11 AGI sprint (S2-S5) blocks.
    AGI blocks use graceful DI: None dependency → block returns status="skipped".

    Args:
        services: Orchestrator services
        engine_instance: Engine instance (for accessing self attributes)
        participant_id: Participant ID for participant-scoped services

    Returns:
        Dictionary mapping block_id to block instance
    """
    blocks = {}

    # Get time manager for participant
    time_manager = None
    logger.debug(f"[BLOCK_FACTORY] Looking up TimeManager: participant_id={participant_id}, time_managers keys={list(services.time_managers.keys()) if services.time_managers else 'None'}")

    if services.time_managers and participant_id:
        time_manager = services.time_managers.get(participant_id)
        logger.debug(f"[BLOCK_FACTORY] Found TimeManager for participant_id={participant_id}: {time_manager is not None}")

    if not time_manager and services.time_managers:
        # Fallback: try "default" key first, then first available
        time_manager = services.time_managers.get("default")
        logger.debug(f"[BLOCK_FACTORY] Found TimeManager for 'default': {time_manager is not None}")
        if not time_manager:
            # Fallback to first available
            time_manager = next(iter(services.time_managers.values())) if services.time_managers else None
            logger.debug(f"[BLOCK_FACTORY] Found TimeManager from first available: {time_manager is not None}")

    # DEPRECATED: api_process_decision - Moved to middleware (RequestProcessorMiddleware)
    # This block is now handled by middleware before pipeline execution
    # blocks["api_process_decision"] = ApiProcessDecisionBlock()  # DEPRECATED

    # DEPRECATED: engine_ensure_initialized - Moved to middleware (EngineInitializerMiddleware)
    # This block is now handled by middleware before pipeline execution
    # if engine_instance:
    #     def initialization_checker() -> None:
    #         """Initialize engine instance."""
    #         engine_instance._ensure_initialized()
    #     blocks["engine_ensure_initialized"] = EngineEnsureInitializedBlock(
    #         initialization_checker=initialization_checker
    #     )
    # else:
    #     # Fallback: no-op checker
    #     blocks["engine_ensure_initialized"] = EngineEnsureInitializedBlock(
    #         initialization_checker=lambda: None
    #     )

    # 3. time_update_sot - Needs TimeManager
    if time_manager:
        blocks["time_update_sot"] = TimeUpdateSotBlock(
            time_manager=time_manager,
            participant_id=participant_id or "default"
        )
    else:
        logger.warning("TimeManager not available for time_update_sot block")
        # Will be skipped by should_skip()
        blocks["time_update_sot"] = TimeUpdateSotBlock(
            time_manager=None,  # type: ignore
            participant_id=participant_id or "default"
        )

    # 4. echo_ontology_event_trace - Needs processor with event trace method
    if services.processor and hasattr(services.processor, 'process_echo_ontology_event_and_trace'):
        class EchoOntologyTracerAdapter:
            def __init__(self, processor):
                self.processor = processor

            def process_event_and_trace(self, user_input, card_type, card_title, scene_context, t_now):
                return self.processor.process_echo_ontology_event_and_trace(
                    user_input=user_input,
                    card_type=card_type,
                    card_title=card_title,
                    scene_context=scene_context,
                    t_now=t_now
                )

        blocks["echo_ontology_event_trace"] = EchoOntologyEventTraceBlock(
            tracer=EchoOntologyTracerAdapter(services.processor)
        )

    # 5. emotion_from_neurotransmitter - Needs processor with neurotransmitter method
    if services.processor and hasattr(services.processor, 'get_emotion_from_neurotransmitter'):
        class NeurotransmitterEmotionAdapter:
            def __init__(self, processor: Any) -> None:
                """Initialize adapter with processor."""
                self.processor = processor

            def get_emotion(self, user_input: str, mode: Optional[str] = None) -> Any:
                """Get emotion from neurotransmitter."""
                return self.processor.get_emotion_from_neurotransmitter(
                    user_input=user_input,
                    mode=mode
                )

        blocks["emotion_from_neurotransmitter"] = EmotionFromNeurotransmitterBlock(
            neurotransmitter=NeurotransmitterEmotionAdapter(services.processor) if services.processor else None
        )

    # 6. emotion_estimation - Needs emotion_estimator
    # CRITICAL: Use shared emotion_cache for determinism across all executions
    # This ensures same input → same output even in parallel execution
    if _EMOTION_CACHE_AVAILABLE and _EmotionCacheClass is not None:
        shared_emotion_cache = emotion_cache or _EmotionCacheClass(max_size=10000, enable_metrics=True)
    else:
        # Fallback: Use provided cache or None (EmotionEstimationBlock will create its own)
        shared_emotion_cache = emotion_cache

    blocks["emotion_estimation"] = EmotionEstimationBlock(
        emotion_estimator=services.emotion_estimator,
        emotion_cache=shared_emotion_cache
    )

    # 7. create_scenario_frame - Needs processor with create_scenario_frame method
    if services.processor and hasattr(services.processor, 'create_scenario_frame'):
        class ScenarioFrameCreatorAdapter:
            def __init__(self, processor: Any) -> None:
                """Initialize adapter with processor."""
                self.processor = processor

            def create_scenario_frame(
                self,
                user_input: str,
                card_type: str,
                card_title: str,
                scene_context: str,
                card_result: str,
                physics_params: Any
            ) -> Any:
                """Create scenario frame."""
                return self.processor.create_scenario_frame(
                    user_input=user_input,
                    session_id=None,  # Will be set from context
                    scenario_id=None,  # Will be set from context
                    scenario_step_id=None,  # Will be set from context
                    time_delta=1.0,  # Will be set from context
                    valence_from_emotion=0.0,  # Will be set from context
                    arousal_from_emotion=0.5,  # Will be set from context
                    mode=None  # Will be set from context
                )

        blocks["create_scenario_frame"] = CreateScenarioFrameBlock(
            frame_creator=ScenarioFrameCreatorAdapter(services.processor)
        )
    else:
        # Fallback: block skips via should_skip() when frame_creator=None
        blocks["create_scenario_frame"] = CreateScenarioFrameBlock(frame_creator=None)

    # 8. initialize_unified_state - Needs processor with initialize_unified_state_for_frame
    if services.processor and hasattr(services.processor, 'initialize_unified_state_for_frame'):
        class UnifiedStateInitializerAdapter:
            def __init__(self, processor: Any) -> None:
                """Initialize adapter with processor."""
                self.processor = processor

            def initialize_unified_state(
                self,
                frame: Any,
                time_delta: float,
                physics_params: Any
            ) -> Any:
                """Initialize unified state."""
                return self.processor.initialize_unified_state_for_frame(
                    frame=frame,
                    previous_phi=None,  # Will be set from context
                    current_entropy=0.5,  # Will be set from context
                    valence_from_emotion=0.0,  # Will be set from context
                    arousal_from_emotion=0.5,  # Will be set from context
                    turn_count=0,  # Will be set from context
                    session_id=None,  # Will be set from context
                    initialize_ukf_callback=None
                )

        blocks["initialize_unified_state"] = InitializeUnifiedStateBlock(
            initializer=UnifiedStateInitializerAdapter(services.processor)
        )
    else:
        # Fallback: block skips via should_skip() when initializer=None
        blocks["initialize_unified_state"] = InitializeUnifiedStateBlock(initializer=None)

    # 9. ukf_predict - Needs processor for UKF Kalman prediction
    if services.processor:
        class UkfPredictorAdapter:
            """Adapter bridging processor to UKF predict interface."""
            def __init__(self, processor: Any) -> None:
                self.processor = processor

            def predict(self, unified_state: Any, time_delta: float = 1.0) -> Any:
                """Run UKF prediction step using real process model."""
                # Build current_state dict from unified_state for process model
                current_state: Dict[str, Any] = {}
                if unified_state is not None:
                    for attr in ("phi", "entropy", "valence", "arousal", "trust", "regulation"):
                        val = getattr(unified_state, attr, None)
                        if val is not None:
                            current_state[attr] = float(val)
                        elif isinstance(unified_state, dict):
                            v = unified_state.get(attr)
                            if v is not None:
                                current_state[attr] = float(v)

                if hasattr(self.processor, 'predict_ukf_state'):
                    return self.processor.predict_ukf_state(
                        time_delta=time_delta,
                        current_state=current_state,
                    )
                # Passthrough: return state unchanged when processor lacks UKF
                return unified_state

        blocks["ukf_predict"] = UkfPredictBlock(
            predictor=UkfPredictorAdapter(services.processor)
        )
    else:
        blocks["ukf_predict"] = UkfPredictBlock(predictor=None)

    # 10. cognitive_layer - Needs processor with process_cognitive_layer
    if services.processor and hasattr(services.processor, 'process_cognitive_layer'):
        class CognitiveLayerProcessorAdapter:
            def __init__(self, processor):
                self.processor = processor

            async def process_cognitive_layer(self, frame, user_input, card_type, card_result, scene_context, physics_params, **kwargs):
                return await self.processor.process_cognitive_layer(
                    frame=frame,
                    user_input=user_input,
                    card_type=card_type,
                    card_result=card_result,
                    scene_context=scene_context,
                    physics_params=physics_params,
                    **kwargs
                )

        blocks["cognitive_layer"] = CognitiveLayerBlock(
            processor=CognitiveLayerProcessorAdapter(services.processor)
        )
    else:
        # Fallback: block skips via should_skip() when processor=None
        blocks["cognitive_layer"] = CognitiveLayerBlock(processor=None)

    # 11. echo_ontology_transformation - Needs processor with transformation method
    if services.processor and hasattr(services.processor, 'process_echo_ontology_transformation'):
        class EchoOntologyTransformerAdapter:
            def __init__(self, processor):
                self.processor = processor

            def transform(self, frame, cognitive_state, trace_result):
                return self.processor.process_echo_ontology_transformation(
                    frame=frame,
                    cognitive_state=cognitive_state,
                    trace_result=trace_result
                )

        blocks["echo_ontology_transformation"] = EchoOntologyTransformationBlock(
            transformer=EchoOntologyTransformerAdapter(services.processor)
        )

    # 12. input_safety_gate - Combined: low_input_gate + safety_layer_pre_cep
    # Get safety processor adapter if available
    safety_processor = None
    if services.processor:
        class SafetyLayerProcessorAdapter:
            def __init__(self, processor):
                self.processor = processor

            async def process_safety(self, frame, user_input, narrative_response, cognitive_state, context_string, cep_flags=None, cep_config=None):
                return await self.processor.process_safety_layer(
                    frame=frame,
                    user_input=user_input,
                    narrative_response=narrative_response,
                    cognitive_state=cognitive_state,
                    context_string=context_string,
                    cep_flags=cep_flags,
                    cep_config=cep_config
                )

        safety_processor = SafetyLayerProcessorAdapter(services.processor)

    blocks["input_safety_gate"] = InputSafetyGateBlock(
        processor=safety_processor,
        min_input_length=3
    )

    # DEPRECATED: low_input_gate (kept for backward compatibility during migration)
    # This will be removed in v2.5.0 migration
    # blocks["low_input_gate"] = LowInputGateBlock()  # DEPRECATED

    # 13. intent_classification - NEW: Intent classification block
    # Get embedding cache if available (for fast path)
    embedding_cache = None
    if hasattr(services, 'embedding_cache'):
        embedding_cache = services.embedding_cache
    elif services.additional_services and 'embedding_cache' in services.additional_services:
        embedding_cache = services.additional_services.get('embedding_cache')

    # Get LLM provider if available (for fallback only)
    llm_provider = None
    if services.processor and hasattr(services.processor, 'llm_provider'):
        llm_provider = services.processor.llm_provider

    blocks["intent_classification"] = IntentClassificationBlock(
        intent_classifier=None,  # Will be created internally
        embedding_cache=embedding_cache,
        llm_provider=llm_provider
    )

    # 14. context_retrieval_rag - NEW: Context retrieval RAG block
    # Get vector store if available
    vector_store = None
    if hasattr(services, 'vector_store'):
        vector_store = services.vector_store
    elif services.additional_services and 'vector_store' in services.additional_services:
        vector_store = services.additional_services.get('vector_store')

    blocks["context_retrieval_rag"] = ContextRetrievalRagBlock(
        rag_service=None,  # Will be created internally
        vector_store=vector_store,
        max_context_tokens=2000,
        relevance_threshold=0.7
    )

    # 15. entropy_amplitude_pre_gate - Needs processor for entropy/amplitude gating
    if services.processor:
        class EntropyAmplitudePreGateAdapter:
            """Adapter bridging processor to entropy amplitude pre-gate interface."""
            def __init__(self, processor: Any) -> None:
                self.processor = processor

            def apply_gate(self, cognitive_state: Any, unified_state: Any, enhanced_context_string: str) -> tuple:
                """Apply entropy/amplitude gate before CEP evaluation."""
                if hasattr(self.processor, 'apply_entropy_amplitude_pre_gate'):
                    return self.processor.apply_entropy_amplitude_pre_gate(
                        cognitive_state=cognitive_state,
                        unified_state=unified_state,
                        enhanced_context_string=enhanced_context_string
                    )
                # Passthrough when processor lacks pre-gate method
                return enhanced_context_string, None

        blocks["entropy_amplitude_pre_gate"] = EntropyAmplitudePreGateBlock(
            gate=EntropyAmplitudePreGateAdapter(services.processor)
        )
    else:
        blocks["entropy_amplitude_pre_gate"] = EntropyAmplitudePreGateBlock(gate=None)

    # DEPRECATED: safety_layer_pre_cep (kept for backward compatibility during migration)
    # This will be removed in v2.5.0 migration
    # input_safety_gate now handles both input validation and safety check
    # 14. safety_layer_pre_cep - DEPRECATED (merged into input_safety_gate)
    # if services.processor:
    #     blocks["safety_layer_pre_cep"] = SafetyLayerPreCepBlock(
    #         processor=SafetyLayerProcessorAdapter(services.processor)
    #     )

    # 15. cep_evaluation - Needs processor with CEP evaluation method
    if services.processor and hasattr(services.processor, 'evaluate_cep_and_update_safety'):
        class CEPEvaluatorAdapter:
            def __init__(self, processor):
                self.processor = processor

            async def evaluate(self, frame, user_input, narrative_response, cognitive_state):
                # Note: processor.evaluate_cep_and_update_safety has different signature
                result = await self.processor.evaluate_cep_and_update_safety(
                    frame=frame,
                    user_input=user_input,
                    narrative_raw_text=narrative_response,
                    cognitive_state=cognitive_state,
                    physics_state={},  # Will be set from context
                    unified_state=None,  # Will be set from context
                    time_delta=1.0,  # Will be set from context
                    current_integrity=100.0,  # Will be set from context
                    character_archetype="shadow",  # Will be set from context
                    profile_name="edu"  # Will be set from context
                )
                # Extract cep_flags and cep_config from result
                frame, safe_text, cep_result, cep_metrics, cep_flags = result
                return cep_flags, cep_metrics  # Return as cep_config

        blocks["cep_evaluation"] = CepEvaluationBlock(
            evaluator=CEPEvaluatorAdapter(services.processor)
        )

    # 16. ethics_pre_response - Needs processor with ethics method
    if services.processor and hasattr(services.processor, 'assess_ethics_pre_response'):
        class EthicsProcessorAdapter:
            def __init__(self, processor):
                self.processor = processor

            def check_ethics_pre_response(self, frame, user_input, cognitive_state):
                """
                Check ethics pre response using processor's assess_ethics_pre_response.

                Returns dict with status, risk_level, harm_risk for test compatibility.
                """
                ethics_result = self.processor.assess_ethics_pre_response(
                    user_input=user_input,
                    unified_state=None,  # Will be set from context
                    current_entropy=0.5,  # Will be set from context
                    valence_from_emotion=0.0,  # Will be set from context
                    arousal_from_emotion=0.5  # Will be set from context
                )
                # Ensure harm_risk is included for test compatibility
                if isinstance(ethics_result, dict):
                    ethics_result["harm_risk"] = ethics_result.get("risk_level", 0.0)
                return ethics_result

        blocks["ethics_pre_response"] = EthicsPreResponseBlock(
            processor=EthicsProcessorAdapter(services.processor)
        )

    # 17. narrative_layer - Needs processor with process_narrative_layer
    if services.processor and hasattr(services.processor, 'process_narrative_layer'):
        class NarrativeLayerProcessorAdapter:
            def __init__(self, processor):
                self.processor = processor

            async def process_narrative_layer(self, frame, user_input, card_type, card_result, scene_context, enhanced_context_string, system_prompt=None, physics_state=None, selected_intent=None, **kwargs):
                return await self.processor.process_narrative_layer(
                    frame=frame,
                    user_input=user_input,
                    card_type=card_type,
                    card_result=card_result,
                    scene_context=scene_context,
                    enhanced_context_string=enhanced_context_string,
                    system_prompt=system_prompt,
                    physics_state=physics_state or {},
                    selected_intent=selected_intent,
                    **kwargs
                )

        blocks["narrative_layer"] = NarrativeLayerBlock(
            processor=NarrativeLayerProcessorAdapter(services.processor)
        )
    else:
        # Fallback: block skips via should_skip() when processor=None
        blocks["narrative_layer"] = NarrativeLayerBlock(processor=None)

    # 18. ethics_post_response - Needs processor (similar to pre_response)
    if services.processor:
        class EthicsPostProcessorAdapter:
            def __init__(self, processor: Any) -> None:
                """Initialize adapter with processor."""
                self.processor = processor

            def check_ethics_post_response(self, frame: Any, narrative_response: str, cognitive_state: Any) -> Any:
                """Check ethics post-response using processor's assess_ethics method."""
                # Use the same assess_ethics method for post-response checking
                # The processor can handle both pre and post response scenarios
                if hasattr(self.processor, 'assess_ethics_post_response'):
                    return self.processor.assess_ethics_post_response(
                        user_input="",  # Post-response doesn't need user input
                        narrative_response=narrative_response,
                        unified_state=None,  # Will be set from context if needed
                        cognitive_state=cognitive_state
                    )
                elif hasattr(self.processor, 'assess_ethics'):
                    # Fallback to general assess_ethics method
                    return self.processor.assess_ethics(
                        user_input="",
                        narrative_response=narrative_response,
                        unified_state=None,
                        cognitive_state=cognitive_state
                    )
                else:
                    # No ethics processor available
                    return None

        blocks["ethics_post_response"] = EthicsPostResponseBlock(
            processor=EthicsPostProcessorAdapter(services.processor)
        )

    # 18.5. behavioral_drift_detection - Silent Failure Firewall (NEW)
    # Optional: Only create if monitoring services are available
    try:
        from phionyx_core.monitoring import (
            BaselineStore,
            BehavioralDriftDetector,
            CircuitBreaker,
        )
        from phionyx_core.memory.vector_store import VectorStore  # noqa: F401

        # Get vector store if available
        vector_store = None
        if hasattr(services, 'vector_store'):
            vector_store = services.vector_store
        elif services.additional_services and 'vector_store' in services.additional_services:
            vector_store = services.additional_services.get('vector_store')

        # Create monitoring services
        baseline_store = BaselineStore()
        drift_detector = BehavioralDriftDetector(
            baseline_store=baseline_store,
            vector_store=vector_store,
            drift_threshold=0.3,
            semantic_threshold=0.7,
            physics_threshold=0.25,
            ethics_threshold=0.2
        )
        circuit_breaker = CircuitBreaker(
            drift_threshold=0.3,
            failure_threshold=3,
            recovery_timeout=300.0,
            half_open_test_limit=5
        )

        blocks["behavioral_drift_detection"] = BehavioralDriftDetectionBlock(
            drift_detector=drift_detector,
            circuit_breaker=circuit_breaker,
            enabled=True  # Can be disabled via config
        )
        logger.info("Behavioral drift detection block created (Silent Failure Firewall)")
    except ImportError as e:
        logger.warning(f"Behavioral drift detection not available: {e}")
        # Create disabled block as fallback
        blocks["behavioral_drift_detection"] = BehavioralDriftDetectionBlock(
            drift_detector=None,
            circuit_breaker=None,
            enabled=False
        )
    except Exception as e:
        logger.warning(f"Failed to create behavioral drift detection block: {e}")
        # Create disabled block as fallback
        blocks["behavioral_drift_detection"] = BehavioralDriftDetectionBlock(
            drift_detector=None,
            circuit_breaker=None,
            enabled=False
        )

    # 19. unified_state_update_esc - Needs processor for unified state update
    if services.processor:
        class UnifiedStateUpdateEscAdapter:
            """Adapter bridging processor to unified state update interface."""
            def __init__(self, processor: Any) -> None:
                self.processor = processor

            def update_state(self, unified_state: Any, physics_state: Any, **kwargs) -> Any:
                """Update unified state from ESC computation."""
                if hasattr(self.processor, 'update_unified_state_esc'):
                    return self.processor.update_unified_state_esc(
                        unified_state=unified_state,
                        physics_state=physics_state,
                        **kwargs
                    )
                # Passthrough when processor lacks ESC update method
                return unified_state

            # Alias for block protocol compatibility
            def update_from_physics_state(self, unified_state: Any, physics_state: Any, **kwargs) -> Any:
                return self.update_state(unified_state, physics_state, **kwargs)

        blocks["unified_state_update_esc"] = UnifiedStateUpdateEscBlock(
            updater=UnifiedStateUpdateEscAdapter(services.processor)
        )
    else:
        blocks["unified_state_update_esc"] = UnifiedStateUpdateEscBlock(updater=None)

    # 20. phi_publish - Note: phi is a computed property, cannot be set directly
    class PhiPublisherAdapter:
        def publish_phi(
            self,
            unified_state: Any,
            phi_value: float,
            phi_components: Optional[Any] = None
        ) -> Any:
            """
            Publish phi value to unified state.

            Note: phi is a computed property (derived from A, V, H), cannot be set directly.
            Instead, we update the underlying state values (A, V, H) to achieve desired phi.

            For now, we simply log the phi value and return the state unchanged.
            In real implementation, we could update A/V/H to approximate the desired phi.
            """
            # phi is computed from A, V, H - cannot set directly
            # Log phi value for tracking
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Phi computed (read-only): {unified_state.phi:.3f} (requested: {phi_value:.3f})")
            # Return state unchanged (phi is computed automatically)
            return unified_state

    blocks["phi_publish"] = PhiPublishBlock(
        publisher=PhiPublisherAdapter()
    )

    # 21. esc_state_helper_update - Needs processor with ESC helper method
    if services.processor and hasattr(services.processor, 'update_unified_state_from_esc_helpers'):
        class ESCStateHelperAdapter:
            def __init__(self, processor):
                self.processor = processor

            def update_helper_state(self, unified_state, physics_state):
                return self.processor.update_unified_state_from_esc_helpers(
                    unified_state=unified_state,
                    frame=None,  # Will be set from context
                    trust_metrics=None,  # Will be set from context
                    turn_count=0  # Will be set from context
                )

        blocks["esc_state_helper_update"] = EscStateHelperUpdateBlock(
            helper=ESCStateHelperAdapter(services.processor)
        )

    # 22. drive_coherence_update - Needs processor with drive coherence method
    if services.processor and hasattr(services.processor, 'update_drive_coherence'):
        class DriveCoherenceUpdaterAdapter:
            def __init__(self, processor):
                self.processor = processor

            def update_drive_coherence(self, unified_state, narrative_response, physics_state):
                return self.processor.update_drive_coherence(
                    unified_state=unified_state,
                    narrative_response=narrative_response,
                    physics_state=physics_state
                )

        blocks["drive_coherence_update"] = DriveCoherenceUpdateBlock(
            updater=DriveCoherenceUpdaterAdapter(services.processor)
        )

    # 23. coherence_qa - Needs processor with compute_coherence method
    if services.processor and hasattr(services.processor, 'compute_coherence'):
        class CoherenceQAAdapter:
            def __init__(self, processor):
                self.processor = processor

            def check_coherence(self, unified_state, narrative_response):
                return self.processor.compute_coherence(
                    unified_state=unified_state,
                    narrative_response=narrative_response,
                    user_input=""  # Will be set from context
                )

        blocks["coherence_qa"] = CoherenceQaBlock(
            qa_checker=CoherenceQAAdapter(services.processor)
        )
    elif services.processor:
        # Inline fallback: 17 regex pattern leak detection + auto-redaction
        blocks["coherence_qa"] = CoherenceQaBlock(qa_checker=None)

    # 24. entropy_amplitude_post_gate - Needs processor for post-narrative entropy gating
    if services.processor:
        class EntropyAmplitudePostGateAdapter:
            """Adapter bridging processor to entropy amplitude post-gate interface."""
            def __init__(self, processor: Any) -> None:
                self.processor = processor

            def apply_gate(self, physics_state: Dict) -> Dict:
                """Apply entropy/amplitude gate after narrative generation."""
                if hasattr(self.processor, 'apply_entropy_amplitude_post_gate'):
                    return self.processor.apply_entropy_amplitude_post_gate(
                        physics_state=physics_state
                    )
                # Passthrough when processor lacks post-gate method
                return physics_state

        blocks["entropy_amplitude_post_gate"] = EntropyAmplitudePostGateBlock(
            gate=EntropyAmplitudePostGateAdapter(services.processor)
        )
    else:
        blocks["entropy_amplitude_post_gate"] = EntropyAmplitudePostGateBlock(gate=None)

    # 25. neurotransmitter_memory_growth - Needs neurotransmitter
    if services.neurotransmitter:
        class NeurotransmitterMemoryGrowthAdapter:
            def __init__(self, neurotransmitter, growth_tracker=None):
                self.neurotransmitter = neurotransmitter
                self.growth_tracker = growth_tracker

            def update_growth(self, user_input, narrative_response, physics_state):
                # Update neurotransmitter and growth tracker
                # This is a simplified adapter - actual implementation may differ
                return {
                    "neurotransmitter_updated": True,
                    "growth_metrics": {}
                }

        blocks["neurotransmitter_memory_growth"] = NeurotransmitterMemoryGrowthBlock(
            growth_updater=NeurotransmitterMemoryGrowthAdapter(
                services.neurotransmitter,
                services.additional_services.get("growth_tracker")
            )
        )

    # 26. audit_layer - Needs processor
    if services.processor:
        class AuditLayerProcessorAdapter:
            def __init__(self, processor):
                self.processor = processor

            async def process_audit(self, frame, unified_state, narrative_response, physics_state):
                return await self.processor.process_audit_layer(
                    frame=frame,
                    user_input="",  # Will be set from context
                    narrative_response=narrative_response,
                    physics_state=physics_state,
                    emotional_state=None,  # Will be set from context
                    memory_result=None,  # Will be set from context
                    growth_metrics=None,  # Will be set from context
                    character_id="",  # Will be set from context
                    actor_ref=None,  # Will be set from context
                    trust_metrics=None,  # Will be set from context
                    scenario_id=None,  # Will be set from context
                    scenario_step_id=None  # Will be set from context
                )

        blocks["audit_layer"] = AuditLayerBlock(
            processor=AuditLayerProcessorAdapter(services.processor)
        )

    # 27. phi_finalize - Needs processor
    if services.processor:
        class PhiFinalizerAdapter:
            def __init__(self, processor):
                self.processor = processor

            def finalize_phi(self, unified_state, phi_value, phi_components=None):
                self.processor.finalize_phi_for_response(
                    frame=None,  # Will be set from context
                    physics_state={},  # Will be set from context
                    unified_state=unified_state,
                    current_unified_state=unified_state,
                    esc_available=True
                )
                return unified_state

        blocks["phi_finalize"] = PhiFinalizeBlock(
            finalizer=PhiFinalizerAdapter(services.processor)
        )

    # 28. state_update_physics - Needs processor for physics state copy
    if services.processor:
        class StateUpdatePhysicsAdapter:
            """Adapter bridging processor to physics state update interface."""
            def __init__(self, processor: Any) -> None:
                self.processor = processor

            def update_physics(self, unified_state: Any, physics_state: Any) -> Any:
                """Copy physics state from unified state."""
                if hasattr(self.processor, 'update_physics_from_state'):
                    return self.processor.update_physics_from_state(
                        unified_state=unified_state,
                        physics_state=physics_state
                    )
                # Passthrough when processor lacks physics update method
                return physics_state

            # Alias for block protocol compatibility
            def update_physics_state(self, physics_state: Any, unified_state: Any) -> Any:
                return self.update_physics(unified_state, physics_state)

        blocks["state_update_physics"] = StateUpdatePhysicsBlock(
            updater=StateUpdatePhysicsAdapter(services.processor)
        )
    else:
        blocks["state_update_physics"] = StateUpdatePhysicsBlock(updater=None)

    # 29. response_build - Needs response_generator
    # CRITICAL: response_build is always-on block, must always be created
    logger.debug(f"[BLOCK_FACTORY] response_generator check: {services.response_generator is not None}, type: {type(services.response_generator)}")

    if services.response_generator:
        logger.debug("[BLOCK_FACTORY] Creating response_build block with ResponseGenerator")
        class ResponseBuilderAdapter:
            def __init__(self, response_generator):
                self.response_generator = response_generator

            def build_response(self, frame, narrative_response, physics_state, **kwargs):
                return self.response_generator.build_response(
                    frame=frame,
                    narrative_response=narrative_response,
                    physics_state=physics_state,
                    **kwargs
                )

        blocks["response_build"] = ResponseBuildBlock(
            builder=ResponseBuilderAdapter(services.response_generator)
        )
        logger.debug("[BLOCK_FACTORY] response_build block created with ResponseGenerator")
    else:
        # CRITICAL: response_build is always-on, must have fallback to prevent pipeline failure
        logger.warning("ResponseGenerator not available for response_build block - using fallback")

        class FallbackResponseBuilder:
            """Fallback response builder when ResponseGenerator is not available."""
            def build_response(
                self,
                frame,
                narrative_response,
                physics_state,
                emotional_state=None,
                memory_result=None,
                growth_metrics=None,
                confidence_result=None,
                cep_metrics=None,
                cep_flags=None,
                entropy_modulated_amplitude=None,
                behavior_modulation=None,
                current_unified_state=None,
                esc_available=False,
                mode=None,
                strategy=None,
                prompt_context=None
            ):
                """Build minimal response payload."""
                return {
                    "narrative_response": narrative_response or "I'm processing your request. Please wait a moment.",
                    "physics": physics_state or {"phi": 0.5, "entropy": 0.5},
                    "emotional_state": emotional_state,
                    "error": "ResponseGenerator not available - using fallback",
                    "mode": mode,
                    "strategy": strategy
                }

        blocks["response_build"] = ResponseBuildBlock(
            builder=FallbackResponseBuilder()
        )
        logger.debug("[BLOCK_FACTORY] response_build block created with fallback")

    # v3.8.0: response_revision_gate — state-driven response revision
    from phionyx_core.pipeline.blocks.response_revision_gate import ResponseRevisionGateBlock
    blocks["response_revision_gate"] = ResponseRevisionGateBlock()
    logger.debug("[BLOCK_FACTORY] response_revision_gate block created")

    # 30. phi_computation - Needs phi_engine; fallback uses real physics formula
    # CRITICAL: replace entropy*0.8 heuristic with calculate_phi_cognitive
    if services.phi_engine:
        class PhiComputationAdapter:
            def __init__(self, phi_engine):
                self.phi_engine = phi_engine

            def compute_phi(self, physics_state=None, previous_phi=None, **kwargs):
                """
                Compute phi from physics state.

                Supports both keyword arguments (from blocks) and positional arguments (from legacy code).
                """
                # Normalize input: handle both keyword and positional arguments
                if physics_state is None:
                    physics_state = kwargs.get("physics_state", {})
                if previous_phi is None:
                    previous_phi = kwargs.get("previous_phi")

                # Ensure physics_state is a dict
                if not isinstance(physics_state, dict):
                    physics_state = {}

                # Try compute_phi method first (if engine supports it)
                if hasattr(self.phi_engine, 'compute_phi'):
                    try:
                        # Try with keyword arguments first (modern interface)
                        result = self.phi_engine.compute_phi(
                            physics_state=physics_state,
                            previous_phi=previous_phi
                        )
                    except TypeError:
                        # Fallback: try with positional arguments (legacy interface)
                        result = self.phi_engine.compute_phi(physics_state, previous_phi)

                    # Handle both dict and scalar returns
                    if isinstance(result, dict):
                        return result
                    return {"phi": result, "components": {}}

                # Fallback: use compute method (legacy interface)
                if hasattr(self.phi_engine, 'compute'):
                    phi_value = self.phi_engine.compute(
                        user_message="",
                        assistant_response="",
                        state={
                            "phi": previous_phi or 0.5,
                            "valence": physics_state.get("valence", 0.0),
                            "arousal": physics_state.get("arousal", 0.5),
                            "previous_responses": []
                        },
                        telemetry_summaries={}
                    )
                    return {"phi": phi_value if isinstance(phi_value, (int, float)) else 0.5, "components": {}}

                # Final fallback
                return {"phi": previous_phi or 0.5, "components": {}}

        blocks["phi_computation"] = PhiComputationBlock(
            phi_computer=PhiComputationAdapter(services.phi_engine)
        )
    else:
        # Fallback: use real physics formula instead of heuristic entropy*0.8
        class PhiComputerFallbackAdapter:
            """Compute phi using real calculate_phi_cognitive formula."""
            def compute_phi(self, physics_state=None, previous_phi=None, **kwargs):
                if physics_state is None:
                    physics_state = {}
                if not isinstance(physics_state, dict):
                    physics_state = {}
                try:
                    from phionyx_core.physics.formulas import calculate_phi_cognitive
                    entropy = float(physics_state.get("entropy", 0.5))
                    stability = float(physics_state.get("stability", 0.8))
                    valence = float(physics_state.get("valence", 0.0))
                    phi = calculate_phi_cognitive(
                        entropy=entropy,
                        stability=stability,
                        valence=valence,
                    )
                    return {
                        "phi": phi,
                        "components": {
                            "entropy": entropy,
                            "stability": stability,
                            "valence": valence,
                            "source": "calculate_phi_cognitive",
                        }
                    }
                except Exception as e:
                    logger.warning(f"calculate_phi_cognitive failed, using entropy*0.8: {e}")
                    entropy = float(physics_state.get("entropy", 0.5))
                    return {"phi": entropy * 0.8, "components": {"entropy": entropy, "source": "heuristic_fallback"}}

        blocks["phi_computation"] = PhiComputationBlock(
            phi_computer=PhiComputerFallbackAdapter()
        )

    # 31. entropy_computation - Needs entropy_engine
    if services.entropy_engine:
        class EntropyComputationAdapter:
            def __init__(self, entropy_engine):
                self.entropy_engine = entropy_engine

            def compute_entropy(self, user_input=None, response_text=None, previous_entropy=None, **kwargs):
                """
                Compute entropy from user input and response.

                Supports both keyword arguments (from blocks) and positional arguments (from legacy code).
                """
                # Normalize input: handle both keyword and positional arguments
                if user_input is None:
                    user_input = kwargs.get("user_input", "")
                if response_text is None:
                    response_text = kwargs.get("response_text")
                if previous_entropy is None:
                    previous_entropy = kwargs.get("previous_entropy")

                # Try compute_entropy method first (if engine supports it)
                if hasattr(self.entropy_engine, 'compute_entropy'):
                    try:
                        # Try with keyword arguments first (modern interface)
                        result = self.entropy_engine.compute_entropy(
                            user_input=user_input,
                            response_text=response_text,
                            previous_entropy=previous_entropy
                        )
                    except TypeError:
                        # Fallback: try with positional arguments (legacy interface)
                        result = self.entropy_engine.compute_entropy(user_input, response_text, previous_entropy)

                    # Handle both dict and scalar returns
                    if isinstance(result, dict):
                        return result
                    return {"entropy": result, "components": {}}

                # Fallback: use compute method (legacy interface)
                if hasattr(self.entropy_engine, 'compute'):
                    entropy_value = self.entropy_engine.compute(
                        user_message=user_input,
                        assistant_response=response_text or "",
                        previous_entropy=previous_entropy or 0.5,
                        echo_types=[]
                    )
                    return {"entropy": entropy_value if isinstance(entropy_value, (int, float)) else 0.5, "components": {}}

                # Final fallback
                return {"entropy": previous_entropy or 0.5, "components": {}}

        blocks["entropy_computation"] = EntropyComputationBlock(
            entropy_computer=EntropyComputationAdapter(services.entropy_engine)
        )

    # ── v3.0.0 AGI World Model Blocks (8) ──────────────────────────────
    # These blocks have no-arg constructors or optional DI; skip gracefully.

    # Kill Switch Gate (S1 Safety)
    try:
        from phionyx_core.governance.kill_switch import KillSwitch
        kill_switch = KillSwitch()
        blocks["kill_switch_gate"] = KillSwitchGateBlock(kill_switch=kill_switch)
    except ImportError:
        blocks["kill_switch_gate"] = KillSwitchGateBlock(kill_switch=None)

    # Perceptual Frame Emit (no DI needed)
    blocks["perceptual_frame_emit"] = PerceptualFrameEmitBlock()

    # Goal Evaluation (no DI needed — uses internal goal registry protocol)
    blocks["goal_evaluation"] = GoalEvaluationBlock()

    # World State Snapshot (no DI needed)
    blocks["world_state_snapshot"] = WorldStateSnapshotBlock()

    # Confidence Fusion (no DI needed)
    blocks["confidence_fusion"] = ConfidenceFusionBlock()

    # Arbitration Resolve (no DI needed)
    blocks["arbitration_resolve"] = ArbitrationResolveBlock()

    # Action Intent Gate (no DI needed)
    blocks["action_intent_gate"] = ActionIntentGateBlock()

    # Learning Gate (no DI needed — uses internal service protocol)
    blocks["learning_gate"] = LearningGateBlock()

    # Workspace Broadcast (no DI needed)
    blocks["workspace_broadcast"] = WorkspaceBroadcastBlock()

    # ── AGI Sprint Pipeline Binding Blocks S2-S5 (11) ───────────────────
    # Each block takes optional DI; None → block skips gracefully.

    # S2: Self-Awareness
    try:
        from phionyx_core.meta.self_model import SelfModel
        self_model = SelfModel()
    except ImportError:
        self_model = None

    # Register known capabilities so can_i_do() returns meaningful assessments
    if self_model is not None:
        self_model.register_capability("respond", available=True, reason="43-blok pipeline ile metin yanit uretimi")
        self_model.register_capability("causal_reasoning", available=True, reason="CausalGraph + Intervention + RCA")
        self_model.register_capability("ethical_deliberation", available=True, reason="4-cerceve musterek etik")
        self_model.register_capability("knowledge_boundary_detection", available=True, reason="OOD + ilgililik + yenilik")
        self_model.register_capability("trust_evaluation", available=True, reason="Gecisken guven yayilimi")
        self_model.register_capability("goal_decomposition", available=True, reason="Alt-hedef DAG, topolojik siralama")
        self_model.register_capability("counterfactual_analysis", available=True, reason="Karsi-olgusal what-if motoru")
        self_model.register_capability("memory_consolidation", available=True, reason="Epizodik-semantik pekistirme")
        self_model.register_capability("self_assessment", available=True, reason="Oz-model ve sapma izleme")
        self_model.register_capability("image_generation", available=False, reason="Gorsel uretim desteklenmiyor")
        self_model.register_capability("realtime_data", available=False, reason="Gercek zamanli veri erisimi yok")
        self_model.register_capability("code_execution", available=False, reason="Sandbox kodu calistirma yok")

    blocks["self_model_assessment"] = SelfModelAssessmentBlock(self_model=self_model)

    try:
        from phionyx_core.meta.knowledge_boundary import KnowledgeBoundaryDetector
        knowledge_boundary = KnowledgeBoundaryDetector()
    except ImportError:
        knowledge_boundary = None
    blocks["knowledge_boundary_check"] = KnowledgeBoundaryCheckBlock(
        knowledge_boundary=knowledge_boundary
    )

    try:
        from phionyx_core.memory.consolidation import MemoryConsolidator
        memory_consolidator = MemoryConsolidator()
    except ImportError:
        memory_consolidator = None
    blocks["memory_consolidation"] = MemoryConsolidationBlock(
        memory_consolidator=memory_consolidator
    )

    # S3: Causality Foundations
    try:
        from phionyx_core.causality.causal_graph import CausalGraphBuilder
        causal_graph_builder = CausalGraphBuilder()
    except ImportError:
        causal_graph_builder = None
    blocks["causal_graph_update"] = CausalGraphUpdateBlock(
        causal_graph_builder=causal_graph_builder
    )

    # Build a CausalGraph from the builder for downstream modules
    _causal_graph = causal_graph_builder.build() if causal_graph_builder else None

    try:
        from phionyx_core.causality.intervention import InterventionModel
        intervention_model = InterventionModel(
            graph=_causal_graph
        ) if _causal_graph else None
    except ImportError:
        intervention_model = None
    blocks["causal_intervention"] = CausalInterventionBlock(
        intervention_model=intervention_model
    )

    # S4: Causality Advanced
    try:
        from phionyx_core.causality.counterfactual import CounterfactualEngine
        counterfactual_engine = CounterfactualEngine(
            graph=_causal_graph
        ) if _causal_graph else None
    except ImportError:
        counterfactual_engine = None
    blocks["counterfactual_analysis"] = CounterfactualAnalysisBlock(
        counterfactual_engine=counterfactual_engine
    )

    try:
        from phionyx_core.causality.root_cause import RootCauseAnalyzer
        root_cause_analyzer = RootCauseAnalyzer(
            graph=_causal_graph
        ) if _causal_graph else None
    except ImportError:
        root_cause_analyzer = None
    blocks["root_cause_analysis"] = RootCauseAnalysisBlock(
        root_cause_analyzer=root_cause_analyzer
    )

    try:
        from phionyx_core.causality.simulator import CausalSimulator
        causal_simulator = CausalSimulator(
            graph=_causal_graph
        ) if _causal_graph else None
    except ImportError:
        causal_simulator = None
    blocks["causal_simulation"] = CausalSimulationBlock(
        causal_simulator=causal_simulator
    )

    # S5: Social & Polish
    try:
        from phionyx_core.social.trust_propagation import TrustNetwork
        trust_network = TrustNetwork()
    except ImportError:
        trust_network = None
    blocks["trust_evaluation"] = TrustEvaluationBlock(trust_network=trust_network)

    try:
        from phionyx_core.planning.goal_decomposer import GoalDecomposer
        goal_decomposer = GoalDecomposer()
    except ImportError:
        goal_decomposer = None
    blocks["goal_decomposition"] = GoalDecompositionBlock(
        goal_decomposer=goal_decomposer
    )

    try:
        from phionyx_core.governance.deliberative_ethics import DeliberativeEthics
        deliberative_ethics = DeliberativeEthics()
    except ImportError:
        deliberative_ethics = None
    blocks["deliberative_ethics_gate"] = DeliberativeEthicsGateBlock(
        deliberative_ethics=deliberative_ethics
    )

    # ── Feedback Loop Block (v3.6.0) ─────────────────────────────────
    # Outcome feedback: bridges turn outcomes to self-model + goal revision
    # DI: self_model (already instantiated above), goal_persistence (new)
    try:
        from phionyx_core.planning.goal_persistence import GoalPersistence
        goal_persistence = GoalPersistence()
    except ImportError:
        goal_persistence = None

    blocks["outcome_feedback"] = OutcomeFeedbackBlock(
        self_model=self_model,
        goal_persistence=goal_persistence,
    )

    logger.info(f"Created {len(blocks)} pipeline blocks (target: 44)")
    logger.debug(f"[BLOCK_FACTORY] response_build in blocks: {'response_build' in blocks}")
    return blocks

