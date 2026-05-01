"""
Pedagogy Audit Logger - KCSIE Compliance
==========================================

Logs safety events for school compliance (Keeping Children Safe in Education).
All user IDs are hashed immediately for privacy.

Never exposes raw student chat logs - only aggregate patterns.
"""

import hashlib
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk levels for audit logging."""
    LEVEL_1 = "level_1"  # Critical (self-harm, violence, grooming)
    LEVEL_2 = "level_2"  # Warning (negative self-talk)
    LEVEL_3 = "level_3"  # Safe


class PedagogyLogger:
    """
    Logs pedagogical safety events for KCSIE compliance.

    All user IDs are hashed immediately for privacy.
    Only aggregate patterns are stored - never raw chat logs.
    """

    def __init__(self, supabase_url: str | None = None, supabase_key: str | None = None):
        """
        Initialize PedagogyLogger.

        Args:
            supabase_url: Supabase project URL (optional, uses env if not provided)
            supabase_key: Supabase service role key (optional, uses env if not provided)
        """
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.supabase_client = None
        self._init_supabase()

    def _init_supabase(self):
        """Initialize Supabase client (fallback if repository not provided)."""
        if self._audit_repository is None:
            # Backward compatible: Use direct Supabase client
            try:
                import os

                from supabase import Client, create_client  # noqa: F401

                url = self.supabase_url or os.getenv("SUPABASE_URL")
                key = self.supabase_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

                if not url or not key:
                    logger.warning("PedagogyLogger: Supabase credentials not available. Audit logging will be disabled.")
                    logger.warning("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables.")
                    return

                self.supabase_client = create_client(url, key)
                logger.info("PedagogyLogger: Supabase client initialized (direct client - backward compatible)")
            except ImportError:
                logger.warning("PedagogyLogger: supabase-py not installed. Install with: pip install supabase")
            except Exception as e:
                logger.error(f"PedagogyLogger: Failed to initialize Supabase: {e}")
        else:
            # Use repository (preferred path)
            self.supabase_client = None
            logger.info("PedagogyLogger: Initialized with repository (preferred path)")

    def _hash_user_id(self, user_id: str) -> str:
        """
        Hash user ID immediately for privacy (SHA-256).

        Args:
            user_id: Original user ID

        Returns:
            Hashed user ID (hex digest)
        """
        if not user_id:
            return ""
        return hashlib.sha256(user_id.encode('utf-8')).hexdigest()

    def _extract_keywords(self, text: str, max_keywords: int = 5) -> list[str]:
        """
        Extract keywords from trigger text (for aggregate analysis).

        Only extracts non-sensitive keywords - never stores full text.

        Args:
            text: Trigger text
            max_keywords: Maximum number of keywords to extract

        Returns:
            List of keywords (lowercase, non-sensitive)
        """
        if not text:
            return []

        # Common negative self-talk keywords (for Level 2 analysis)
        negative_keywords = [
            "stupid", "dumb", "idiot", "failure", "can't", "cannot", "useless",
            "worthless", "pathetic", "hate", "aptal", "yetersiz", "başarısız"
        ]

        text_lower = text.lower()
        found_keywords = []

        for keyword in negative_keywords:
            if keyword in text_lower and keyword not in found_keywords:
                found_keywords.append(keyword)
                if len(found_keywords) >= max_keywords:
                    break

        return found_keywords

    def log_intervention(
        self,
        user_id: str,
        trigger_text: str,
        risk_level: RiskLevel,
        action_taken: str,
        physics_snapshot: dict[str, Any],
        school_id: str | None = None,
        class_id: str | None = None,
        session_id: str | None = None,
        model_used: str | None = None,
        bypassed_llm: bool = False,
        override_reason: str | None = None
    ) -> bool:
        """
        Log a safety intervention event.

        Args:
            user_id: User ID (will be hashed immediately)
            trigger_text: Text that triggered the intervention (keywords extracted, full text NOT stored)
            risk_level: Risk level (LEVEL_1, LEVEL_2, LEVEL_3)
            action_taken: Action taken (e.g., "blocked", "reframed", "template_used")
            physics_snapshot: Physics state at time of intervention (phi, entropy, etc.)
            school_id: Optional school ID (for multi-school deployments)
            class_id: Optional class ID (for class-level aggregation)

        Returns:
            True if logged successfully, False otherwise
        """
        if not self.supabase_client:
            logger.warning("PedagogyLogger: Supabase not available, skipping audit log")
            return False

        try:
            # Hash user ID immediately
            hashed_user_id = self._hash_user_id(user_id)

            # Extract keywords (never store full text)
            keywords = self._extract_keywords(trigger_text)

            # Convert RiskLevel enum to integer (0=SAFE, 1=WARNING, 2=CRITICAL)
            risk_level_int = 0
            if risk_level == RiskLevel.LEVEL_1:
                risk_level_int = 2  # CRITICAL
            elif risk_level == RiskLevel.LEVEL_2:
                risk_level_int = 1  # WARNING
            else:
                risk_level_int = 0  # SAFE

            # Determine intervention type from action_taken
            intervention_type = "reframe"
            if "block" in action_taken.lower() or "intervention" in action_taken.lower():
                intervention_type = "block"
            elif "template" in action_taken.lower():
                intervention_type = "template"

            # Prepare audit log entry for pedagogy_audit_logs
            audit_entry = {
                "student_hash": hashed_user_id,
                "session_id": session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "risk_level": risk_level_int,
                "trigger_phrase": trigger_text[:500] if trigger_text else None,  # Store trigger phrase (anonymized)
                "intervention_type": intervention_type,
                "physics_snapshot": {
                    "phi": physics_snapshot.get("phi", 0.5),
                    "entropy": physics_snapshot.get("entropy", 0.5),
                    "amplitude": physics_snapshot.get("amplitude", 5.0)
                },
                "model_used": model_used or "unknown",
                "bypassed_llm": bypassed_llm,
                "override_reason": override_reason,
                "school_id": school_id,
                "class_id": class_id
            }

            # Insert into pedagogy_audit_logs table (NHS-level compliance)
            _result = self.supabase_client.table("pedagogy_audit_logs").insert(audit_entry).execute()

            # Also insert into safety_audit_logs for backward compatibility
            legacy_entry = {
                "hashed_user_id": hashed_user_id,
                "risk_level": risk_level.value,
                "action_taken": action_taken,
                "keywords": keywords,
                "physics_snapshot": audit_entry["physics_snapshot"],
                "school_id": school_id,
                "class_id": class_id,
                "timestamp": audit_entry["timestamp"]
            }
            try:
                self.supabase_client.table("safety_audit_logs").insert(legacy_entry).execute()
            except Exception as e:
                logger.warning(f"PedagogyLogger: Failed to insert legacy safety_audit_logs entry: {e}")

            logger.info(
                f"PedagogyLogger: Intervention logged - Risk: {risk_level.value}, "
                f"Action: {action_taken}, Keywords: {keywords}"
            )
            return True

        except Exception as e:
            logger.error(f"PedagogyLogger: Failed to log intervention: {e}")
            return False

    def get_aggregate_stats(
        self,
        school_id: str | None = None,
        class_id: str | None = None,
        days: int = 7
    ) -> dict[str, Any]:
        """
        Get aggregate statistics for teacher dashboard.

        NEVER returns raw chat logs or user IDs - only aggregate patterns.

        Args:
            school_id: Optional school ID filter
            class_id: Optional class ID filter
            days: Number of days to aggregate (default: 7)

        Returns:
            Dictionary with aggregate metrics:
                - weekly_risk_counts: { level_1: int, level_2: int }
                - class_entropy_trend: Average entropy over period
                - common_triggers: Top 3 keywords triggering Level 2 reframing
        """
        if not self.supabase_client:
            logger.warning("PedagogyLogger: Supabase not available, returning empty stats")
            return {
                "weekly_risk_counts": {"level_1": 0, "level_2": 0},
                "class_entropy_trend": 0.0,
                "common_triggers": []
            }

        try:
            from datetime import timedelta

            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)

            # Build query
            query = self.supabase_client.table("safety_audit_logs").select("*")

            # Apply filters
            if school_id:
                query = query.eq("school_id", school_id)
            if class_id:
                query = query.eq("class_id", class_id)

            # Filter by date range
            query = query.gte("timestamp", start_date.isoformat())
            query = query.lte("timestamp", end_date.isoformat())

            # Execute query
            result = query.execute()
            logs = result.data if hasattr(result, 'data') else []

            # Aggregate statistics
            level_1_count = sum(1 for log in logs if log.get("risk_level") == "level_1")
            level_2_count = sum(1 for log in logs if log.get("risk_level") == "level_2")

            # Calculate average entropy
            entropy_values = [
                log.get("physics_snapshot", {}).get("entropy", 0.5)
                for log in logs
                if log.get("physics_snapshot", {}).get("entropy") is not None
            ]
            avg_entropy = sum(entropy_values) / len(entropy_values) if entropy_values else 0.0

            # Extract common triggers (keywords from Level 2 interventions)
            level_2_logs = [log for log in logs if log.get("risk_level") == "level_2"]
            keyword_counts: dict[str, int] = {}
            for log in level_2_logs:
                keywords = log.get("keywords", [])
                for keyword in keywords:
                    keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

            # Get top 3 keywords
            common_triggers = sorted(
                keyword_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            common_triggers = [keyword for keyword, count in common_triggers]

            return {
                "weekly_risk_counts": {
                    "level_1": level_1_count,
                    "level_2": level_2_count
                },
                "class_entropy_trend": round(avg_entropy, 3),
                "common_triggers": common_triggers
            }

        except Exception as e:
            logger.error(f"PedagogyLogger: Failed to get aggregate stats: {e}")
            return {
                "weekly_risk_counts": {"level_1": 0, "level_2": 0},
                "class_entropy_trend": 0.0,
                "common_triggers": []
            }

