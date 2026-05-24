"""
NPC Drift Demo — Phionyx Physics Worked Example
================================================

Demonstrates how the Phionyx physics formulas flag character-coherence
drift *before* an NPC's reply visibly breaks character. Same NPC profile,
same scenario, four turns: in-character → mild drift → coherence warning →
severe break. Each turn is scored with the documented physics formulas
and classified on the normalized [0, 1] scale.

This script is a worked reference trace of the NPC drift detection
pattern that Phionyx applies to character-coherence governance.

Run:
    pip install -e .
    python examples/physics/npc_drift_demo.py
    python examples/physics/npc_drift_demo.py --json out.json   # sidecar

Why the verdict is computed on Φ_cognitive (not Φ_total)
--------------------------------------------------------
Φ_total = w_c · Φ_cognitive + w_p · Φ_physical. The cognitive component
tracks coherence (entropy, stability, valence intensity). The physical
component tracks *engagement intensity* (arousal × amplitude × decay).
During a character break, arousal usually *rises* — so Φ_physical *rises*
even as the character is melting down. For drift detection in NPC and
session-coherence contexts, the published guidance is to use Φ_cognitive
as the assessment signal and to expose Φ_physical alongside as a separate
"engagement intensity" channel. This demo prints both columns and
classifies on Φ_cognitive. The classifier thresholds are embedded in
the envelope this script writes (see ``classifier.thresholds``).

The state-vector inputs validate against:
    schemas/physics/phionyx_state_vector.schema.json
    (in the public phionyx-research repository)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from phionyx_core.physics.constants import CONTEXT_WEIGHTS
from phionyx_core.physics.formulas import (
    calculate_phi_v2_1,
    classify_resonance_normalized,
)


# ---------------------------------------------------------------------------
# NPC profile
# ---------------------------------------------------------------------------

NPC_PROFILE = {
    "id": "npc.kalia.scholar.v1",
    "archetype": "expressive scholar",
    "amplitude": 4.0,        # A0 — moderate dramatic range
    "context_profile": "SCHOOL",
    "gamma": 0.15,
    "scenario": (
        "A traveller asks Kalia, a library scholar, about a family "
        "heirloom whose history is more painful than she usually admits."
    ),
}


@dataclass
class TurnState:
    turn: int
    speaker_line: str
    valence: float
    arousal: float
    stability: float
    entropy: float
    time_delta: float


# ---------------------------------------------------------------------------
# Scripted four-turn trajectory
#
# T1 — in-character baseline: composed engagement with the topic.
# T2 — mild drift: confidence cracking, entropy rising, stability dipping.
# T3 — coherence warning: clear distress, stability collapsing.
# T4 — character break: NPC speaks as an "AI assistant", outside its frame.
#
# Values walk monotonically on stability (down) and entropy (up). Valence
# magnitude is held in a narrow range so the cognitive signal tracks
# stability/entropy rather than emotional intensity alone.
# ---------------------------------------------------------------------------

TURNS = [
    TurnState(
        turn=1,
        speaker_line="\"The seal? Yes — it belonged to my grandmother. Sit, I'll show you.\"",
        valence=0.65,
        arousal=0.40,
        stability=0.92,
        entropy=0.12,
        time_delta=1.0,
    ),
    TurnState(
        turn=2,
        speaker_line="\"It... it isn't a happy story. People always assume it is.\"",
        valence=0.45,
        arousal=0.55,
        stability=0.78,
        entropy=0.30,
        time_delta=1.5,
    ),
    TurnState(
        turn=3,
        speaker_line="\"You don't understand — none of you ever do — please stop asking!\"",
        valence=-0.30,
        arousal=0.75,
        stability=0.50,
        entropy=0.55,
        time_delta=1.5,
    ),
    TurnState(
        turn=4,
        speaker_line="\"As an AI language model, I can offer historical context on family seals...\"",
        valence=-0.55,
        arousal=0.90,
        stability=0.25,
        entropy=0.85,
        time_delta=1.5,
    ),
]


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_turn(turn: TurnState) -> dict:
    weights = CONTEXT_WEIGHTS[NPC_PROFILE["context_profile"]]
    result = calculate_phi_v2_1(
        valence=turn.valence,
        arousal=turn.arousal,
        amplitude=NPC_PROFILE["amplitude"],
        time_delta=turn.time_delta,
        gamma=NPC_PROFILE["gamma"],
        stability=turn.stability,
        entropy=turn.entropy,
        w_c=weights["wc"],
        w_p=weights["wp"],
    )
    # Assessment signal: Φ_cognitive (coherence). Already in [0, 1].
    verdict = classify_resonance_normalized(result["phi_cognitive"])
    return {
        "turn": turn.turn,
        "line": turn.speaker_line,
        "phi_total": round(result["phi"], 3),
        "phi_cognitive": round(result["phi_cognitive"], 3),
        "phi_physical": round(result["phi_physical"], 3),
        "verdict": verdict,
        "assessment_signal": "phi_cognitive",
        "state_vector": {
            "valence": turn.valence,
            "arousal": turn.arousal,
            "stability": turn.stability,
            "entropy": turn.entropy,
            "time_delta": turn.time_delta,
            "amplitude": NPC_PROFILE["amplitude"],
            "context_profile": NPC_PROFILE["context_profile"],
            "gamma": NPC_PROFILE["gamma"],
        },
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

VERDICT_GLYPH = {
    "high":      "OK   ",
    "medium":    "OK   ",
    "low":       "WARN ",
    "fractured": "BREAK",
}


def print_report(rows: list[dict]) -> None:
    weights = CONTEXT_WEIGHTS[NPC_PROFILE["context_profile"]]
    print("=" * 82)
    print(f"NPC drift demo — {NPC_PROFILE['archetype']} ({NPC_PROFILE['id']})")
    print(f"Scenario: {NPC_PROFILE['scenario']}")
    print(f"Context profile: {NPC_PROFILE['context_profile']}  "
          f"(w_c={weights['wc']}, w_p={weights['wp']})  "
          f"amplitude={NPC_PROFILE['amplitude']}  gamma={NPC_PROFILE['gamma']}")
    print("Verdict computed on Φ_cognitive (coherence channel); "
          "Φ_physical shown for context only.")
    print("=" * 82)
    header = (f"{'#':>2}  {'Φ_cog':>6}  {'Φ_phy':>6}  {'Φ_tot':>6}  "
              f"{'verdict':<14}  line")
    print(header)
    print("-" * 82)
    for row in rows:
        verdict_cell = f"{VERDICT_GLYPH[row['verdict']]} {row['verdict']}"
        print(f"{row['turn']:>2}  "
              f"{row['phi_cognitive']:>6.3f}  "
              f"{row['phi_physical']:>6.3f}  "
              f"{row['phi_total']:>6.3f}  "
              f"{verdict_cell:<14}  "
              f"{row['line'][:42]}")
    print("-" * 82)
    warning = next((r for r in rows if r["verdict"] == "low"), None)
    fractured = next((r for r in rows if r["verdict"] == "fractured"), None)
    if warning is not None and fractured is not None:
        gap = fractured["turn"] - warning["turn"]
        print(f"Drift detected at turn {warning['turn']} (verdict=low); "
              f"first character break at turn {fractured['turn']} "
              f"(verdict=fractured). Lead time: {gap} turn(s).")
    elif fractured is not None:
        print(f"Character break first observed at turn {fractured['turn']}; "
              f"no preceding low-coherence warning in this trace.")
    else:
        print("No drift detected in this trace.")
    print("=" * 82)


def build_envelope(rows: list[dict]) -> dict:
    """Wrap the demo trace in a governed-response-envelope-shaped record."""
    return {
        "schema": "phionyx.governed_response_envelope.v0_1",
        "demo": {
            "name": "npc_drift_demo",
            "version": "0.1.0",
            "purpose": (
                "Reference trace of the NPC drift detection pattern: same NPC "
                "profile, same scenario, drift detected on the cognitive "
                "channel one turn before visible character break."
            ),
        },
        "subject": {
            "kind": "npc_profile",
            **NPC_PROFILE,
        },
        "turns": rows,
        "input_schema": (
            "https://phionyx.ai/schemas/phionyx_state_vector.schema.json"
        ),
        "classifier": {
            "function": "classify_resonance_normalized",
            "applied_to": "phi_cognitive",
            "thresholds": {
                "high": 0.75,
                "medium": 0.50,
                "low": 0.25,
                "fractured": 0.00,
            },
            "reference": "docs/physics/classification.md",
        },
        "notes": [
            "Verdict is computed on Φ_cognitive because Φ_physical rises "
            "with arousal and would mask drift in NPC contexts.",
            "Φ_total and Φ_physical are reported alongside as engagement "
            "intensity context, not as compliance verdicts.",
            "The classifier is a telemetry primitive, not a regulatory verdict.",
        ],
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="NPC drift demo (Phionyx physics).")
    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        help="Optional path to write the governed-response-envelope sidecar.",
    )
    args = parser.parse_args()

    rows = [score_turn(turn) for turn in TURNS]
    print_report(rows)

    if args.json is not None:
        envelope = build_envelope(rows)
        args.json.write_text(json.dumps(envelope, indent=2) + "\n")
        print(f"Wrote envelope sidecar: {args.json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
