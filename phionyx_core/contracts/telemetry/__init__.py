"""
Telemetry Contract Package

Provides access to canonical telemetry blocks (46-block pipeline, CONTRACT v3.8.0).
Supports backward compatibility with v3.7.0, v3.6.0, v3.5.0, v3.0.0, v2.5.0, and v2.4.0.
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Contract version management
_CONTRACT_V2_4_0_PATH = Path(__file__).parent / "archive" / "canonical_blocks_v2_4_0.json"
_CONTRACT_V2_5_0_PATH = Path(__file__).parent / "canonical_blocks_v2_5_0.json"
_CONTRACT_V3_0_0_PATH = Path(__file__).parent / "canonical_blocks_v3_0_0.json"
_CONTRACT_V3_5_0_PATH = Path(__file__).parent / "canonical_blocks_v3_5_0.json"
_CONTRACT_V3_6_0_PATH = Path(__file__).parent / "canonical_blocks_v3_6_0.json"
_CONTRACT_V3_7_0_PATH = Path(__file__).parent / "canonical_blocks_v3_7_0.json"
_CONTRACT_V3_8_0_PATH = Path(__file__).parent / "canonical_blocks_v3_8_0.json"
_CURRENT_VERSION = "3.8.0"
_FALLBACK_VERSION = "2.5.0"


def _load_contract(version: Optional[str] = None) -> Dict[str, Any]:
    """Load telemetry contract for specified version."""
    # v3.8.0 support (state-driven response revision — 46 blocks)
    if version == "3.8.0" or version is None:
        if _CONTRACT_V3_8_0_PATH.exists():
            with open(_CONTRACT_V3_8_0_PATH, 'r') as f:
                return json.load(f)
        if version == "3.8.0":
            raise FileNotFoundError("v3.8.0 contract file not found")
    # v3.7.0 support (CEP reactivation pipeline — 45 blocks)
    if version == "3.7.0" or version is None:
        if _CONTRACT_V3_7_0_PATH.exists():
            with open(_CONTRACT_V3_7_0_PATH, 'r') as f:
                return json.load(f)
        if version == "3.7.0":
            raise FileNotFoundError("v3.7.0 contract file not found")
    # v3.6.0 support (feedback loop pipeline — 44 blocks)
    if version == "3.6.0" or version is None:
        if _CONTRACT_V3_6_0_PATH.exists():
            with open(_CONTRACT_V3_6_0_PATH, 'r') as f:
                return json.load(f)
        if version == "3.6.0":
            raise FileNotFoundError("v3.6.0 contract file not found")
    # v3.5.0 support (full AGI pipeline — 43 blocks)
    if version == "3.5.0" or version is None:
        if _CONTRACT_V3_5_0_PATH.exists():
            with open(_CONTRACT_V3_5_0_PATH, 'r') as f:
                return json.load(f)
        # Fall through to v3.0.0 if v3.5.0 not found and no explicit version requested
        if version == "3.5.0":
            raise FileNotFoundError("v3.5.0 contract file not found")
    # v3.0.0 support (AD-3: pipeline version coexistence)
    if version == "3.0.0" or version is None:
        if _CONTRACT_V3_0_0_PATH.exists():
            with open(_CONTRACT_V3_0_0_PATH, 'r') as f:
                return json.load(f)
        if version == "3.0.0":
            raise FileNotFoundError("v3.0.0 contract file not found")
    if version == "2.5.0" or version is None:
        if _CONTRACT_V2_5_0_PATH.exists():
            with open(_CONTRACT_V2_5_0_PATH, 'r') as f:
                return json.load(f)
    # Fallback to v2.4.0
    if _CONTRACT_V2_4_0_PATH.exists():
        with open(_CONTRACT_V2_4_0_PATH, 'r') as f:
            return json.load(f)
    raise FileNotFoundError("Telemetry contract file not found")


def get_canonical_blocks(version: Optional[str] = None) -> List[str]:
    """
    Returns canonical block order from JSON contract (46 blocks, CONTRACT v3.8.0).

    This is the single source of truth for telemetry block order.
    Supports versions: 3.8.0, 3.7.0, 3.6.0, 3.5.0, 3.0.0, 2.5.0, 2.4.0.

    Args:
        version: Contract version to load. Defaults to current version (3.8.0).

    Returns:
        List of block IDs in canonical order.
    """
    contract = _load_contract(version)
    return contract['canonical_block_order']


def get_canonical_block_order(version: Optional[str] = None) -> List[str]:
    """
    Get canonical block order (alias for get_canonical_blocks).

    Args:
        version: Optional version string (defaults to current version)

    Returns:
        List of canonical block IDs in order
    """
    return get_canonical_blocks(version)


def get_middleware_blocks(version: Optional[str] = None) -> List[str]:
    """
    Returns middleware blocks (v2.5.0+ only).

    Args:
        version: Contract version to load. Defaults to current version.

    Returns:
        List of middleware block IDs.
    """
    contract = _load_contract(version)
    return contract.get('middleware_blocks', [])


def get_block_mapping(version: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns block mapping for migration (v2.5.0+ only).

    Args:
        version: Contract version to load. Defaults to current version.

    Returns:
        Block mapping dictionary.
    """
    contract = _load_contract(version)
    return contract.get('block_mapping', {})


def get_required_event_types(version: Optional[str] = None) -> List[str]:
    """Returns required event types."""
    contract = _load_contract(version)
    return contract['required_event_types']


def get_contract_version() -> str:
    """Returns current contract version."""
    try:
        contract = _load_contract()
        return contract.get('contract_version', _CURRENT_VERSION)
    except FileNotFoundError:
        return _FALLBACK_VERSION


def migrate_block_id(old_block_id: str, from_version: str = "2.4.0", to_version: str = "2.5.0") -> str:
    """
    Migrate block ID from old version to new version.

    Args:
        old_block_id: Block ID from old version.
        from_version: Source version.
        to_version: Target version.

    Returns:
        New block ID or original if no mapping exists.
    """
    if from_version == "2.4.0" and to_version == "2.5.0":
        contract = _load_contract("2.5.0")
        mapping = contract.get('block_mapping', {}).get('v2.4.0_to_v2.5.0', {})
        return mapping.get(old_block_id, old_block_id)
    if from_version == "2.5.0" and to_version == "3.0.0":
        # v3.0.0 is additive — no block renames, only insertions
        return old_block_id
    if from_version == "3.0.0" and to_version == "3.5.0":
        # v3.5.0 is additive — no block renames, only insertions
        return old_block_id
    if from_version == "3.5.0" and to_version == "3.6.0":
        # v3.6.0 is additive — no block renames, only insertions (outcome_feedback)
        return old_block_id
    if from_version == "3.6.0" and to_version == "3.7.0":
        # v3.7.0 is additive — no block renames, only insertions (cep_evaluation)
        return old_block_id
    if from_version == "3.7.0" and to_version == "3.8.0":
        # v3.8.0 is additive+reorder — no block renames
        return old_block_id
    return old_block_id


# Export for convenience
CANONICAL_BLOCK_ORDER = get_canonical_blocks()
REQUIRED_EVENT_TYPES = get_required_event_types()
CONTRACT_VERSION = get_contract_version()

__all__ = [
    'get_canonical_blocks',
    'get_canonical_block_order',
    'get_middleware_blocks',
    'get_block_mapping',
    'get_required_event_types',
    'get_contract_version',
    'migrate_block_id',
    'CANONICAL_BLOCK_ORDER',
    'REQUIRED_EVENT_TYPES',
    'CONTRACT_VERSION',
]
