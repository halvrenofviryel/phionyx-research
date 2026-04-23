"""
Pipeline Blocks
===============

46 canonical pipeline blocks for the Phionyx pipeline (contract v3.8.0).

Pre-v3.8.0 blocks live under ``phionyx_core.pipeline.blocks.archive`` and are
re-exported from here only for ``block_factory`` backward-compat wiring (v2.4.0
loader). New code must target v3.8.0 canonical blocks only.
"""

from .base_block import BaseBlock

# v2.4.0 legacy blocks (archived — imported here only for block_factory wiring)
from .archive.api_process_decision import ApiProcessDecisionBlock
from .archive.engine_ensure_initialized import EngineEnsureInitializedBlock
from .archive.echo_ontology_event_trace import EchoOntologyEventTraceBlock
from .archive.emotion_from_neurotransmitter import EmotionFromNeurotransmitterBlock
from .archive.echo_ontology_transformation import EchoOntologyTransformationBlock
from .archive.low_input_gate import LowInputGateBlock  # DEPRECATED: Use InputSafetyGateBlock
from .archive.safety_layer_pre_cep import SafetyLayerPreCepBlock  # DEPRECATED
from .archive.esc_state_helper_update import EscStateHelperUpdateBlock
from .archive.drive_coherence_update import DriveCoherenceUpdateBlock
from .archive.coherence_qa import CoherenceQaBlock
from .archive.phi_finalize import PhiFinalizeBlock

# v3.8.0 canonical blocks
from .time_update_sot import TimeUpdateSotBlock
from .emotion_estimation import EmotionEstimationBlock
from .create_scenario_frame import CreateScenarioFrameBlock
from .initialize_unified_state import InitializeUnifiedStateBlock
from .ukf_predict import UkfPredictBlock
from .cognitive_layer import CognitiveLayerBlock
from .input_safety_gate import InputSafetyGateBlock  # Combined: low_input_gate + safety_layer_pre_cep
from .intent_classification import IntentClassificationBlock
from .context_retrieval_rag import ContextRetrievalRagBlock
from .entropy_amplitude_pre_gate import EntropyAmplitudePreGateBlock
from .cep_evaluation import CepEvaluationBlock
from .ethics_pre_response import EthicsPreResponseBlock
from .narrative_layer import NarrativeLayerBlock
from .ethics_post_response import EthicsPostResponseBlock
from .unified_state_update_esc import UnifiedStateUpdateEscBlock
from .phi_publish import PhiPublishBlock
from .entropy_amplitude_post_gate import EntropyAmplitudePostGateBlock
from .neurotransmitter_memory_growth import NeurotransmitterMemoryGrowthBlock
from .audit_layer import AuditLayerBlock
from .state_update_physics import StateUpdatePhysicsBlock
from .response_build import ResponseBuildBlock
from .phi_computation import PhiComputationBlock
from .entropy_computation import EntropyComputationBlock
from .behavioral_drift_detection import BehavioralDriftDetectionBlock

# v3.8.0 State-Driven Response Revision
from .response_revision_gate import ResponseRevisionGateBlock

# v4 AGI World Model Blocks
from .kill_switch_gate import KillSwitchGateBlock
from .perceptual_frame_emit import PerceptualFrameEmitBlock
from .goal_evaluation import GoalEvaluationBlock
from .world_state_snapshot import WorldStateSnapshotBlock
from .confidence_fusion import ConfidenceFusionBlock
from .arbitration_resolve import ArbitrationResolveBlock
from .action_intent_gate import ActionIntentGateBlock
from .learning_gate import LearningGateBlock
from .workspace_broadcast import WorkspaceBroadcastBlock

# AGI Sprint Pipeline Binding Blocks (S2-S5)
from .self_model_assessment import SelfModelAssessmentBlock
from .knowledge_boundary_check import KnowledgeBoundaryCheckBlock
from .memory_consolidation_block import MemoryConsolidationBlock
from .causal_graph_update import CausalGraphUpdateBlock
from .causal_intervention_block import CausalInterventionBlock
from .counterfactual_analysis import CounterfactualAnalysisBlock
from .root_cause_analysis import RootCauseAnalysisBlock
from .causal_simulation import CausalSimulationBlock
from .trust_evaluation import TrustEvaluationBlock
from .goal_decomposition import GoalDecompositionBlock
from .deliberative_ethics_gate import DeliberativeEthicsGateBlock

# Feedback Loop Block (v3.6.0)
from .outcome_feedback import OutcomeFeedbackBlock

__all__ = [
    'BaseBlock',
    'ApiProcessDecisionBlock',
    'EngineEnsureInitializedBlock',
    'TimeUpdateSotBlock',
    'EchoOntologyEventTraceBlock',
    'EmotionFromNeurotransmitterBlock',
    'EmotionEstimationBlock',
    'CreateScenarioFrameBlock',
    'InitializeUnifiedStateBlock',
    'UkfPredictBlock',
    'CognitiveLayerBlock',
    'EchoOntologyTransformationBlock',
    'LowInputGateBlock',  # DEPRECATED
    'InputSafetyGateBlock',  # Combined: low_input_gate + safety_layer_pre_cep
    'IntentClassificationBlock',  # NEW: Intent classification
    'ContextRetrievalRagBlock',  # NEW: Context retrieval RAG
    'EntropyAmplitudePreGateBlock',
    'SafetyLayerPreCepBlock',  # DEPRECATED
    'CepEvaluationBlock',
    'EthicsPreResponseBlock',
    'NarrativeLayerBlock',
    'EthicsPostResponseBlock',
    'UnifiedStateUpdateEscBlock',
    'PhiPublishBlock',
    'EscStateHelperUpdateBlock',
    'DriveCoherenceUpdateBlock',
    'CoherenceQaBlock',
    'EntropyAmplitudePostGateBlock',
    'NeurotransmitterMemoryGrowthBlock',
    'AuditLayerBlock',
    'PhiFinalizeBlock',
    'StateUpdatePhysicsBlock',
    'ResponseBuildBlock',
    'PhiComputationBlock',
    'EntropyComputationBlock',
    'BehavioralDriftDetectionBlock',  # NEW: Silent Failure Firewall
    'ResponseRevisionGateBlock',  # v3.8.0: State-driven response revision
    # v4 AGI World Model Blocks
    'KillSwitchGateBlock',
    'PerceptualFrameEmitBlock',
    'GoalEvaluationBlock',
    'WorldStateSnapshotBlock',
    'ConfidenceFusionBlock',
    'ArbitrationResolveBlock',
    'ActionIntentGateBlock',
    'LearningGateBlock',
    'WorkspaceBroadcastBlock',
    # AGI Sprint Pipeline Binding Blocks (S2-S5)
    'SelfModelAssessmentBlock',
    'KnowledgeBoundaryCheckBlock',
    'MemoryConsolidationBlock',
    'CausalGraphUpdateBlock',
    'CausalInterventionBlock',
    'CounterfactualAnalysisBlock',
    'RootCauseAnalysisBlock',
    'CausalSimulationBlock',
    'TrustEvaluationBlock',
    'GoalDecompositionBlock',
    'DeliberativeEthicsGateBlock',
    # Feedback Loop Block (v3.6.0)
    'OutcomeFeedbackBlock',
]
