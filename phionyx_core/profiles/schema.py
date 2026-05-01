"""
Profile Schema - Pydantic Models for Configuration
===================================================

Defines the nested structure for high-level personas and low-level technical parameters.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BaseMode(str, Enum):
    """Base context mode for physics calculations."""
    SCHOOL = "SCHOOL"
    GAME = "GAME"
    THERAPY = "THERAPY"
    NPC_ENGINE = "NPC_ENGINE"
    DEFAULT = "DEFAULT"


class PIIMode(str, Enum):
    """PII scrubbing mode."""
    NONE = "NONE"  # No scrubbing
    PARTIAL = "PARTIAL"  # Basic patterns (email, phone)
    FULL = "FULL"  # All PII patterns + custom rules


class AuditLevel(str, Enum):
    """Audit logging level."""
    MINIMAL = "MINIMAL"  # Only critical events
    STANDARD = "STANDARD"  # All events
    VERBOSE = "VERBOSE"  # All events + debug info


class LLMTierStrategy(str, Enum):
    """LLM tier selection strategy."""
    COST_OPTIMIZED = "COST_OPTIMIZED"  # Prefer cheaper models
    QUALITY_OPTIMIZED = "QUALITY_OPTIMIZED"  # Prefer best models
    BALANCED = "BALANCED"  # Balance cost and quality
    ADAPTIVE = "ADAPTIVE"  # Switch based on complexity


# ============================================================================
# Configuration Models
# ============================================================================


class PhysicsConfig(BaseModel):
    """
    Physics module configuration.

    High-level knobs that map to low-level physics parameters.
    """
    reactivity: float = Field(0.5, ge=0.0, le=1.0, description="Response speed (0=slow, 1=fast)")
    resilience: float = Field(0.5, ge=0.0, le=1.0, description="Stability (0=fragile, 1=robust)")
    safety_bias: float = Field(0.5, ge=0.0, le=1.0, description="Safety strictness (0=permissive, 1=strict)")
    base_mode: BaseMode = Field(BaseMode.DEFAULT, description="Base context mode")
    # Physics v2.1 Parameters (Circumplex Model) - optional for backward compatibility
    valence: float | None = Field(None, ge=-1.0, le=1.0, description="Emotional valence from Circumplex (-1 to +1)")
    arousal: float | None = Field(None, ge=0.0, le=1.0, description="Arousal from Circumplex (0 to 1)")
    amplitude: float | None = Field(None, ge=0.0, le=10.0, description="Emotional intensity slider (0-10)")
    entropy: float | None = Field(None, ge=0.0, le=1.0, description="Chaos level (0-1)")
    stability: float | None = Field(None, ge=0.0, le=1.0, description="Internal resilience (0-1)")
    gamma: float | None = Field(None, ge=0.0, le=1.0, description="Decay rate (0-1)")
    w_c: float | None = Field(None, ge=0.0, le=1.0, description="Cognitive weight (0-1)")
    w_p: float | None = Field(None, ge=0.0, le=1.0, description="Physical weight (0-1)")
    entropy_penalty_k: float | None = Field(1.0, ge=0.0, le=2.0, description="Entropy penalty coefficient (0-2, default 1.0)")

    @field_validator('reactivity', 'resilience', 'safety_bias')
    @classmethod
    def validate_range(cls, v: float) -> float:
        """Ensure values are in [0, 1] range."""
        return max(0.0, min(1.0, v))


class PedagogyConfig(BaseModel):
    """
    Pedagogy module configuration.

    Educational intervention parameters.
    """
    vygotsky_level: float = Field(0.5, ge=0.0, le=1.0, description="Zone of Proximal Development level")
    scaffolding_aggressiveness: float = Field(0.5, ge=0.0, le=1.0, description="How much to help (0=minimal, 1=aggressive)")
    intervention_threshold: float = Field(0.3, ge=0.0, le=1.0, description="When to intervene (0=never, 1=always)")

    @field_validator('vygotsky_level', 'scaffolding_aggressiveness', 'intervention_threshold')
    @classmethod
    def validate_range(cls, v: float) -> float:
        """Ensure values are in [0, 1] range."""
        return max(0.0, min(1.0, v))


class GovernanceConfig(BaseModel):
    """
    Governance module configuration.

    Security, privacy, and compliance parameters.
    """
    policy_id: str = Field("default", description="Policy identifier")
    pii_mode: PIIMode = Field(PIIMode.PARTIAL, description="PII scrubbing mode")
    audit_level: AuditLevel = Field(AuditLevel.STANDARD, description="Audit logging level")
    custom_regex_patterns: list[str] | None = Field(None, description="Custom PII regex patterns")

    model_config = ConfigDict(use_enum_values=True)
class RoutingConfig(BaseModel):
    """
    LLM routing configuration.

    Determines which LLM tier to use for different scenarios.
    """
    llm_tier_strategy: LLMTierStrategy = Field(LLMTierStrategy.BALANCED, description="LLM selection strategy")
    fallback_model: str | None = Field(None, description="Fallback model if primary fails")
    max_tokens_per_tier: dict[str, int] | None = Field(None, description="Max tokens per tier")
    enable_graph_rag: bool = Field(False, description="Enable GraphRAG for hidden context discovery (default: OFF, only for Academic/Enterprise/Deep-analysis modes)")

    model_config = ConfigDict(use_enum_values=True)
class ExecutionGuardConfig(BaseModel):
    """
    Per-profile ExecutionGuard limits.

    Makes the hard-coded constants in `ExecutionGuard.__init__` tunable by
    profile (SCHOOL, GAME, THERAPY, DEFAULT). A ``None`` instance means
    "use ExecutionGuard's built-in defaults", preserving backwards
    compatibility for callers that never set it.
    """
    max_iterations_multiplier: int = Field(
        3,
        ge=1,
        le=10,
        description="Iteration limit = block_order_length * this. Guard default: 3.",
    )
    max_block_executions: int = Field(
        2,
        ge=1,
        le=10,
        description="Max executions per block before abort. Guard default: 2.",
    )
    max_execution_time_sec: float = Field(
        300.0,
        gt=0.0,
        le=3600.0,
        description="Max total execution time in seconds. Guard default: 300 (5 min).",
    )
    max_repeated_sequence: int = Field(
        3,
        ge=2,
        le=10,
        description="Circular-sequence detection window. Guard default: 3.",
    )

    model_config = ConfigDict(use_enum_values=True)
class Profile(BaseModel):
    """
    Root profile model containing all module configurations.

    This is the high-level "Persona" that maps to low-level technical parameters.
    """
    name: str = Field(..., description="Profile identifier (e.g., 'SCHOOL_DEFAULT')")
    description: str | None = Field(None, description="Human-readable description")

    # Module configurations
    physics: PhysicsConfig = Field(default_factory=PhysicsConfig, description="Physics module config")
    pedagogy: PedagogyConfig = Field(default_factory=PedagogyConfig, description="Pedagogy module config")
    governance: GovernanceConfig = Field(default_factory=GovernanceConfig, description="Governance module config")
    routing: RoutingConfig = Field(default_factory=RoutingConfig, description="Routing module config")
    execution_guard: ExecutionGuardConfig | None = Field(
        None,
        description="Optional per-profile ExecutionGuard limits. None = hard-coded defaults.",
    )

    # Metadata
    version: str | None = Field("1.0.0", description="Profile version")
    tags: list[str] | None = Field(None, description="Tags for filtering/searching")

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={'example': {'name': 'SCHOOL_DEFAULT', 'description': 'Default school profile: High resilience, low reactivity', 'physics': {'reactivity': 0.2, 'resilience': 0.9, 'safety_bias': 0.8, 'base_mode': 'SCHOOL'}, 'pedagogy': {'vygotsky_level': 0.7, 'scaffolding_aggressiveness': 0.6, 'intervention_threshold': 0.4}, 'governance': {'policy_id': 'school_policy', 'pii_mode': 'FULL', 'audit_level': 'VERBOSE'}, 'routing': {'llm_tier_strategy': 'QUALITY_OPTIMIZED'}}},
    )
