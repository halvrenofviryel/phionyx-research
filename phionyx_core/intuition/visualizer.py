"""
Graph Visualizer - Export graph data for visualization
======================================================

Exports the knowledge graph in formats compatible with:
- Cosmograph (https://cosmograph.app/)
- Cytoscape.js (https://js.cytoscape.org/)

This is crucial for "Visual Proof" in documentation and pitch decks.
"""

import logging
from typing import Any

try:
    from supabase import Client
except ImportError:
    Client = None

logger = logging.getLogger(__name__)


class GraphVisualizer:
    """
    Exports knowledge graph data for visualization tools.

    Usage:
        visualizer = GraphVisualizer(client, user_id)
        graph_data = await visualizer.export_for_cosmograph()
        # Use graph_data in Cosmograph or Cytoscape.js
    """

    def __init__(self, client: Client, user_id: str):
        """
        Initialize graph visualizer.

        Args:
            client: Supabase client
            user_id: User UUID
        """
        self.client = client
        self.user_id = user_id

    async def export_for_cosmograph(
        self,
        min_weight: float = 0.3,
        limit_nodes: int | None = None
    ) -> dict[str, Any]:
        """
        Export graph in Cosmograph-compatible JSON format.

        Cosmograph format:
        {
            "nodes": [
                {"id": "uuid", "label": "Concept Name", "category": "emotion", ...}
            ],
            "links": [
                {"source": "uuid1", "target": "uuid2", "weight": 0.8, ...}
            ]
        }

        Args:
            min_weight: Minimum edge weight to include
            limit_nodes: Maximum number of nodes (None = all)

        Returns:
            Dictionary with 'nodes' and 'links' arrays
        """
        if not self.client:
            return {"nodes": [], "links": []}

        try:
            # Load concepts
            concepts_query = self.client.table("concepts").select("*").eq("user_id", self.user_id)
            if limit_nodes:
                concepts_query = concepts_query.limit(limit_nodes)

            concepts_res = concepts_query.execute()
            concepts = {c["id"]: c for c in concepts_res.data or []}

            # Load associations
            associations_res = self.client.table("associations").select("*").eq(
                "user_id", self.user_id
            ).gte("weight", min_weight).execute()

            # Build nodes array
            nodes = []
            for concept_id, concept in concepts.items():
                nodes.append({
                    "id": concept_id,
                    "label": concept.get("name", "Unknown"),
                    "category": concept.get("category", "abstract"),
                    "total_mentions": concept.get("total_mentions", 0),
                    "avg_phi": concept.get("avg_phi_when_mentioned", 0.0),
                    "first_seen": concept.get("first_seen_at"),
                    "last_seen": concept.get("last_seen_at")
                })

            # Build links array
            links = []
            for assoc in associations_res.data or []:
                source_id = assoc["source_id"]
                target_id = assoc["target_id"]

                # Only include links where both nodes exist
                if source_id in concepts and target_id in concepts:
                    links.append({
                        "source": source_id,
                        "target": target_id,
                        "weight": assoc.get("weight", 0.0),
                        "max_phi": assoc.get("max_phi", 0.0),
                        "co_occurrences": assoc.get("total_co_occurrences", 1),
                        "first_seen": assoc.get("first_seen_at"),
                        "last_seen": assoc.get("last_seen_at")
                    })

            logger.info(f"GraphVisualizer: Exported {len(nodes)} nodes, {len(links)} links for Cosmograph")

            return {
                "nodes": nodes,
                "links": links,
                "metadata": {
                    "user_id": self.user_id,
                    "total_nodes": len(nodes),
                    "total_links": len(links),
                    "min_weight": min_weight
                }
            }

        except Exception as e:
            logger.error(f"GraphVisualizer: Failed to export for Cosmograph: {e}")
            return {"nodes": [], "links": [], "error": str(e)}

    async def export_for_cytoscape(
        self,
        min_weight: float = 0.3,
        limit_nodes: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Export graph in Cytoscape.js-compatible JSON format.

        Cytoscape format:
        [
            {
                "data": {"id": "uuid", "label": "Concept Name", ...},
                "group": "nodes"
            },
            {
                "data": {"source": "uuid1", "target": "uuid2", "weight": 0.8, ...},
                "group": "edges"
            }
        ]

        Args:
            min_weight: Minimum edge weight to include
            limit_nodes: Maximum number of nodes (None = all)

        Returns:
            List of Cytoscape elements
        """
        if not self.client:
            return []

        try:
            # Load concepts
            concepts_query = self.client.table("concepts").select("*").eq("user_id", self.user_id)
            if limit_nodes:
                concepts_query = concepts_query.limit(limit_nodes)

            concepts_res = concepts_query.execute()
            concepts = {c["id"]: c for c in concepts_res.data or []}

            # Load associations
            associations_res = self.client.table("associations").select("*").eq(
                "user_id", self.user_id
            ).gte("weight", min_weight).execute()

            elements = []

            # Add nodes
            for concept_id, concept in concepts.items():
                elements.append({
                    "data": {
                        "id": concept_id,
                        "label": concept.get("name", "Unknown"),
                        "category": concept.get("category", "abstract"),
                        "total_mentions": concept.get("total_mentions", 0),
                        "avg_phi": concept.get("avg_phi_when_mentioned", 0.0)
                    },
                    "group": "nodes"
                })

            # Add edges
            for assoc in associations_res.data or []:
                source_id = assoc["source_id"]
                target_id = assoc["target_id"]

                # Only include links where both nodes exist
                if source_id in concepts and target_id in concepts:
                    elements.append({
                        "data": {
                            "id": f"{source_id}-{target_id}",
                            "source": source_id,
                            "target": target_id,
                            "weight": assoc.get("weight", 0.0),
                            "max_phi": assoc.get("max_phi", 0.0),
                            "co_occurrences": assoc.get("total_co_occurrences", 1)
                        },
                        "group": "edges"
                    })

            logger.info(f"GraphVisualizer: Exported {len(elements)} elements for Cytoscape.js")
            return elements

        except Exception as e:
            logger.error(f"GraphVisualizer: Failed to export for Cytoscape.js: {e}")
            return []

    async def export_statistics(self) -> dict[str, Any]:
        """
        Export graph statistics for documentation.

        Returns:
            Dictionary with graph metrics
        """
        if not self.client:
            return {}

        try:
            # Count concepts
            concepts_res = self.client.table("concepts").select("id", count="exact").eq(
                "user_id", self.user_id
            ).execute()
            total_concepts = concepts_res.count or 0

            # Count associations
            associations_res = self.client.table("associations").select("id", count="exact").eq(
                "user_id", self.user_id
            ).execute()
            total_associations = associations_res.count or 0

            # Get top concepts by mentions
            top_concepts_res = self.client.table("concepts").select("name, total_mentions, category").eq(
                "user_id", self.user_id
            ).order("total_mentions", desc=True).limit(10).execute()

            # Get strongest associations
            top_associations_res = self.client.table("associations").select(
                "weight, max_phi, total_co_occurrences"
            ).eq("user_id", self.user_id).order("weight", desc=True).limit(10).execute()

            return {
                "total_concepts": total_concepts,
                "total_associations": total_associations,
                "top_concepts": top_concepts_res.data or [],
                "top_associations": top_associations_res.data or [],
                "density": total_associations / max(total_concepts * (total_concepts - 1) / 2, 1) if total_concepts > 1 else 0.0
            }

        except Exception as e:
            logger.error(f"GraphVisualizer: Failed to export statistics: {e}")
            return {}

