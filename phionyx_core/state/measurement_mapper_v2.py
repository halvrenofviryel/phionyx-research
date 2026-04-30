"""
Measurement Mapper v2.0 - Enhanced with MeasurementPacket
===========================================================

Per Echoism Core v1.1 / Faz 2.1:
- MeasurementPacket: Extended measurement with optional D, provider metadata, timestamp, evidence
- EvidenceSpan: Text spans that contributed to measurement
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field



class EvidenceSpan(BaseModel):
    """Text span that contributed to a measurement."""
    start: int
    end: int
    text: str
    contribution: float = Field(default=0.5, ge=0.0, le=1.0, description="Contribution weight")


class MeasurementPacket(BaseModel):
    """
    Enhanced measurement packet (v2.0).

    Per Faz 2.1:
    - Includes optional D (dominance)
    - Provider metadata for quality assessment
    - Timestamp for temporal tracking
    - Evidence spans for explainability
    """
    A: float = Field(ge=-1.0, le=1.0, description="Arousal measurement")
    V: float = Field(ge=-1.0, le=1.0, description="Valence measurement")
    D: Optional[float] = Field(default=None, ge=-1.0, le=1.0, description="Dominance measurement (optional)")
    H: float = Field(ge=0.0, le=1.0, description="Entropy measurement")
    confidence: float = Field(ge=0.0, le=1.0, description="Measurement confidence")
    provider: Dict[str, Any] = Field(default_factory=dict, description="Provider metadata")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Measurement timestamp")
    evidence_spans: List[EvidenceSpan] = Field(default_factory=list, description="Evidence spans")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "A": self.A,
            "V": self.V,
            "D": self.D,
            "H": self.H,
            "confidence": self.confidence,
            "provider": self.provider,
            "timestamp": self.timestamp.isoformat(),
            "evidence_spans": [span.model_dump() for span in self.evidence_spans]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MeasurementPacket:
        """Create from dictionary."""
        evidence_spans = [
            EvidenceSpan(**span) if isinstance(span, dict) else span
            for span in data.get("evidence_spans", [])
        ]

        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        elif timestamp is None:
            timestamp = datetime.now(timezone.utc)

        return cls(
            A=data.get("A", data.get("A_meas", 0.0)),
            V=data.get("V", data.get("V_meas", 0.0)),
            D=data.get("D", data.get("D_meas")),
            H=data.get("H", data.get("H_meas", 0.5)),
            confidence=data.get("confidence", 0.5),
            provider=data.get("provider", {}),
            timestamp=timestamp,
            evidence_spans=evidence_spans
        )

