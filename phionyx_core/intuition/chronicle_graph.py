"""
Chronicle Graph Extensions for GraphEngine
==========================================

Chronicle Graph API methods for Echo Chronicles character development.
Integrates with GraphEngine to store character events and retrieve subgraphs
for narrative generation.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ChronicleGraphAPI:
    """
    Chronicle Graph API - Extension methods for GraphEngine.

    Provides methods for:
    - Storing character events (choices, scenes, echo transformations)
    - Retrieving character subgraphs for narrative generation
    - Linking events to GraphEngine concepts
    """

    def __init__(self, graph_engine):
        """
        Initialize Chronicle Graph API.

        Args:
            graph_engine: GraphEngine instance
        """
        self.graph_engine = graph_engine
        self.user_id = graph_engine.user_id
        self.client = graph_engine.client

    async def upsert_character_event(
        self,
        character_id: str,
        event_type: str,
        event_payload: Dict,
        concept_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Add or update an event node in Chronicle Graph.

        Args:
            character_id: Character identifier
            event_type: Type of event ('choice', 'scene', 'echo_transformation', 'npc_interaction', 'location_visit')
            event_payload: Event data (choice_id, scene_id, echo_delta, physics_snapshot, etc.)
            concept_id: Optional link to GraphEngine concept

        Returns:
            Event ID (UUID) or None if failed
        """
        if not self.client:
            # Offline mode: generate temporary ID
            return str(uuid.uuid4())

        try:
            event_data = {
                "character_id": character_id,
                "user_id": self.user_id,
                "event_type": event_type,
                "event_payload": event_payload,
                "concept_id": concept_id,
                "created_at": datetime.now().isoformat()
            }

            # Insert event
            result = self.client.table("chronicle_events").insert(event_data).execute()

            if result.data and len(result.data) > 0:
                event_id = result.data[0]["id"]
                logger.info(f"ChronicleGraph: Created event {event_id} for character {character_id} ({event_type})")
                return event_id

            return None
        except Exception as e:
            logger.error(f"ChronicleGraph: Failed to upsert character event: {e}")
            return None

    async def get_character_subgraph(
        self,
        character_id: str,
        window: int = 10,
        include_relationships: bool = True
    ) -> Dict:
        """
        Get relevant subgraph for narrative generation.

        Args:
            character_id: Character identifier
            window: Number of recent events to include (default: 10)
            include_relationships: Include NPC relationships and locations

        Returns:
            Dict with nodes and edges for narrative context
        """
        if not self.client:
            return {
                "nodes": [],
                "edges": [],
                "summary": "Offline mode: No chronicle data available"
            }

        try:
            # Get recent events for character
            events_result = self.client.table("chronicle_events").select(
                "*"
            ).eq(
                "character_id", character_id
            ).eq(
                "user_id", self.user_id
            ).order(
                "created_at", desc=True
            ).limit(window).execute()

            events = events_result.data or []

            # Build subgraph structure
            nodes = []
            edges = []

            # Process events as nodes
            for event in events:
                node = {
                    "id": event["id"],
                    "type": "event",
                    "event_type": event["event_type"],
                    "payload": event["event_payload"],
                    "created_at": event["created_at"]
                }
                nodes.append(node)

                # Link to character if available
                if include_relationships:
                    edges.append({
                        "source": character_id,
                        "target": event["id"],
                        "type": "experienced",
                        "weight": 1.0
                    })

            # If concept_id links exist, fetch related concepts from GraphEngine
            concept_ids = [e.get("concept_id") for e in events if e.get("concept_id")]
            if concept_ids and include_relationships:
                # Fetch concepts and their associations
                # This integrates Chronicle Graph with GraphEngine concepts
                for concept_id in concept_ids:
                    _related = await self.graph_engine.get_related_concepts(
                        concept_name="",  # We'll need concept_id lookup
                        limit=5
                    )
                    # Add related concepts as nodes/edges

            # Generate summary for narrative context
            summary = self._generate_narrative_summary(events, character_id)

            return {
                "nodes": nodes,
                "edges": edges,
                "events": events,
                "summary": summary,
                "character_id": character_id,
                "window": window
            }

        except Exception as e:
            logger.error(f"ChronicleGraph: Failed to get character subgraph: {e}")
            return {
                "nodes": [],
                "edges": [],
                "summary": f"Error retrieving subgraph: {e}"
            }

    def _generate_narrative_summary(
        self,
        events: List[Dict],
        character_id: str
    ) -> str:
        """
        Generate a narrative summary from events.

        Args:
            events: List of event dicts
            character_id: Character identifier

        Returns:
            Narrative summary string
        """
        if not events:
            return f"Character {character_id} has no recorded events yet."

        # Group events by type
        choice_events = [e for e in events if e["event_type"] == "choice"]
        scene_events = [e for e in events if e["event_type"] == "scene"]
        echo_events = [e for e in events if e["event_type"] == "echo_transformation"]

        summary_parts = []

        if echo_events:
            summary_parts.append(f"Character has experienced {len(echo_events)} echo transformation(s).")

        if scene_events:
            scene_ids = [e["event_payload"].get("scene_id") for e in scene_events if e["event_payload"].get("scene_id")]
            summary_parts.append(f"Recent scenes: {', '.join(set(scene_ids[:3]))}.")

        if choice_events:
            summary_parts.append(f"Made {len(choice_events)} significant choice(s) recently.")

        return " ".join(summary_parts) if summary_parts else "Character history is emerging."

    async def get_recent_events(
        self,
        character_id: str,
        event_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Get recent events for a character, optionally filtered by type.

        Args:
            character_id: Character identifier
            event_type: Optional event type filter
            limit: Maximum number of events

        Returns:
            List of event dicts
        """
        if not self.client:
            return []

        try:
            query = self.client.table("chronicle_events").select("*").eq(
                "character_id", character_id
            ).eq(
                "user_id", self.user_id
            )

            if event_type:
                query = query.eq("event_type", event_type)

            result = query.order("created_at", desc=True).limit(limit).execute()

            return result.data or []
        except Exception as e:
            logger.error(f"ChronicleGraph: Failed to get recent events: {e}")
            return []

