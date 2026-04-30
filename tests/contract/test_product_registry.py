"""
Contract tests for the ProductRegistry (K3 / PR #9 follow-up).

The goal is to catch the three classes of drift that silently break
the registry in practice:

1. A ``product_config.yaml`` uses a value the ``DevelopmentStage`` enum
   (or its sibling validator in ``config_loader.py``) rejects. Before
   this test landed, nine of sixteen products silently failed to load
   with no CI signal.
2. The enum in ``product_manager.py`` and the ``valid_stages`` list in
   ``config_loader.py`` drift apart — they are duplicated strings and
   the duplication cannot be removed safely in one commit because too
   many call sites import from both.
3. Every known product directory has a ``commercial_status`` assigned
   by ``scripts/active/apply_commercial_tiers.py``; a product that
   slips in with ``unclassified`` breaks the flagship-first sort in
   the Founder Console and Product Dashboard APIs.

These are cheap assertions; the whole suite runs in well under a
second.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

# `phionyx_products` is monorepo-only — it ships in the founder's
# internal repo but not in this public SDK release. Skip the whole
# module on a clean clone so the rest of `tests/contract` can run.
pytest.importorskip(
    "phionyx_products",
    reason="phionyx_products is monorepo-only; this contract test skips on the public SDK release",
)

from phionyx_products.config_loader import ProductConfigLoader  # noqa: E402
from phionyx_products.product_manager import DevelopmentStage  # noqa: E402
from phionyx_products.product_registry import ProductRegistry  # noqa: E402


PRODUCTS_DIR = Path(__file__).resolve().parents[2] / "phionyx_products" / "products"


def _product_dirs() -> list[Path]:
    return sorted(
        p for p in PRODUCTS_DIR.iterdir()
        if p.is_dir() and (p / "product_config.yaml").is_file()
    )


class TestProductRegistryLoads:
    def test_registry_loads_every_product_directory(self):
        """Every directory under phionyx_products/products/ with a
        product_config.yaml must load into ProductRegistry.products.

        Regression: 2026-04-17 validator rejected 9/16 configs because
        the DevelopmentStage enum was 4 values but configs used 6.
        """
        product_dirs = _product_dirs()
        assert len(product_dirs) >= 16, (
            f"expected ≥16 product directories, found {len(product_dirs)}"
        )

        registry = ProductRegistry()
        loaded_ids = set(registry.products.keys())
        expected_ids = {p.name for p in product_dirs}

        missing = expected_ids - loaded_ids
        assert not missing, (
            f"{len(missing)} product(s) failed to load into the registry: "
            f"{sorted(missing)}. Check phionyx_products/config_loader.py"
            f"::valid_stages against DevelopmentStage in product_manager.py."
        )


class TestDevelopmentStageConsistency:
    """The enum in ``product_manager.py`` and the validator list in
    ``config_loader.py`` are duplicated. Until the duplication is
    removed (a refactor that requires founder review because it
    touches the product public API), this test is the fence."""

    def test_enum_and_validator_list_agree(self):
        enum_values = {stage.value for stage in DevelopmentStage}
        loader = ProductConfigLoader(products_dir=PRODUCTS_DIR)
        # Exercise the validator with each enum value — if any enum
        # value is rejected, the duplication has drifted.
        for value in enum_values:
            minimal_config = {
                "product": {"id": "test", "name": "x", "version": "0.0.1", "tier": 1, "priority": 1},
                "status": {
                    "development_stage": value,
                    "completion_percentage": 0.0,
                    "last_updated": "2026-04-17",
                },
                "roadmap": {},
            }
            # Should not raise.
            loader._validate_config(minimal_config, "test")

    def test_every_config_uses_an_enum_value(self):
        enum_values = {stage.value for stage in DevelopmentStage}
        for product_dir in _product_dirs():
            cfg_path = product_dir / "product_config.yaml"
            with cfg_path.open(encoding="utf-8") as handle:
                cfg = yaml.safe_load(handle)
            stage = cfg["status"]["development_stage"]
            assert stage in enum_values, (
                f"{product_dir.name}: development_stage '{stage}' is not "
                f"in DevelopmentStage enum ({sorted(enum_values)})"
            )


class TestCommercialStatusCoverage:
    """Every loaded product must have a non-empty commercial_status.
    ``unclassified`` is the default when apply_commercial_tiers.py has
    not run yet; shipping it is a planning bug, not a runtime bug, so
    this test fails loudly in CI."""

    def test_no_product_is_unclassified(self):
        registry = ProductRegistry()
        unclassified = sorted(
            pid for pid, meta in registry.products.items()
            if meta.commercial_status == "unclassified" or not meta.commercial_status
        )
        assert not unclassified, (
            f"{len(unclassified)} product(s) have commercial_status='unclassified' "
            f"or empty: {unclassified}. Run "
            f"`python scripts/active/apply_commercial_tiers.py` or add the "
            f"product to the COMMERCIAL_TIER dict in that script."
        )

    def test_flagship_count_matches_matrix(self):
        """The commercial-tier matrix in
        phionyx_products/COMMERCIAL_TIER_MATRIX.md claims three
        flagship products. Guard against silent demotion."""
        registry = ProductRegistry()
        flagships = registry.get_flagship_products()
        assert len(flagships) == 3, (
            f"expected exactly 3 flagship products (core_sdk, "
            f"ai_assurance_kit, governance_node per COMMERCIAL_TIER_MATRIX.md); "
            f"found {len(flagships)}: {sorted(p.product_id for p in flagships)}"
        )
