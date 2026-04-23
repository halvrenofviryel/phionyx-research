"""Audit logger — append-only structured event logging.

Every experiment action is logged with full context for
accountability and traceability. The audit log is Tier D (immutable).
"""
import json
import time
from pathlib import Path
from typing import Any


class AuditLogger:
    """Append-only audit event logger.

    Events are written as JSONL with timestamps.
    The audit log is never modified or deleted.
    """

    def __init__(self, audit_dir: str = "data/research_engine/audit"):
        self._dir = Path(audit_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._file = self._dir / "audit.jsonl"

    def log(self, event_type: str, data: dict[str, Any]) -> None:
        """Log an audit event."""
        event = {
            "event_type": event_type,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "epoch": time.time(),
            **data,
        }
        with open(self._file, "a") as f:
            f.write(json.dumps(event, default=str) + "\n")

    def log_experiment_start(self, experiment_id: str, hypothesis: dict) -> None:
        """Log experiment start."""
        self.log("experiment_start", {
            "experiment_id": experiment_id,
            "hypothesis": hypothesis,
        })

    def log_experiment_complete(
        self,
        experiment_id: str,
        decision: str,
        status: str,
        rationale: str,
        cqs_delta: float,
        metrics: dict,
    ) -> None:
        """Log experiment completion with decision."""
        self.log("experiment_complete", {
            "experiment_id": experiment_id,
            "decision": decision,
            "status": status,
            "rationale": rationale,
            "cqs_delta": cqs_delta,
            "metrics": metrics,
        })

    def log_revert(self, experiment_id: str, git_commit: str) -> None:
        """Log a revert action."""
        self.log("revert", {
            "experiment_id": experiment_id,
            "git_commit": git_commit,
        })

    def log_session_start(self, session_id: str, config: dict) -> None:
        """Log session start with configuration."""
        self.log("session_start", {
            "session_id": session_id,
            "config": config,
        })

    def log_session_end(self, session_id: str, report: dict) -> None:
        """Log session end with summary report."""
        self.log("session_end", {
            "session_id": session_id,
            "report": report,
        })

    def log_budget_exhausted(self, session_id: str, reason: str) -> None:
        """Log budget exhaustion."""
        self.log("budget_exhausted", {
            "session_id": session_id,
            "reason": reason,
        })

    def get_events(self, event_type: str | None = None) -> list[dict]:
        """Get audit events, optionally filtered by type."""
        if not self._file.exists():
            return []
        events = []
        with open(self._file) as f:
            for line in f:
                line = line.strip()
                if line:
                    event = json.loads(line)
                    if event_type is None or event.get("event_type") == event_type:
                        events.append(event)
        return events
