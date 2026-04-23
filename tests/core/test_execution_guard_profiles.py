"""
Tests for the profile-driven ExecutionGuard config (K6 / PR #7).

The goal is NOT to re-test every guard rule (``execution_guard.py`` is
well-covered elsewhere). The goal is to prove four things:

1. Passing no config reproduces the original hard-coded defaults exactly.
2. Passing a ``ExecutionGuardConfig`` threads profile values through to the
   live ``ExecutionGuard`` instance.
3. The multiplier survives ``reset()`` — important because the orchestrator
   resets the guard at the start of every pipeline run.
4. The Pydantic bounds reject pathological values so profile YAML typos
   cannot silently disable the guard.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from phionyx_core.orchestrator.execution_guard import ExecutionGuard
from phionyx_core.profiles.schema import ExecutionGuardConfig


BLOCK_COUNT = 46  # v3.8.0 canonical pipeline length


class TestExecutionGuardFromConfig:
    def test_default_config_matches_historical_hardcoded_values(self):
        """A ``None`` config reproduces the pre-PR#7 defaults exactly."""
        guard = ExecutionGuard.from_config(None, block_order_length=BLOCK_COUNT)

        assert guard.max_iterations == BLOCK_COUNT * 3
        assert guard.max_block_executions == 2
        assert guard.max_execution_time == 300.0
        assert guard.max_repeated_sequence == 3

    def test_custom_config_is_threaded_through(self):
        config = ExecutionGuardConfig(
            max_iterations_multiplier=5,
            max_block_executions=4,
            max_execution_time_sec=120.0,
            max_repeated_sequence=5,
        )
        guard = ExecutionGuard.from_config(config, block_order_length=BLOCK_COUNT)

        assert guard.max_iterations == BLOCK_COUNT * 5
        assert guard.max_block_executions == 4
        assert guard.max_execution_time == 120.0
        assert guard.max_repeated_sequence == 5

    def test_multiplier_is_preserved_across_reset(self):
        config = ExecutionGuardConfig(max_iterations_multiplier=7)
        guard = ExecutionGuard.from_config(config, block_order_length=BLOCK_COUNT)

        # Simulate the orchestrator reset path that nulls out max_iterations
        # and re-derives it from block_order_length.
        guard.max_iterations = None
        guard.reset(block_order_length=BLOCK_COUNT)

        assert guard.max_iterations == BLOCK_COUNT * 7


class TestExecutionGuardConfigBounds:
    @pytest.mark.parametrize(
        "field,bad_value",
        [
            ("max_iterations_multiplier", 0),
            ("max_iterations_multiplier", 11),
            ("max_block_executions", 0),
            ("max_block_executions", 11),
            ("max_execution_time_sec", 0.0),
            ("max_execution_time_sec", 3601.0),
            ("max_repeated_sequence", 1),
            ("max_repeated_sequence", 11),
        ],
    )
    def test_rejects_out_of_range_values(self, field: str, bad_value):
        with pytest.raises(ValidationError):
            ExecutionGuardConfig(**{field: bad_value})

    def test_accepts_documented_safe_values(self):
        # Values used as defaults / examples in the schema must validate.
        ExecutionGuardConfig()
        ExecutionGuardConfig(
            max_iterations_multiplier=3,
            max_block_executions=2,
            max_execution_time_sec=300.0,
            max_repeated_sequence=3,
        )
