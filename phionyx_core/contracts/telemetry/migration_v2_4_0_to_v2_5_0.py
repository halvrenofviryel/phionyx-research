"""
Telemetry Contract Migration Script: v2.4.0 -> v2.5.0

This script helps migrate telemetry data and dashboard configurations
from v2.4.0 to v2.5.0 contract.

Usage:
    python -m phionyx_core.contracts.telemetry.migration_v2_4_0_to_v2_5_0
"""
import json
from pathlib import Path
from typing import Any

from phionyx_core.contracts.telemetry import (
    get_block_mapping,
    get_canonical_blocks,
    get_middleware_blocks,
    migrate_block_id,
)


def validate_migration() -> dict[str, Any]:
    """
    Validate that migration mapping is correct.

    Returns:
        Validation report with errors and warnings.
    """
    errors = []
    warnings = []

    # Load both contracts
    contract_v2_4_0_path = Path(__file__).parent / "archive" / "canonical_blocks_v2_4_0.json"
    contract_v2_5_0_path = Path(__file__).parent / "canonical_blocks_v2_5_0.json"

    with open(contract_v2_4_0_path) as f:
        contract_v2_4_0 = json.load(f)

    with open(contract_v2_5_0_path) as f:
        contract_v2_5_0 = json.load(f)

    # Check that all mapped blocks exist in v2.4.0
    mapping = contract_v2_5_0.get('block_mapping', {}).get('v2.4.0_to_v2.5.0', {})
    v2_4_0_blocks = set(contract_v2_4_0['canonical_block_order'])

    for old_block in mapping.keys():
        if old_block not in v2_4_0_blocks:
            errors.append(f"Mapping references non-existent block: {old_block}")

    # Check that new blocks are actually new
    new_blocks = set(contract_v2_5_0.get('block_mapping', {}).get('new_blocks', []))
    v2_5_0_blocks = set(contract_v2_5_0['canonical_block_order'])

    for new_block in new_blocks:
        if new_block not in v2_5_0_blocks:
            errors.append(f"New block not in canonical order: {new_block}")

    # Check middleware blocks
    middleware_blocks = set(contract_v2_5_0.get('middleware_blocks', []))
    if middleware_blocks & v2_5_0_blocks:
        warnings.append("Middleware blocks should not be in canonical order")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def migrate_telemetry_data(telemetry_data: dict[str, Any]) -> dict[str, Any]:
    """
    Migrate telemetry data from v2.4.0 to v2.5.0 format.

    Args:
        telemetry_data: Telemetry data in v2.4.0 format.

    Returns:
        Migrated telemetry data in v2.5.0 format.
    """
    migrated = telemetry_data.copy()

    # Update contract version
    migrated['telemetry_contract_version'] = '2.5.0'

    # Migrate block IDs in canonical_blocks
    if 'canonical_blocks' in migrated:
        new_canonical_blocks = {}
        for old_block_id, block_data in migrated['canonical_blocks'].items():
            new_block_id = migrate_block_id(old_block_id)
            if new_block_id.startswith('middleware.'):
                # Move to middleware_blocks
                if 'middleware_blocks' not in migrated:
                    migrated['middleware_blocks'] = {}
                middleware_key = new_block_id.replace('middleware.', '')
                migrated['middleware_blocks'][middleware_key] = block_data
            else:
                new_canonical_blocks[new_block_id] = block_data

        migrated['canonical_blocks'] = new_canonical_blocks

    return migrated


def generate_migration_report() -> str:
    """
    Generate a human-readable migration report.

    Returns:
        Migration report as string.
    """
    v2_4_0_blocks = get_canonical_blocks("2.4.0")
    v2_5_0_blocks = get_canonical_blocks("2.5.0")
    middleware_blocks = get_middleware_blocks("2.5.0")
    mapping = get_block_mapping("2.5.0")

    report = []
    report.append("=" * 80)
    report.append("Telemetry Contract Migration Report: v2.4.0 -> v2.5.0")
    report.append("=" * 80)
    report.append("")

    report.append(f"v2.4.0 Blocks: {len(v2_4_0_blocks)}")
    report.append(f"v2.5.0 Blocks: {len(v2_5_0_blocks)}")
    report.append(f"Middleware Blocks: {len(middleware_blocks)}")
    report.append("")

    report.append("Block Mappings:")
    report.append("-" * 80)
    v2_4_to_v2_5 = mapping.get('v2.4.0_to_v2.5.0', {})
    for old_block, new_block in v2_4_to_v2_5.items():
        report.append(f"  {old_block} -> {new_block}")
    report.append("")

    report.append("New Blocks:")
    report.append("-" * 80)
    for new_block in mapping.get('new_blocks', []):
        report.append(f"  + {new_block}")
    report.append("")

    report.append("Removed Blocks (from canonical order):")
    report.append("-" * 80)
    for removed_block in mapping.get('removed_blocks', []):
        report.append(f"  - {removed_block}")
    report.append("")

    report.append("Middleware Blocks:")
    report.append("-" * 80)
    for middleware_block in middleware_blocks:
        report.append(f"  {middleware_block}")
    report.append("")

    # Validation
    validation = validate_migration()
    report.append("Validation:")
    report.append("-" * 80)
    if validation['valid']:
        report.append("  ✅ Migration mapping is valid")
    else:
        report.append("  ❌ Migration mapping has errors:")
        for error in validation['errors']:
            report.append(f"    - {error}")

    if validation['warnings']:
        report.append("  ⚠️  Warnings:")
        for warning in validation['warnings']:
            report.append(f"    - {warning}")

    report.append("")
    report.append("=" * 80)

    return "\n".join(report)


if __name__ == "__main__":
    # Generate and print migration report
    report = generate_migration_report()
    print(report)

    # Validate migration
    validation = validate_migration()
    if not validation['valid']:
        print("\n❌ Migration validation failed!")
        exit(1)
    else:
        print("\n✅ Migration validation passed!")

