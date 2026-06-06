"""
Context Manager - State Machine for Context Switching
=====================================================

Manages context switching by flushing active context and loading
mode-specific memory blocks.
"""

from typing import Dict, Optional, List, Any
import logging

from .definitions import ContextMode, ContextDefinitions
from .detector import ModeDetector

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manages context switching across LLM sessions.

    Responsibilities:
    - Detect mode switches
    - Flush active context (short-term RAM)
    - Load mode-specific memory blocks
    - Inject system prompts for context awareness
    """

    def __init__(self, vector_store=None):
        """
        Initialize context manager.

        Args:
            vector_store: Optional VectorStore instance for memory retrieval
        """
        self.definitions = ContextDefinitions()
        self.detector = ModeDetector()
        self.vector_store = vector_store

        # Current state
        self.current_mode: Optional[ContextMode] = None
        self.active_context: Dict[str, Any] = {}
        self.loaded_memories: List[Dict] = []

        logger.info("ContextManager initialized")

    async def process(
        self,
        user_input: str,
        current_state: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process user input and determine if context switch is needed.

        Args:
            user_input: User's text input
            current_state: Current context state (optional)

        Returns:
            Dict with:
            - mode: Detected/current context mode
            - switch_required: Whether context should switch
            - system_prompt: System prompt to inject
            - memory_tags: Tags to filter memories
            - active_memories: Loaded memories for this mode
        """
        # Detect mode
        detection = self.detector.detect_mode(user_input, current_state)

        # Check if switch is required
        if detection.switch_required:
            await self.switch_context(detection.detected_mode)
            self.current_mode = detection.detected_mode
        elif self.current_mode is None:
            # First time, set to detected mode
            self.current_mode = detection.detected_mode

        # Get context definition
        definition = self.definitions.get_definition(self.current_mode)
        if not definition:
            definition = self.definitions.get_definition(ContextMode.DEFAULT)

        # Get primary rule
        rule = definition.get_primary_rule()
        if not rule:
            rule = self.definitions.get_definition(ContextMode.DEFAULT).get_primary_rule()

        # Build result
        result = {
            "mode": self.current_mode.value if self.current_mode else ContextMode.DEFAULT.value,
            "switch_required": detection.switch_required,
            "confidence": detection.confidence,
            "system_prompt": rule.system_prompt_prefix if rule else "",
            "memory_tags": rule.memory_tags if rule else [],
            "active_memories": self.loaded_memories,
            "detected_keywords": detection.detected_keywords,
        }

        return result

    async def switch_context(self, new_mode: ContextMode) -> None:
        """
        Switch context to a new mode.

        Actions:
        1. Flush current active context (short-term RAM)
        2. Load mode-specific memory blocks from Vector Store
        3. Prepare system prompt for context awareness

        Args:
            new_mode: Target context mode
        """
        logger.info(f"ContextManager: Switching context from {self.current_mode} to {new_mode.value}")

        # 1. Flush active context
        self.active_context = {}
        self.loaded_memories = []

        # 2. Get context definition
        definition = self.definitions.get_definition(new_mode)
        if not definition:
            logger.warning(f"ContextManager: No definition found for {new_mode.value}, using DEFAULT")
            definition = self.definitions.get_definition(ContextMode.DEFAULT)

        # 3. Load mode-specific memories from Vector Store
        if self.vector_store and definition.rules:
            primary_rule = definition.get_primary_rule()
            if primary_rule and primary_rule.memory_tags:
                await self._load_memories_for_mode(primary_rule.memory_tags)

        # 4. Update current mode
        self.current_mode = new_mode

        logger.info(
            f"ContextManager: Context switched to {new_mode.value}. "
            f"Loaded {len(self.loaded_memories)} memories."
        )

    async def _load_memories_for_mode(self, memory_tags: List[str]) -> None:
        """
        Load memories from Vector Store filtered by context_tags.

        Args:
            memory_tags: Context tags to filter memories (e.g., ["sdk_architecture", "api_design"])
        """
        if not self.vector_store:
            logger.warning("ContextManager: VectorStore not available, cannot load memories")
            return

        try:
            # Use retrieve_relevant with filter_tags for efficient tag-based filtering
            # Search with a generic query and filter by context_tags
            all_memories = []
            for tag in memory_tags:
                # Use retrieve_relevant with filter_tags parameter
                results = await self.vector_store.retrieve_relevant(
                    query_text=tag,
                    user_id="system",  # System-level context memories
                    limit=5,
                    filter_tags=[tag]  # Filter by this specific tag
                )
                all_memories.extend(results)

            # Deduplicate by memory ID
            seen_ids = set()
            unique_memories = []
            for memory in all_memories:
                memory_id = memory.get("id")
                if memory_id and memory_id not in seen_ids:
                    seen_ids.add(memory_id)
                    unique_memories.append(memory)

            self.loaded_memories = unique_memories[:10]  # Limit to 10 most relevant

            logger.info(
                f"ContextManager: Loaded {len(self.loaded_memories)} memories "
                f"for context_tags: {memory_tags}"
            )
        except Exception as e:
            logger.error(f"ContextManager: Failed to load memories: {e}")
            self.loaded_memories = []

    def get_active_context(self) -> Dict[str, Any]:
        """Get current active context state."""
        return {
            "current_mode": self.current_mode.value if self.current_mode else None,
            "active_memories_count": len(self.loaded_memories),
            "active_context": self.active_context,
        }

    def reset(self) -> None:
        """Reset context manager to initial state."""
        self.current_mode = None
        self.active_context = {}
        self.loaded_memories = []
        logger.info("ContextManager: Reset to initial state")

