"""
Narrative Engine - LLM Orchestration with Automatic Physics & Safety Constraints
================================================================================

This module provides narrative generation that automatically enforces:
1. Physics constraints (Phi, Entropy) - tone must match emotional state
2. Safety filters (Ethics Engine) - prevents harmful content
3. Provider-agnostic LLM calls via LiteLLM

The App layer should NOT manually add these constraints - the SDK enforces them automatically.
"""

import os
import logging
from typing import Dict, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from phionyx_core.contracts.llm_provider import LLMProviderProtocol

# litellm imports removed - using centralized LLM service instead

logger = logging.getLogger(__name__)


@dataclass
class NarrativeConfig:
    """Configuration for NarrativeEngine."""
    # LLM Provider Configuration
    llm_provider: str = None  # "openai", "ollama", "anthropic", etc.
    llm_model: str = None  # Model name (e.g., "gpt-4o", "llama3.1:latest")
    llm_api_key: str = None
    llm_base_url: str = None  # For local models (Ollama)

    # Generation Parameters
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: float = 180.0

    # Safety & Physics
    enforce_physics_constraints: bool = True  # Auto-inject Phi constraints
    enforce_safety_filters: bool = True  # Auto-apply Ethics Engine

    def __post_init__(self):
        """Load from environment variables if not explicitly set."""
        if self.llm_provider is None:
            self.llm_provider = os.getenv("LLM_PROVIDER", "ollama")
        if self.llm_model is None:
            self.llm_model = os.getenv("LLM_MODEL", "llama3.1:latest")
        if self.llm_api_key is None:
            # Ollama doesn't require API key for local usage
            self.llm_api_key = os.getenv("LLM_API_KEY")  # None is OK for Ollama
        if self.llm_base_url is None:
            self.llm_base_url = os.getenv("LLM_BASE_URL") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


class NarrativeEngine:
    """
    Narrative generation engine with automatic physics and safety constraints.

    The SDK automatically enforces:
    - Physics constraints: Narrative tone must match Phi (emotional state)
    - Safety filters: Ethics Engine prevents harmful content

    Usage:
        engine = NarrativeEngine()
        response = await engine.generate(
            context="Player enters the tavern",
            physics_state={"phi": 0.5, "entropy": 0.3, "amplitude": 7.0}
        )
    """

    def __init__(
        self,
        config: Optional[NarrativeConfig] = None,
        llm_provider: Optional['LLMProviderProtocol'] = None
    ):
        """
        Initialize NarrativeEngine.

        Args:
            config: Configuration object. If None, uses defaults from env vars.
            llm_provider: LLM provider service (optional, will attempt to import if not provided).
                         This parameter enables dependency injection and breaks circular dependencies.
        """
        self.config = config or NarrativeConfig()
        self._llm_provider = llm_provider
        logger.info(f"NarrativeEngine initialized: {self.config.llm_provider}/{self.config.llm_model}")

    def _build_model_string(self) -> str:
        """Build model string for LiteLLM."""
        if self.config.llm_provider == "ollama":
            # Ollama format: "ollama/llama3.1:latest" or just model if base_url is set
            if self.config.llm_base_url and self.config.llm_base_url != "http://localhost:11434":
                return self.config.llm_model
            return f"ollama/{self.config.llm_model}"
        elif self.config.llm_provider == "openai":
            return self.config.llm_model
        else:
            # Other providers: "provider/model"
            return f"{self.config.llm_provider}/{self.config.llm_model}"

    def _inject_physics_constraints(
        self,
        system_prompt: str,
        physics_state: Dict[str, float]
    ) -> str:
        """
        Automatically inject Physics constraints into system prompt.

        CRUCIAL: This enforces that narrative tone matches Phi (emotional state).
        If Phi < 0.3 (Fractured), narrative MUST be dark/struggling.

        Args:
            system_prompt: Base system prompt
            physics_state: Physics state dict with phi, entropy, amplitude, etc.

        Returns:
            Enhanced system prompt with physics constraints
        """
        if not self.config.enforce_physics_constraints:
            return system_prompt

        phi = physics_state.get("phi", 0.5)
        entropy = physics_state.get("entropy", 0.5)
        _amplitude = physics_state.get("amplitude", 5.0)

        physics_constraints = []

        # Hard constraint: Phi < 0.3 MUST be dark/struggling
        if phi < 0.3:
            physics_constraints.append(
                f"[PHYSICS CONSTRAINT: FRACTURED STATE]\n"
                f"The character's Echo Quality (Phi={phi:.3f}) is critically low. "
                f"The narrative tone MUST be dark, struggling, and chaotic. "
                f"Do NOT resolve the tension yet. Use words like: dark, struggle, pain, fear, chaos, broken, lost, despair. "
                f"Avoid: happy, success, victory, celebration, relief, peace, calm."
            )
        elif phi < 0.5:
            physics_constraints.append(
                f"[PHYSICS CONSTRAINT: LOW STATE]\n"
                f"The character's Echo Quality (Phi={phi:.3f}) is low. "
                f"The tone should be uncertain, tense, and challenging. "
                f"Do not make it overly positive or resolved."
            )
        elif phi >= 0.7:
            physics_constraints.append(
                f"[PHYSICS CONSTRAINT: HIGH STATE]\n"
                f"The character's Echo Quality (Phi={phi:.3f}) is high. "
                f"The narrative can be more positive, but still maintain depth and complexity."
            )

        # Entropy constraint: High entropy = chaos/anxiety
        if entropy > 0.7:
            physics_constraints.append(
                f"[PHYSICS CONSTRAINT: HIGH ENTROPY]\n"
                f"The character's Entropy (chaos level) is {entropy:.3f} (high). "
                f"The narrative should reflect anxiety, uncertainty, and internal chaos."
            )
        elif entropy < 0.3:
            physics_constraints.append(
                f"[PHYSICS CONSTRAINT: LOW ENTROPY]\n"
                f"The character's Entropy (chaos level) is {entropy:.3f} (low). "
                f"The narrative should reflect calm, clarity, and focus."
            )

        if physics_constraints:
            enhanced_prompt = f"{system_prompt}\n\n" + "\n\n".join(physics_constraints)
            logger.debug(f"Injected {len(physics_constraints)} physics constraints (Phi={phi:.3f})")
            return enhanced_prompt

        return system_prompt

    def _apply_safety_filters(
        self,
        prompt: str,
        physics_state: Dict[str, float]
    ) -> str:
        """
        Automatically apply Safety filters (Ethics Engine).

        CRUCIAL: This prevents harmful content generation.

        Args:
            prompt: User prompt
            physics_state: Physics state (for entropy-based safety checks)

        Returns:
            Filtered prompt (or original if safe)
        """
        if not self.config.enforce_safety_filters:
            return prompt

        # Basic safety: Check for high entropy + potentially harmful keywords
        entropy = physics_state.get("entropy", 0.5)

        # If entropy is very high (>0.9), add safety reminder
        if entropy > 0.9:
            safety_note = (
                "\n[SAFETY REMINDER: The character is in extreme distress. "
                "Maintain therapeutic boundaries. Do not generate content that could harm the user. "
                "Focus on resilience, support, and growth opportunities rather than despair."
            )
            return prompt + safety_note

        return prompt

    async def generate(
        self,
        context: str,
        physics_state: Dict[str, float],
        system_prompt: Optional[str] = None,
        memory_context: Optional[str] = None,
        intuitive_context: Optional[str] = None,
        seasonal_context: Optional[str] = None,
        user_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate narrative with automatic physics and safety constraints.

        CRUCIAL: The SDK automatically enforces:
        - Physics constraints (tone must match Phi)
        - Safety filters (Ethics Engine)

        The App layer should NOT manually add these - they are enforced automatically.

        Args:
            context: Scene context or user input
            physics_state: Physics state dict (phi, entropy, amplitude, etc.)
            system_prompt: Base system prompt (optional)
            memory_context: RAG context from Memory System (optional)
            intuitive_context: GraphRAG hidden context (optional)
            seasonal_context: Seasonal context (optional)
            user_prompt: User's explicit prompt (optional, defaults to context)
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Generated narrative text

        Raises:
            ValueError: If physics_state is missing required keys
            RuntimeError: If centralized LLM service is not available
        """
        # Validate physics_state
        if "phi" not in physics_state:
            raise ValueError("physics_state must contain 'phi' key")

        # Build base system prompt
        if system_prompt is None:
            system_prompt = "You are a narrative generator for an interactive therapeutic game."

        # Inject memory context (RAG)
        if memory_context:
            system_prompt += f"\n\n[CONTEXT: MEMORIES]\n{memory_context}"

        # Inject intuitive context (GraphRAG - THE MAGIC)
        if intuitive_context:
            system_prompt += (
                f"\n\n[INTUITION ENGINE: HIDDEN CONTEXT]\n{intuitive_context}\n\n"
                f"Use this hidden context to understand not just what the user says, "
                f"but what they mean and why. Address hidden emotions and connections."
            )

        # Inject seasonal context
        if seasonal_context:
            system_prompt += f"\n\n[SEASONAL CONTEXT]\n{seasonal_context}\n\nReflect this seasonal atmosphere in the narrative."

        # AUTOMATIC: Inject Physics constraints
        system_prompt = self._inject_physics_constraints(system_prompt, physics_state)

        # AUTOMATIC: Apply Safety filters
        user_input = user_prompt or context
        user_input = self._apply_safety_filters(user_input, physics_state)

        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]

        # Get generation parameters
        temperature = kwargs.get("temperature", self.config.temperature)
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        top_p = kwargs.get("top_p", getattr(self.config, "top_p", 0.9))  # Default 0.9 if not in config

        # Get LLM provider (dependency injection or fallback to import)
        llm_service = self._get_llm_provider()
        if not llm_service or not llm_service.available:
            raise RuntimeError("LLM service not available")

        # Get model string for logging
        model_string = self._build_model_string()
        logger.debug(f"Calling LLM service: {model_string} (Phi={physics_state.get('phi', 0.5):.3f})")

        # Use LLM service for completion
        narrative = await llm_service.completion(
            messages=messages,
            model=self.config.llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
            **{"top_p": top_p} if top_p else {}
        )

        logger.info(f"Narrative generated successfully (length: {len(narrative)})")
        return narrative

    def _get_llm_provider(self) -> Optional['LLMProviderProtocol']:
        """
        Get LLM provider (dependency injection only).

        Returns:
            LLM provider instance or None if unavailable

        Raises:
            RuntimeError: If LLM provider is not injected (architectural violation)
        """
        # If provided via dependency injection, use it
        if self._llm_provider is not None:
            return self._llm_provider

        # No fallback - architectural violation removed
        logger.error(
            "LLM provider not injected. "
            "NarrativeEngine requires LLMProviderProtocol to be passed via __init__. "
            "This is a dependency injection requirement to maintain layer isolation."
        )
        return None

    async def check_model_availability(self) -> Dict[str, Any]:
        """Check if configured model is available via LLM service."""
        llm_service = self._get_llm_provider()
        if not llm_service or not llm_service.available:
            return {
                "available": False,
                "reason": "LLM service not available"
            }

        # Try a simple completion to check availability
        _model_string = self._build_model_string()
        try:
            _response = await llm_service.completion(
                messages=[{"role": "user", "content": "test"}],
                model=self.config.llm_model,
                max_tokens=1
            )
            return {"available": True, "reason": "Model is ready"}
        except Exception as e:
            logger.warning(f"Model availability check failed: {e}")
            return {"available": False, "reason": str(e)}

