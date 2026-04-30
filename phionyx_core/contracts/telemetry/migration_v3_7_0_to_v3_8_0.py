"""
Migration v3.7.0 → v3.8.0 — State-Driven Response Revision
============================================================

Purpose:
    v3.8.0 closes the in-turn state → response feedback loop surfaced in
    ``docs/publications/patents/ukipo/BLOCK_CLAIM_ALIGNMENT_ANALYSIS.md``.

Changes (contract-level, no semantics removed):

    1. Reorder four state-computation blocks to execute BEFORE ``response_build``:
         phi_computation        (was 38, now 37)
         entropy_computation    (was 39, now 38)
         confidence_fusion      (was 40, now 39)
         arbitration_resolve    (was 41, now 40)

    2. Insert new block ``response_revision_gate`` at position 41, immediately
       before ``response_build``. The gate consumes final-turn state metrics
       and emits a deterministic ``revision_directive`` (pass / damp / rewrite
       / regenerate / reject) used by ``response_build``.

    3. ``response_build`` position shifts from 37 → 42.
    4. Total block count: 45 → 46.

Compatibility:
    * Additive at the block level (no block deleted, no block renamed).
    * The four reordered blocks keep their block IDs and implementations.
    * Runtimes on v3.7.0 continue to work (contract loader supports both).
    * Emits a new required event type: ``response_revision``.

Rationale (patent-claim alignment):
    - Echoism Axiom 1: symbolic layer must be able to override neural output
      within the same turn; v3.7.0 ordering created a 1-turn lag because the
      final state computations ran AFTER response_build.
    - SF1 Claim 15: LLM output as sensor measurement, evaluated deterministically.
    - SF2 Claim 1 / Claim 11: state-level governance before output generation.
    - SF1 Claim 4: response_build remains the terminal response block; all
      state updates precede it.

Founder approval: granted in session_01RW4rjACATaqAHoRNxpCjjg.
"""


SOURCE_VERSION = "3.7.0"
TARGET_VERSION = "3.8.0"

# Block IDs reordered (moved up) — position changes are data-only.
REORDERED_BLOCKS: list[str] = [
    "phi_computation",
    "entropy_computation",
    "confidence_fusion",
    "arbitration_resolve",
]

# Newly inserted block IDs.
NEW_BLOCKS: list[str] = [
    "response_revision_gate",
]

# Newly required event types.
NEW_EVENT_TYPES: list[str] = [
    "response_revision",
]


def migrate_block_id(old_block_id: str) -> str:
    """
    Migrate a block ID from v3.7.0 to v3.8.0.

    v3.8.0 is additive+reorder only: no block is renamed, so this returns
    the input unchanged. The function is provided for symmetry with prior
    migration modules.
    """
    return old_block_id


def is_reordered(block_id: str) -> bool:
    """Return True if the given block id changed position between v3.7.0 and v3.8.0."""
    return block_id in REORDERED_BLOCKS


def is_new(block_id: str) -> bool:
    """Return True if the given block id is new in v3.8.0."""
    return block_id in NEW_BLOCKS


__all__ = [
    "SOURCE_VERSION",
    "TARGET_VERSION",
    "REORDERED_BLOCKS",
    "NEW_BLOCKS",
    "NEW_EVENT_TYPES",
    "migrate_block_id",
    "is_reordered",
    "is_new",
]
