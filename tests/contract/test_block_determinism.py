"""Contract test: every concrete ``PipelineBlock`` declares a valid
``determinism`` class attribute.

This is the inventory-level test. A future PR will add behavioural
verification (100-run hash equality for ``strict`` blocks); for now we only
guarantee the taxonomy is complete and that ``DETERMINISM_MATRIX.md`` is kept
in sync with the code.

Related:
- Plan: ``docs/PHIONYX_KOD_UYGULAMA_PLANI_2026_04_16.md`` PR #2 (K7)
- Base class: ``phionyx_core/pipeline/base.py::PipelineBlock.determinism``
- Matrix doc: ``docs/arxiv/DETERMINISM_MATRIX.md``
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
import subprocess
import sys
from pathlib import Path
from typing import get_args

import pytest

from phionyx_core.pipeline import blocks as blocks_pkg
from phionyx_core.pipeline.base import DeterminismClass, PipelineBlock

VALID_CLASSES = set(get_args(DeterminismClass))
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _discover_block_classes() -> list[type[PipelineBlock]]:
    out: dict[str, type[PipelineBlock]] = {}
    for mod_info in pkgutil.iter_modules(blocks_pkg.__path__):
        if mod_info.name.startswith("_"):
            continue
        name = f"{blocks_pkg.__name__}.{mod_info.name}"
        module = importlib.import_module(name)
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, PipelineBlock)
                and obj is not PipelineBlock
                and obj.__module__ == name
                and not inspect.isabstract(obj)
            ):
                out.setdefault(obj.__name__, obj)
    return sorted(out.values(), key=lambda c: c.__name__)


BLOCK_CLASSES = _discover_block_classes()


def test_blocks_discovered():
    """At least 45 concrete blocks must be discoverable (v3.7.0 minimum)."""
    assert len(BLOCK_CLASSES) >= 45, (
        f"only {len(BLOCK_CLASSES)} concrete PipelineBlock subclasses found; "
        "expected ≥ 45 for the canonical v3.7.0 pipeline"
    )


@pytest.mark.parametrize("block_cls", BLOCK_CLASSES, ids=lambda c: c.__name__)
def test_block_declares_valid_determinism(block_cls: type[PipelineBlock]):
    """Every concrete block must declare a determinism class in the allowed set."""
    det = getattr(block_cls, "determinism", None)
    assert det in VALID_CLASSES, (
        f"{block_cls.__name__} declares determinism={det!r}, "
        f"must be one of {sorted(VALID_CLASSES)}"
    )


def test_default_is_strict():
    """PipelineBlock base class default must remain 'strict' — subclasses
    override only when they genuinely consume external measurements."""
    assert PipelineBlock.determinism == "strict"


def test_matrix_doc_in_sync():
    """Running ``generate_determinism_matrix.py --check`` must succeed,
    proving the committed matrix doc matches the current code."""
    script = REPO_ROOT / "scripts" / "active" / "generate_determinism_matrix.py"
    if not script.exists():
        pytest.skip(
            "generate_determinism_matrix.py is monorepo-only and not "
            "shipped on the public SDK release. The doc is regenerated "
            "in the monorepo and committed manually here."
        )
    result = subprocess.run(
        [sys.executable, str(script), "--check"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        "DETERMINISM_MATRIX.md is out of date. "
        "Regenerate with: python scripts/active/generate_determinism_matrix.py\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
