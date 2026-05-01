"""
ErrorPayload — v4 Schema §3.13
=================================

Extends BlockResult with severity enum, recovery actions,
and structured error reporting.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorSeverity(str, Enum):
    """Error severity classification."""
    DEBUG = "debug"         # Diagnostic only
    INFO = "info"           # Informational
    WARNING = "warning"     # Non-critical issue
    ERROR = "error"         # Operation failed
    CRITICAL = "critical"   # System stability affected
    FATAL = "fatal"         # System must stop


class RecoveryAction(str, Enum):
    """Recommended recovery action."""
    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    ESCALATE = "escalate"
    SHUTDOWN = "shutdown"
    NONE = "none"


class ErrorPayload(BaseModel):
    """
    v4 ErrorPayload schema.

    Provides structured error reporting that can be optionally
    attached to BlockResult for richer error handling.
    """
    error_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique error identifier"
    )
    severity: ErrorSeverity = Field(
        ...,
        description="Error severity level"
    )
    error_code: str = Field(
        default="UNKNOWN",
        description="Machine-readable error code"
    )
    message: str = Field(
        ...,
        description="Human-readable error message"
    )

    # Recovery
    recovery_action: RecoveryAction = Field(
        default=RecoveryAction.NONE,
        description="Recommended recovery action"
    )
    recovery_details: str | None = Field(
        None,
        description="Detailed recovery instructions"
    )
    retryable: bool = Field(
        default=False,
        description="Whether the operation can be retried"
    )
    retry_after_ms: int | None = Field(
        None, ge=0,
        description="Suggested retry delay in milliseconds"
    )

    # Context
    source_module: str = Field(
        default="unknown",
        description="Module where error originated"
    )
    source_block_id: str | None = Field(
        None,
        description="Pipeline block ID if error is from pipeline"
    )
    stack_trace: str | None = Field(
        None,
        description="Stack trace (debug/staging only, never in production)"
    )

    # Impact
    affected_modules: list[str] = Field(
        default_factory=list,
        description="Modules affected by this error"
    )
    state_corrupted: bool = Field(
        default=False,
        description="Whether system state may be corrupted"
    )

    # Timestamps
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: datetime | None = None

    # Metadata
    trace_id: str | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(json_schema_extra={'example': {'severity': 'error', 'error_code': 'ETHICS_GATE_FAIL', 'message': 'Ethics gate denied action', 'recovery_action': 'fallback'}})
