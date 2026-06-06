"""
Baseline Store Module
Persistent baseline storage and retrieval for drift detection.
"""

from typing import Dict, List, Optional, Any, Protocol
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class DatabaseProtocol(Protocol):
    """Protocol for database operations."""

    async def insert(self, table: str, data: Dict[str, Any]) -> Optional[str]:
        """Insert a record. Returns record ID if successful."""
        ...

    async def query(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Query records. Returns list of records."""
        ...

    async def update(
        self,
        table: str,
        record_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update a record. Returns True if successful."""
        ...


@dataclass
class BaselineSnapshot:
    """Baseline snapshot for drift comparison."""
    baseline_id: str
    version: str
    session_id: Optional[str]
    agent_id: Optional[str]
    created_at: datetime
    reference_outputs: List[str]  # Sample outputs
    reference_metrics: Dict[str, float]  # phi, entropy, valence, arousal
    physics_state: Dict[str, float]  # Full state snapshot
    integrity_hash: str  # SHA256 hash
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        # Convert datetime to ISO string
        data['created_at'] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaselineSnapshot':
        """Create from dictionary."""
        # Convert ISO string to datetime
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


class BaselineStore:
    """
    Persistent baseline storage and retrieval.

    Storage Strategy:
    - Database table: `baseline_snapshots`
    - Columns: baseline_id, version, session_id, agent_id, created_at,
               reference_outputs (JSONB), reference_metrics (JSONB),
               physics_state (JSONB), integrity_hash, metadata (JSONB)
    - Indexes: (version, session_id), (agent_id, created_at)

    For now, uses in-memory storage. Database integration via DatabaseProtocol.
    """

    def __init__(self, database: Optional[DatabaseProtocol] = None):
        """
        Initialize baseline store.

        Args:
            database: Optional database protocol implementation.
                      If None, uses in-memory storage.
        """
        self.db = database
        # In-memory fallback storage
        self._memory_store: Dict[str, BaselineSnapshot] = {}

    def _generate_integrity_hash(
        self,
        version: str,
        reference_outputs: List[str],
        reference_metrics: Dict[str, float],
        physics_state: Dict[str, float]
    ) -> str:
        """Generate SHA256 integrity hash for baseline data."""
        baseline_data = {
            "version": version,
            "reference_outputs": sorted(reference_outputs),  # Sort for consistency
            "reference_metrics": dict(sorted(reference_metrics.items())),
            "physics_state": dict(sorted(physics_state.items()))
        }
        data_str = json.dumps(baseline_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    async def create_baseline(
        self,
        version: str,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        reference_outputs: List[str] = None,
        reference_metrics: Dict[str, float] = None,
        physics_state: Dict[str, float] = None,
        metadata: Dict[str, Any] = None
    ) -> BaselineSnapshot:
        """
        Create and store baseline snapshot.

        Args:
            version: Baseline version (e.g., "v2.5.0")
            session_id: Optional session ID
            agent_id: Optional agent ID
            reference_outputs: Sample outputs for semantic comparison
            reference_metrics: Reference physics metrics (phi, entropy, etc.)
            physics_state: Full physics state snapshot
            metadata: Additional metadata

        Returns:
            BaselineSnapshot instance
        """
        if reference_outputs is None:
            reference_outputs = []
        if reference_metrics is None:
            reference_metrics = {}
        if physics_state is None:
            physics_state = {}
        if metadata is None:
            metadata = {}

        # Generate integrity hash
        integrity_hash = self._generate_integrity_hash(
            version, reference_outputs, reference_metrics, physics_state
        )

        # Generate baseline ID
        timestamp = datetime.now().isoformat()
        baseline_id = f"baseline_{timestamp}_{hashlib.sha256(integrity_hash.encode()).hexdigest()[:8]}"

        # Create snapshot
        snapshot = BaselineSnapshot(
            baseline_id=baseline_id,
            version=version,
            session_id=session_id,
            agent_id=agent_id,
            created_at=datetime.now(),
            reference_outputs=reference_outputs,
            reference_metrics=reference_metrics,
            physics_state=physics_state,
            integrity_hash=integrity_hash,
            metadata=metadata
        )

        # Store in database or memory
        if self.db:
            try:
                await self.db.insert("baseline_snapshots", snapshot.to_dict())
            except Exception as e:
                logger.warning(f"Database storage failed, using memory: {e}")
                self._memory_store[baseline_id] = snapshot
        else:
            # In-memory storage
            self._memory_store[baseline_id] = snapshot

        logger.info(f"Created baseline: {baseline_id} (version={version})")
        return snapshot

    async def get_baseline(
        self,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        version: Optional[str] = None
    ) -> Optional[BaselineSnapshot]:
        """
        Retrieve baseline snapshot by session/agent/version.

        Args:
            session_id: Session ID filter
            agent_id: Agent ID filter
            version: Version filter

        Returns:
            BaselineSnapshot if found, None otherwise
        """
        # Build filters
        filters = {}
        if session_id:
            filters['session_id'] = session_id
        if agent_id:
            filters['agent_id'] = agent_id
        if version:
            filters['version'] = version

        # Query database or memory
        if self.db:
            try:
                results = await self.db.query("baseline_snapshots", filters, limit=1)
                if results:
                    snapshot = BaselineSnapshot.from_dict(results[0])
                    # Validate integrity
                    if self._validate_integrity(snapshot):
                        return snapshot
                    else:
                        logger.error("Baseline integrity validation failed")
                        return None
            except Exception as e:
                logger.warning(f"Database query failed, trying memory: {e}")

        # Fallback to memory
        for snapshot in self._memory_store.values():
            if session_id and snapshot.session_id != session_id:
                continue
            if agent_id and snapshot.agent_id != agent_id:
                continue
            if version and snapshot.version != version:
                continue
            if self._validate_integrity(snapshot):
                return snapshot

        return None

    def _validate_integrity(self, snapshot: BaselineSnapshot) -> bool:
        """Validate baseline integrity using hash."""
        expected_hash = self._generate_integrity_hash(
            snapshot.version,
            snapshot.reference_outputs,
            snapshot.reference_metrics,
            snapshot.physics_state
        )
        return snapshot.integrity_hash == expected_hash

    async def compare_with_baseline(
        self,
        current_output: str,
        current_metrics: Dict[str, float],
        baseline: BaselineSnapshot,
        vector_store: Optional[Any] = None  # VectorStore type
    ) -> Dict[str, Any]:
        """
        Compare current state with baseline.

        Args:
            current_output: Current output text
            current_metrics: Current physics metrics
            baseline: Baseline snapshot to compare against
            vector_store: Optional vector store for semantic similarity

        Returns:
            Comparison results with semantic_similarity, physics_drift, drift_score
        """
        # 1. Semantic similarity
        semantic_similarity = 1.0  # Default: no drift
        if baseline.reference_outputs:
            try:
                similarities = []
                for ref_output in baseline.reference_outputs:
                    if vector_store and hasattr(vector_store, 'compute_similarity'):
                        sim = await vector_store.compute_similarity(
                            current_output, ref_output
                        )
                        similarities.append(sim)
                    else:
                        # Fallback: simple text similarity
                        similarities.append(self._simple_text_similarity(
                            current_output, ref_output
                        ))
                semantic_similarity = max(similarities) if similarities else 1.0
            except Exception as e:
                logger.warning(f"Semantic similarity computation failed: {e}")

        # 2. Physics metric drift
        physics_drift = self._compute_physics_drift(
            current_metrics, baseline.reference_metrics
        )

        # 3. Overall drift score
        drift_score = self._compute_drift_score(semantic_similarity, physics_drift)

        return {
            "semantic_similarity": semantic_similarity,
            "physics_drift": physics_drift,
            "drift_score": drift_score
        }

    def _compute_physics_drift(
        self,
        current_metrics: Dict[str, float],
        reference_metrics: Dict[str, float]
    ) -> Dict[str, float]:
        """Compute physics metric drift."""
        drift = {}
        for key in reference_metrics:
            if key in current_metrics:
                ref_value = reference_metrics[key]
                curr_value = current_metrics[key]
                # Compute relative drift
                if ref_value != 0:
                    drift[key] = abs(curr_value - ref_value) / abs(ref_value)
                else:
                    drift[key] = abs(curr_value) if curr_value != 0 else 0.0
            else:
                drift[key] = 1.0  # Missing metric = 100% drift
        return drift

    def _compute_drift_score(
        self,
        semantic_similarity: float,
        physics_drift: Dict[str, float]
    ) -> float:
        """
        Compute overall drift score (0.0 = no drift, 1.0 = maximum drift).

        Formula:
        - Semantic drift = 1.0 - semantic_similarity
        - Physics drift = average of all metric drifts
        - Overall = weighted average (50% semantic, 50% physics)
        """
        semantic_drift = 1.0 - semantic_similarity

        if physics_drift:
            physics_drift_avg = sum(physics_drift.values()) / len(physics_drift)
        else:
            physics_drift_avg = 0.0

        # Weighted average
        overall_drift = (semantic_drift * 0.5) + (physics_drift_avg * 0.5)

        # Clamp to [0.0, 1.0]
        return max(0.0, min(1.0, overall_drift))

    def _simple_text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity fallback (Jaccard similarity)."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        return intersection / union if union > 0 else 0.0

