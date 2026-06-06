"""
Pipeline Migration: v2.5.0 → v3.0.0
======================================

Migrates canonical pipeline from 24-block v2.5.0 to 32-block v3.0.0.
Non-destructive: v2.5.0 pipeline continues to work alongside v3.0.0 (AD-3).
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# New blocks introduced in v3.0.0
V3_NEW_BLOCKS = [
    "perceptual_frame_emit",
    "goal_evaluation",
    "action_intent_gate",
    "workspace_broadcast",
    "world_state_snapshot",
    "confidence_fusion",
    "arbitration_resolve",
    "learning_gate",
]

# Insertion points: {new_block: insert_after_block}
V3_INSERTION_POINTS = {
    "perceptual_frame_emit": "context_retrieval_rag",
    "goal_evaluation": "initialize_unified_state",
    "action_intent_gate": "ethics_post_response",
    "workspace_broadcast": "behavioral_drift_detection",
    "world_state_snapshot": "state_update_physics",
    "confidence_fusion": "phi_computation",
    "arbitration_resolve": "confidence_fusion",
    "learning_gate": "audit_layer",
}


def migrate_block_order(v2_blocks: List[str]) -> List[str]:
    """
    Migrate v2.5.0 block order to v3.0.0 by inserting new blocks.

    Args:
        v2_blocks: v2.5.0 canonical block order

    Returns:
        v3.0.0 canonical block order (32 blocks)
    """
    result = list(v2_blocks)

    for new_block, after_block in V3_INSERTION_POINTS.items():
        if new_block in result:
            continue  # Already present

        if after_block in result:
            idx = result.index(after_block) + 1
            result.insert(idx, new_block)
        else:
            logger.warning(
                f"Insertion point '{after_block}' not found for '{new_block}', "
                f"appending to end"
            )
            result.append(new_block)

    return result


def validate_migration(v3_blocks: List[str]) -> Dict[str, Any]:
    """
    Validate that migrated block order is correct.

    Returns:
        Validation result with success status and any issues
    """
    issues = []

    # Check all v3 blocks present
    for block in V3_NEW_BLOCKS:
        if block not in v3_blocks:
            issues.append(f"Missing new block: {block}")

    # Check ordering constraints
    ordering_constraints = [
        ("perceptual_frame_emit", "create_scenario_frame"),
        ("goal_evaluation", "ukf_predict"),
        ("action_intent_gate", "behavioral_drift_detection"),
        ("workspace_broadcast", "unified_state_update_esc"),
        ("world_state_snapshot", "response_build"),
        ("confidence_fusion", "entropy_computation"),
        ("arbitration_resolve", "audit_layer"),
        ("learning_gate", "telemetry_publish"),
    ]

    for before, after in ordering_constraints:
        if before in v3_blocks and after in v3_blocks:
            if v3_blocks.index(before) >= v3_blocks.index(after):
                issues.append(f"Ordering violation: {before} must come before {after}")

    return {
        "valid": len(issues) == 0,
        "block_count": len(v3_blocks),
        "expected_count": 32,
        "issues": issues,
    }


def get_migration_diff(v2_blocks: List[str], v3_blocks: List[str]) -> Dict[str, Any]:
    """Get diff between v2.5.0 and v3.0.0 block orders."""
    added = [b for b in v3_blocks if b not in v2_blocks]
    removed = [b for b in v2_blocks if b not in v3_blocks]
    preserved = [b for b in v2_blocks if b in v3_blocks]

    return {
        "added": added,
        "removed": removed,
        "preserved": preserved,
        "added_count": len(added),
        "removed_count": len(removed),
        "preserved_count": len(preserved),
    }
