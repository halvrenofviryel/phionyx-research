"""
Null/No-Op Implementations
===========================

Null implementations for all ports.
Used when a module is not included in product profile.

Key Principle:
- Pipeline remains stable when module is removed
- Null implementations return safe defaults
- No errors, just "module not available" behavior
"""

from typing import Dict, Any, List, Optional

from .physics_port import PhysicsPort
from .memory_port import MemoryPort
from .intuition_port import IntuitionPort
from .pedagogy_port import PedagogyPort
from .policy_port import PolicyPort
from .narrative_port import NarrativePort
from .meta_port import MetaPort


class NullPhysicsEngine(PhysicsPort):
    """Null implementation of Physics Port."""

    async def calculate_phi(
        self,
        amplitude: float,
        entropy: float,
        time_delta: float,
        gamma: float,
        stability: float,
        valence: float = 0.0,
        arousal: float = 1.0,
        w_c: float = 0.5,
        w_p: float = 0.5,
        context_mode: str = "DEFAULT",
        entropy_penalty_k: float = 0.5
    ) -> Dict[str, float]:
        """Calculate phi using direct SDK if available, otherwise return safe defaults."""
        try:
            # Try to use real physics calculation
            from phionyx_core.physics.formulas import calculate_phi_v2_1

            phi_result = calculate_phi_v2_1(
                amplitude=amplitude,
                entropy=entropy,
                time_delta=time_delta,
                gamma=gamma,
                stability=stability,
                valence=valence,
                arousal=arousal,
                w_c=w_c,
                w_p=w_p,
                entropy_penalty_k=entropy_penalty_k
            )

            return {
                "phi": phi_result.get("phi", 0.5),
                "phi_cognitive": phi_result.get("phi_cognitive", 0.5),
                "phi_physical": phi_result.get("phi_physical", 0.0),
                "consciousness": phi_result.get("consciousness", 0.5)
            }
        except ImportError:
            # Fallback: Return safe default phi values
            return {
                "phi": 0.5,  # Neutral default
                "phi_cognitive": 0.5,
                "phi_physical": 0.0,
                "consciousness": 0.5
            }

    async def calculate_consciousness(self, phi: float, entropy: float) -> float:
        return 0.5  # Neutral default

    async def calculate_resonance_force(self, phi: float, amplitude: float) -> float:
        return 0.5  # Neutral default

    async def adjust_gamma(self, current_gamma: float, entropy: float, stability: float) -> float:
        return current_gamma  # No adjustment


class NullMemoryEngine(MemoryPort):
    """Null implementation of Memory Port."""

    async def add_memory(
        self,
        content: str,
        user_id: str,
        importance: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Memory not available - return None."""
        return None

    async def search(
        self,
        query: str,
        limit: int = 5,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search memories - Null implementation returns empty list."""
        return []

    async def search_memories(
        self,
        query: str,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """No memories available - return empty list."""
        return []

    async def get_memory_by_id(
        self,
        memory_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        return None

    def is_connected(self) -> bool:
        """Null implementation is always "connected" (degraded mode)."""
        return True  # Return True so engine can use it (degraded)


class NullIntuitionEngine(IntuitionPort):
    """Null implementation of Intuition Port (GraphRAG disabled)."""

    def is_available(self) -> bool:
        """Null implementation is always "available" (degraded mode)."""
        return True  # Return True so engine can use it (degraded)

    async def extract_concepts(self, text: str) -> List[str]:
        """No concept extraction - return empty list."""
        return []

    async def discover_hidden_context(
        self,
        user_text: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Null implementation returns empty context."""
        return {
            "intuitive_context": None,
            "extracted_concepts": [],
            "inferred_contexts": []
        }

    async def infer_hidden_context(
        self,
        concepts: List[str],
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """No hidden context inference - return None."""
        return None

    async def build_concept_graph(
        self,
        concepts: List[str],
        relationships: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        return None


class NullPedagogyEngine(PedagogyPort):
    """Null implementation of Pedagogy Port."""

    async def assess_risk(
        self,
        user_input: str,
        physics_state: Dict[str, float],
        actor_ref: Optional[str] = None,
        tenant_ref: Optional[str] = None
    ) -> Dict[str, Any]:
        """Return safe default risk assessment."""
        return {
            "risk_level": 0,  # No risk
            "risk_type": "none",
            "recommendations": []
        }

    async def calculate_vygotsky_level(
        self,
        actor_ref: str,
        current_phi: float
    ) -> float:
        return 0.5  # Neutral default

    async def get_safe_template(
        self,
        risk_type: str,
        language: str = "tr",
        physics_state: Optional[Dict[str, float]] = None
    ) -> Optional[str]:
        return None

    def get_strictness_level(self) -> str:
        return "off"


class NullPolicyEngine(PolicyPort):
    """Null implementation of Policy Port."""

    async def select_policy(
        self,
        context_mode: Optional[str] = None,
        risk_level: int = 0,
        user_role: Optional[str] = None
    ) -> Optional[Any]:
        return None

    async def evaluate_content(
        self,
        content: str,
        policy: Any,
        physics_state: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        return {
            "decision": "allow",
            "blocking_reason": None
        }

    def get_default_policy(self) -> Any:
        return None


class NullNarrativeEngine(NarrativePort):
    """Null implementation of Narrative Port."""

    async def generate_narrative(
        self,
        user_input: str,
        context: str,
        physics_state: Dict[str, float],
        model_id: str,
        system_prompt: str,
        temperature: Optional[float] = None
    ) -> str:
        """Return safe default response."""
        return "I'm here to help. Could you tell me more about what you're thinking?"

    def get_mode(self) -> str:
        return "simple"

    async def apply_filters(self, narrative: str, filters: List[str]) -> str:
        return narrative  # No filtering


class NullMetaEngine(MetaPort):
    """Null implementation of Meta Port."""

    async def estimate_confidence(
        self,
        user_input: str,
        context: Optional[str] = None,
        memory_matches: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Return safe default confidence."""
        return {
            "confidence_score": 0.7,  # Moderate confidence
            "is_uncertain": False,
            "recommendation": "allow"
        }

    def get_hedging_phrase(self, language: str = "tr") -> str:
        return ""  # No hedging

    def is_available(self) -> bool:
        return False

