"""
Graph Engine - The Intuition Motor
==================================

This module implements a lightweight GraphRAG system that:
1. Extracts concepts from user input using LLM
2. Forms associations between concepts weighted by Phi (physics resonance)
3. Infers hidden context through graph traversal
4. Stores everything in Supabase for persistence

The magic: When user says "Darkness", the engine can infer "Fear"
through the graph: Darkness -> Cave -> Fear (weight: 0.9)
"""

import logging
import os
from typing import List, Dict, Optional, Tuple, Any, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
import uuid

try:
    import networkx as nx
except ImportError:
    nx = None

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None
# litellm imports removed - using centralized LLM service instead

if TYPE_CHECKING:
    from phionyx_core.contracts.llm_provider import LLMProviderProtocol
    from phionyx_core.contracts.database import GraphRepositoryProtocol

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

class EdgeType(str, Enum):
    """Typed relationship between concepts (v4 §1 Entity Layer)."""
    RELATED = "related"          # Default co-occurrence
    CAUSES = "causes"            # Causal: A causes B
    IS_A = "is_a"                # Taxonomic: A is a type of B
    PART_OF = "part_of"          # Mereological: A is part of B
    CONTRADICTS = "contradicts"  # Contradiction: A contradicts B
    PRECEDES = "precedes"        # Temporal: A happens before B
    INFLUENCES = "influences"    # Weak causal: A influences B


@dataclass
class Concept:
    """A concept extracted from text."""
    id: Optional[str] = None
    name: str = ""
    normalized_name: str = ""
    category: str = ""  # emotion, person, location, abstract, object, action, trait
    confidence: float = 0.0
    observation_source: str = ""  # v4: where this concept was observed (user_input, llm, system)
    first_observed: Optional[str] = None  # v4: ISO timestamp of first observation


@dataclass
class Association:
    """An edge between two concepts."""
    source_id: str
    target_id: str
    weight: float
    formation_phi: float
    edge_type: str = EdgeType.RELATED.value  # v4: typed relationship
    context: Optional[str] = None


@dataclass
class HiddenContext:
    """Inferred hidden context from graph traversal."""
    concept_id: str
    concept_name: str
    path_weight: float
    path_length: int
    reasoning: str


# ============================================================================
# GRAPH ENGINE
# ============================================================================

class GraphEngine:
    """
    The Intuition Engine - GraphRAG for hidden associations.

    Usage:
        engine = GraphEngine(user_id="...")
        concepts = await engine.extract_concepts("I'm afraid of the dark")
        await engine.form_associations(concepts, phi=0.8)
        hidden = await engine.infer_hidden_context(["darkness"])
    """

    def __init__(
        self,
        actor_ref: str,
        llm_provider: Optional['LLMProviderProtocol'] = None,
        graph_repository: Optional['GraphRepositoryProtocol'] = None
    ):  # SPRINT 5: Replaced user_id with actor_ref (core-neutral)
        """
        Initialize the Graph Engine.

        Args:
            actor_ref: Actor reference (core-neutral identifier, replaces user_id)
            llm_provider: LLM provider service (optional, will attempt to import if not provided).
                         This parameter enables dependency injection and breaks circular dependencies.
            graph_repository: Graph repository (optional). If provided, uses repository for DB access.
                            If None, falls back to direct Supabase client (backward compatible).
        """
        self.actor_ref = actor_ref  # SPRINT 5: Use actor_ref
        # SPRINT 5: For backward compatibility with DB queries, we still use user_id in DB calls
        # but store actor_ref internally (DB migration can happen later)
        self.user_id = actor_ref  # SPRINT 5: Map actor_ref to user_id for DB compatibility

        # Store repository (if provided)
        self._graph_repository = graph_repository

        self.client: Optional[Client] = None
        self._init_supabase()

        # In-memory graph for fast traversal (loaded from DB)
        if nx is not None:
            self.graph = nx.DiGraph()
        else:
            self.graph = None
            logger.debug("networkx not available — graph engine disabled")
        self._load_graph_cache()

        # Embedding configuration (for Entity Resolution - Microsoft GraphRAG)
        # Use centralized LLM service for embeddings
        self.embedding_provider = os.getenv("EMBEDDING_PROVIDER", "ollama")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "llama3.1:latest")
        self._llm_provider = llm_provider
        self.embeddings_enabled = True  # Centralized service handles availability

    def _init_supabase(self):
        """Initialize Supabase client (fallback if repository not provided)."""
        if self._graph_repository is None:
            # Backward compatible: Use direct Supabase client
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

            if supabase_url and supabase_key:
                try:
                    self.client = create_client(supabase_url, supabase_key)
                    logger.info(f"GraphEngine: Supabase connected for user {self.user_id} (direct client - backward compatible)")
                except Exception as e:
                    logger.error(f"GraphEngine: Failed to connect to Supabase: {e}")
                    self.client = None
            else:
                logger.warning("GraphEngine: Supabase credentials not found, running in offline mode")
                self.client = None
        else:
            # Use repository (preferred path)
            self.client = None
            logger.info("GraphEngine: Initialized with repository (preferred path)")

    def _load_graph_cache(self):
        """Load graph from Supabase into NetworkX for fast traversal."""
        if not self.client:
            return

        try:
            # Load concepts
            concepts_res = self.client.table("concepts").select("*").eq("user_id", self.user_id).execute()
            concepts = {c["id"]: c for c in concepts_res.data or []}

            # Load associations
            associations_res = self.client.table("associations").select("*").eq("user_id", self.user_id).execute()

            # Build graph
            self.graph.clear()
            for assoc in associations_res.data or []:
                source_id = assoc["source_id"]
                target_id = assoc["target_id"]
                weight = assoc["weight"]

                if source_id in concepts and target_id in concepts:
                    self.graph.add_edge(
                        source_id,
                        target_id,
                        weight=weight,
                        max_phi=assoc.get("max_phi", 0.0),
                        edge_type=assoc.get("edge_type", EdgeType.RELATED.value),
                        context=assoc.get("last_context")
                    )

            logger.info(f"GraphEngine: Loaded {len(concepts)} concepts, {len(associations_res.data or [])} edges")
        except Exception as e:
            logger.error(f"GraphEngine: Failed to load graph cache: {e}")

    async def extract_concepts(
        self,
        text: str,
        model: str = None
    ) -> List[Concept]:
        """
        Extract key concepts from user input using centralized LLM service.

        Args:
            text: User input text
            model: LLM model to use. If None, uses default from centralized service

        Returns:
            List of extracted concepts with categories
        """
        if not text or not text.strip():
            return []

        llm_service = self._get_llm_provider()
        if not llm_service or not llm_service.available:
            logger.warning("GraphEngine: LLM service not available, returning empty concepts")
            return []

        try:
            # Extract concepts using LLM service
            concepts = await llm_service.extract_concepts(text, model=model)

            # Convert LLM service Concept objects to GraphEngine Concept objects
            graph_concepts = []
            for concept in concepts:
                graph_concept = Concept(
                    id=None,  # Will be set when stored in DB
                    name=concept.name,
                    normalized_name=concept.name.lower().strip(),
                    category=concept.category,
                    confidence=concept.confidence
                )
                graph_concepts.append(graph_concept)

            logger.info(f"GraphEngine: Extracted {len(graph_concepts)} concepts from text")
            return graph_concepts

        except Exception as e:
            logger.error(f"GraphEngine: Failed to extract concepts: {e}")
            return []

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
            "GraphEngine requires LLMProviderProtocol to be passed via __init__. "
            "This is a dependency injection requirement to maintain layer isolation."
        )
        return None

    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for entity resolution (Microsoft GraphRAG style).

        Args:
            text: Concept name to embed

        Returns:
            Embedding vector (1536 dimensions) or None if failed
        """
        if not self.embeddings_enabled:
            return None

        llm_service = self._get_llm_provider()
        if not llm_service or not llm_service.available:
            logger.warning("GraphEngine: LLM service not available, returning None")
            return None

        try:
            # Generate embedding using LLM service
            embedding_vector = await llm_service.embedding(text, model=self.embedding_model, use_cache=True)

            if embedding_vector:
                logger.debug(f"Generated embedding for '{text}' (dim: {len(embedding_vector)}) via centralized service")
                return embedding_vector
            else:
                logger.warning(f"Failed to generate embedding for '{text}': Centralized service returned None")
                return None

        except ImportError as e:
            logger.error(f"GraphEngine: Failed to import centralized LLM service: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to generate embedding for '{text}': {e}")
            return None

    async def get_or_create_concept(
        self,
        concept: Concept,
        phi: float = 0.0
    ) -> Optional[str]:
        """
        Get existing concept ID or create new one in database.

        MICROSOFT GRAPHRAG UPGRADE: Now includes Entity Resolution via embeddings.
        Before creating a new concept, searches for similar concepts (cosine similarity > 0.90)
        and merges them to prevent graph fragmentation.

        Args:
            concept: Concept to get/create
            phi: Physics score when this concept was mentioned

        Returns:
            Concept UUID or None if failed
        """
        if not self.client:
            # Offline mode: generate temporary ID
            return str(uuid.uuid4())

        try:
            # STEP 1: Generate embedding for entity resolution
            concept_embedding = None
            if self.embeddings_enabled:
                concept_embedding = await self._generate_embedding(concept.name)
                if concept_embedding:
                    logger.debug(f"Entity Resolution: Generated embedding for '{concept.name}'")

            # STEP 2: Call Supabase function with embedding (if available)
            # The function will:
            # - Try exact match first (fast path)
            # - If no exact match AND embedding provided: Search for similar concepts (similarity > 0.90)
            # - If similar concept found: MERGE (return existing ID, update stats)
            # - If no similar concept: CREATE NEW

            params = {
                "p_user_id": self.user_id,
                "p_name": concept.name,
                "p_category": concept.category,
                "p_phi": phi
            }

            # Add embedding if available (for entity resolution)
            if concept_embedding:
                params["p_embedding"] = concept_embedding

            result = self.client.rpc(
                "get_or_create_concept",
                params
            ).execute()

            if result.data:
                concept_id = result.data
                concept.id = concept_id

                # Log if entity resolution occurred (would need to check if it was a merge)
                if concept_embedding:
                    logger.debug(f"Entity Resolution: Processed '{concept.name}' (ID: {concept_id})")

                return concept_id
            else:
                logger.warning("GraphEngine: get_or_create_concept returned no data")
                return None

        except Exception as e:
            logger.error(f"GraphEngine: Failed to get/create concept: {e}")
            return None

    async def form_associations(
        self,
        concepts: List[Concept],
        phi: float,
        context: Optional[str] = None,
        edge_type: str = EdgeType.RELATED.value,
    ) -> List[Association]:
        """
        Form associations between all pairs of concepts, weighted by Phi.

        Args:
            concepts: List of concepts that appeared together
            phi: Physics resonance score (0.0 - 1.0)
            context: Original text context
            edge_type: Typed relationship (v4 §1 Entity Layer)

        Returns:
            List of formed associations
        """
        if len(concepts) < 2:
            return []

        associations = []

        # Get/create concept IDs
        concept_ids = []
        for concept in concepts:
            concept_id = await self.get_or_create_concept(concept, phi)
            if concept_id:
                concept_ids.append((concept_id, concept))

        if len(concept_ids) < 2:
            return []

        # Form associations between all pairs
        for i, (source_id, source_concept) in enumerate(concept_ids):
            for target_id, target_concept in concept_ids[i+1:]:
                # Prevent self-loops
                if source_id == target_id:
                    continue

                # Call Supabase function to form/strengthen association
                if self.client:
                    try:
                        result = self.client.rpc(
                            "form_association",
                            {
                                "p_user_id": self.user_id,
                                "p_source_id": source_id,
                                "p_target_id": target_id,
                                "p_phi": phi,
                                "p_context": context
                            }
                        ).execute()

                        if result.data:
                            _assoc_id = result.data
                            # Update in-memory graph with edge_type
                            self.graph.add_edge(
                                source_id,
                                target_id,
                                weight=min(1.0, 0.1 + (phi * 0.1)),
                                max_phi=phi,
                                edge_type=edge_type,
                                context=context
                            )

                            associations.append(Association(
                                source_id=source_id,
                                target_id=target_id,
                                weight=min(1.0, 0.1 + (phi * 0.1)),
                                formation_phi=phi,
                                edge_type=edge_type,
                                context=context
                            ))
                    except Exception as e:
                        logger.error(f"GraphEngine: Failed to form association: {e}")

        logger.info(f"GraphEngine: Formed {len(associations)} [{edge_type}] associations with phi={phi:.2f}")
        return associations

    def add_relationship(
        self,
        source: str,
        target: str,
        relationship_type: str = "causes",
        weight: float = 0.5
    ):
        """
        Add a relationship between two concepts (synchronous wrapper for testing).

        This is a convenience method for tests. For production, use form_associations().

        Args:
            source: Source concept name
            target: Target concept name
            relationship_type: Type of relationship (e.g., "causes", "relates_to")
            weight: Relationship weight (0.0-1.0)
        """
        import asyncio

        # Map relationship_type to EdgeType (backward compatible)
        edge_type = relationship_type
        try:
            edge_type = EdgeType(relationship_type).value
        except ValueError:
            edge_type = EdgeType.RELATED.value

        # Create Concept objects
        source_concept = Concept(
            name=source,
            normalized_name=source.lower().strip(),
            category="abstract",
            confidence=weight,
            observation_source="test",
        )
        target_concept = Concept(
            name=target,
            normalized_name=target.lower().strip(),
            category="abstract",
            confidence=weight,
            observation_source="test",
        )

        # Use form_associations (async) - run in event loop if available
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, schedule the coroutine
                asyncio.create_task(self.form_associations(
                    [source_concept, target_concept], weight, edge_type=edge_type
                ))
            else:
                # If no loop is running, run it
                loop.run_until_complete(self.form_associations(
                    [source_concept, target_concept], weight, edge_type=edge_type
                ))
        except RuntimeError:
            # No event loop, create one
            asyncio.run(self.form_associations(
                [source_concept, target_concept], weight, edge_type=edge_type
            ))

    def infer_context(self, text: str) -> Dict[str, Any]:
        """
        Infer context from text (synchronous wrapper for testing).

        Args:
            text: Input text

        Returns:
            Dict with related_concepts list
        """
        import asyncio

        # Extract concept names from text (simplified)
        concept_names = [text.lower().strip()]

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, return empty (can't block)
                return {"related_concepts": []}
            else:
                # If no loop is running, run it
                hidden_contexts = loop.run_until_complete(self.infer_hidden_context(concept_names))
                return {
                    "related_concepts": [hc.concept_name for hc in hidden_contexts]
                }
        except RuntimeError:
            # No event loop, create one
            hidden_contexts = asyncio.run(self.infer_hidden_context(concept_names))
            return {
                "related_concepts": [hc.concept_name for hc in hidden_contexts]
            }

    async def infer_hidden_context(
        self,
        concept_names: List[str],
        max_hops: int = 2,
        min_weight: float = 0.3
    ) -> List[HiddenContext]:
        """
        Infer hidden context using Microsoft GraphRAG-style PageRank algorithm.

        MICROSOFT GRAPHRAG UPGRADE: Replaced simple shortest path with PageRank-based inference.
        This finds statistically "central" nodes in the ego-graph, providing more meaningful
        hidden context than simple path traversal.

        Algorithm:
        1. Load ego-graph (neighbors of neighbors) for input concepts
        2. Calculate PageRank on subgraph using edge weights (derived from Phi)
        3. Return top nodes with highest PageRank that were NOT in original input

        Args:
            concept_names: List of concept names to start from
            max_hops: Maximum graph traversal depth (for ego-graph construction)
            min_weight: Minimum edge weight to include in subgraph

        Returns:
            List of inferred hidden contexts with PageRank scores
        """
        if not self.client or not concept_names:
            return []

        # STEP 1: Find concept IDs from names
        concept_ids = []
        concept_id_to_name = {}
        for name in concept_names:
            normalized = name.lower().strip()
            try:
                result = self.client.table("concepts").select("id, name").eq(
                    "user_id", self.user_id
                ).eq("normalized_name", normalized).limit(1).execute()

                if result.data:
                    concept_id = result.data[0]["id"]
                    concept_ids.append(concept_id)
                    concept_id_to_name[concept_id] = result.data[0]["name"]
            except Exception as e:
                logger.error(f"GraphEngine: Failed to find concept '{name}': {e}")

        if not concept_ids:
            logger.warning("GraphEngine: No concept IDs found for inference")
            return []

        # STEP 2: Build ego-graph (neighbors of neighbors)
        # This creates a subgraph centered around the input concepts
        ego_graph = nx.DiGraph()
        nodes_to_include = set(concept_ids)

        # Load graph cache if not already loaded
        if len(self.graph.nodes()) == 0:
            self._load_graph_cache()

        # Expand ego-graph: include neighbors up to max_hops
        current_level = set(concept_ids)
        for hop in range(max_hops):
            next_level = set()
            for node_id in current_level:
                # Add node to subgraph
                if node_id in self.graph:
                    nodes_to_include.add(node_id)

                    # Add neighbors
                    for neighbor in self.graph.neighbors(node_id):
                        edge_data = self.graph.get_edge_data(node_id, neighbor, {})
                        weight = edge_data.get("weight", 0.0)

                        # Only include edges above minimum weight
                        if weight >= min_weight:
                            nodes_to_include.add(neighbor)
                            next_level.add(neighbor)

                            # Add edge to ego-graph (with weight for PageRank)
                            ego_graph.add_edge(node_id, neighbor, weight=weight)

            current_level = next_level
            if not current_level:
                break

        if len(ego_graph.nodes()) == 0:
            logger.warning("GraphEngine: Ego-graph is empty, no hidden context to infer")
            return []

        # STEP 3: Calculate PageRank with edge weights (Microsoft GraphRAG style)
        # Use edge weights (derived from Phi) as weights for PageRank
        # This makes high-Phi associations more influential in the ranking
        try:
            # Build weight dictionary for PageRank
            # PageRank expects edge weights to be in a specific format
            # We'll use the 'weight' attribute from edges
            pagerank_scores = nx.pagerank(
                ego_graph,
                weight="weight",  # Use edge weights (Phi-derived) for PageRank
                alpha=0.85,  # Damping factor (standard PageRank value)
                max_iter=100
            )

            logger.info(f"GraphEngine: Calculated PageRank on ego-graph ({len(ego_graph.nodes())} nodes, {len(ego_graph.edges())} edges)")

        except Exception as e:
            logger.error(f"GraphEngine: PageRank calculation failed: {e}")
            return []

        # STEP 4: Get concept names for PageRank nodes
        # We need to map concept IDs back to names for the output
        concept_id_map = {}
        if nodes_to_include:
            try:
                result = self.client.table("concepts").select("id, name").eq(
                    "user_id", self.user_id
                ).in_("id", list(nodes_to_include)).execute()

                for row in result.data or []:
                    concept_id_map[row["id"]] = row["name"]
            except Exception as e:
                logger.error(f"GraphEngine: Failed to fetch concept names: {e}")

        # STEP 5: Filter and rank results
        # Return top nodes with highest PageRank that were NOT in original input
        hidden_contexts = []
        for node_id, pagerank_score in sorted(pagerank_scores.items(), key=lambda x: x[1], reverse=True):
            # Skip if this was in the original input
            if node_id in concept_ids:
                continue

            # Get concept name
            concept_name = concept_id_map.get(node_id, f"Unknown-{node_id[:8]}")

            # Build reasoning (Microsoft GraphRAG style)
            reasoning = f"PageRank score: {pagerank_score:.4f} (statistically central in ego-graph)"

            hidden_contexts.append(HiddenContext(
                concept_id=node_id,
                concept_name=concept_name,
                path_weight=pagerank_score,  # Use PageRank score as "weight"
                path_length=max_hops,  # Approximate path length
                reasoning=reasoning
            ))

        # Return top 3 (highest PageRank)
        top_contexts = sorted(hidden_contexts, key=lambda x: x.path_weight, reverse=True)[:3]

        logger.info(f"GraphEngine: Inferred {len(top_contexts)} hidden contexts via PageRank")
        return top_contexts

    async def get_related_concepts(
        self,
        concept_name: str,
        limit: int = 10,
        depth: int = 1
    ) -> List[Dict]:
        """
        Get directly related concepts (1-hop neighbors).

        Args:
            concept_name: Concept to find neighbors for
            limit: Maximum number of neighbors to return

        Returns:
            List of related concepts with weights
        """
        if not self.client:
            return []

        # Find concept ID
        normalized = concept_name.lower().strip()
        try:
            result = self.client.table("concepts").select("id").eq(
                "user_id", self.user_id
            ).eq("normalized_name", normalized).limit(1).execute()

            if not result.data:
                return []

            concept_id = result.data[0]["id"]

            # Get related concepts using Supabase function
            result = self.client.rpc(
                "get_related_concepts",
                {
                    "p_user_id": self.user_id,
                    "p_concept_id": concept_id,
                    "p_min_weight": 0.3,
                    "p_limit": limit
                }
            ).execute()

            return result.data or []

        except Exception as e:
            logger.error(f"GraphEngine: Failed to get related concepts: {e}")
            return []

    def get_edges_by_type(self, edge_type: str) -> List[Tuple[str, str, Dict]]:
        """
        Get all edges of a specific type from the in-memory graph.

        Args:
            edge_type: EdgeType value to filter by

        Returns:
            List of (source_id, target_id, edge_data) tuples
        """
        return [
            (u, v, d) for u, v, d in self.graph.edges(data=True)
            if d.get("edge_type", EdgeType.RELATED.value) == edge_type
        ]

    def get_causal_subgraph(self) -> "nx.DiGraph":
        """
        Extract causal subgraph (edges with type CAUSES or INFLUENCES).

        Returns:
            NetworkX DiGraph with only causal edges
        """
        causal_edges = [
            (u, v, d) for u, v, d in self.graph.edges(data=True)
            if d.get("edge_type") in (EdgeType.CAUSES.value, EdgeType.INFLUENCES.value)
        ]
        subgraph = nx.DiGraph()
        subgraph.add_edges_from(causal_edges)
        return subgraph

    def get_contradictions(self) -> List[Tuple[str, str, Dict]]:
        """Get all contradiction edges."""
        return self.get_edges_by_type(EdgeType.CONTRADICTS.value)

    def refresh_graph_cache(self):
        """Reload graph from database (call after forming new associations)."""
        self._load_graph_cache()

    # ========================================================================
    # CHRONICLE GRAPH API (Echo Chronicles Character Development)
    # ========================================================================

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
            from datetime import datetime
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
                logger.info(f"GraphEngine: Created Chronicle event {event_id} for character {character_id} ({event_type})")
                return event_id

            return None
        except Exception as e:
            logger.error(f"GraphEngine: Failed to upsert character event: {e}")
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

            # Generate summary for narrative context
            summary = self._generate_chronicle_summary(events, character_id)

            return {
                "nodes": nodes,
                "edges": edges,
                "events": events,
                "summary": summary,
                "character_id": character_id,
                "window": window
            }

        except Exception as e:
            logger.error(f"GraphEngine: Failed to get character subgraph: {e}")
            return {
                "nodes": [],
                "edges": [],
                "summary": f"Error retrieving subgraph: {e}"
            }

    def _generate_chronicle_summary(
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
            unique_scenes = list(set(scene_ids[:3]))
            if unique_scenes:
                summary_parts.append(f"Recent scenes: {', '.join(unique_scenes)}.")

        if choice_events:
            summary_parts.append(f"Made {len(choice_events)} significant choice(s) recently.")

        return " ".join(summary_parts) if summary_parts else "Character history is emerging."

