"""
Pytest configuration for Phionyx tests.
"""

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "level0: L0 proof tests (hard gates)"
    )
    config.addinivalue_line(
        "markers", "level1: L1 proof tests (determinism, trace integrity)"
    )


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on directory."""
    for item in items:
        # Auto-mark based on test file location
        if "test_contracts" in str(item.fspath):
            if "test_contracts_load" in str(item.fspath) or                "test_envelope_validation" in str(item.fspath) or                "test_telemetry_canonical_order" in str(item.fspath):
                item.add_marker(pytest.mark.level0)
        elif "test_kernel" in str(item.fspath):
            if "test_determinism" in str(item.fspath) or                "test_trace_integrity" in str(item.fspath):
                item.add_marker(pytest.mark.level1)
