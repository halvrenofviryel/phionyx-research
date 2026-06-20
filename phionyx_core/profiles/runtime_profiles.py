"""Runtime deployment profiles — the three governance products + a full baseline.

Grounded in the phionyx-core value study (docs/research/phionyx_core_value_study/):
the governance value concentrates in the evidence record (C), calibrated
abstention (D), and fail-closed gates (B) — NOT the physics/mind-loop. Rather than
"run all 46 blocks," a deployment selects a profile that names which canonical
blocks are ACTIVE; the rest are **policy-bypassed with an audit trail** (never
deleted — Architecture Invariant: "Blocks are never deleted, only policy-bypassed").

This module is declarative + additive. It does NOT itself rewire the pipeline; the
orchestrator/block_factory consume `active_blocks` as a bypass policy (follow-up,
founder-gated because it touches pipeline assembly + determinism).

Profiles map to the three runtimes presented on phionyx.ai:
  - Evidence Runtime         (Category C — the notary)
  - Abstention & Boundary    (Category D — calibrated refuse/hedge/defer)
  - Safety Gate Profile      (Category B — fail-closed gates + escalation)
  - Full Cognition (baseline — all 46; for products that genuinely need the
    physics/affect/memory substrate, e.g. NPC Studio / companions)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# The canonical 46 (contract v3.8.0). Kept here as the validation surface; the
# accompanying test cross-checks this against
# contracts/telemetry/canonical_blocks_v3_8_0.json so drift is caught.
CANONICAL_BLOCKS_V3_8_0: tuple[str, ...] = (
    "kill_switch_gate", "time_update_sot", "input_safety_gate", "intent_classification",
    "context_retrieval_rag", "perceptual_frame_emit", "create_scenario_frame",
    "initialize_unified_state", "goal_evaluation", "goal_decomposition", "ukf_predict",
    "entropy_amplitude_pre_gate", "cognitive_layer", "self_model_assessment",
    "knowledge_boundary_check", "trust_evaluation", "ethics_pre_response",
    "deliberative_ethics_gate", "cep_evaluation", "narrative_layer", "ethics_post_response",
    "action_intent_gate", "behavioral_drift_detection", "workspace_broadcast",
    "unified_state_update_esc", "phi_publish", "entropy_amplitude_post_gate",
    "neurotransmitter_memory_growth", "emotion_estimation", "state_update_physics",
    "causal_graph_update", "causal_intervention", "counterfactual_analysis",
    "root_cause_analysis", "causal_simulation", "world_state_snapshot", "phi_computation",
    "entropy_computation", "confidence_fusion", "arbitration_resolve",
    "response_revision_gate", "response_build", "memory_consolidation", "audit_layer",
    "outcome_feedback", "learning_gate",
)
_CANON = frozenset(CANONICAL_BLOCKS_V3_8_0)

# Safety + record floor — present in EVERY governance profile (never bypassed).
_FLOOR = ("kill_switch_gate", "input_safety_gate", "audit_layer")


@dataclass(frozen=True)
class RuntimeProfile:
    """A deployment profile: which canonical blocks are active vs policy-bypassed."""
    name: str
    title: str
    category: str  # the value-study category this profile delivers (C/D/B/full)
    description: str
    active_blocks: tuple[str, ...]
    fail_closed: bool
    execution_mode: Literal["inline", "async", "hybrid"]
    target_types: tuple[str, ...]
    artifact: str  # the concrete buyer-facing artifact this profile produces

    @property
    def bypassed_blocks(self) -> tuple[str, ...]:
        """Blocks NOT active for this profile — policy-bypassed (with audit), not deleted."""
        return tuple(b for b in CANONICAL_BLOCKS_V3_8_0 if b not in set(self.active_blocks))

    def validate(self) -> None:
        unknown = set(self.active_blocks) - _CANON
        if unknown:
            raise ValueError(f"{self.name}: unknown blocks {sorted(unknown)}")
        missing_floor = set(_FLOOR) - set(self.active_blocks)
        if self.name != "full_cognition" and missing_floor:
            raise ValueError(f"{self.name}: must keep safety/record floor {sorted(missing_floor)}")


# ── Profile A — Evidence Runtime (Category C, the notary) ──────────────────────
EVIDENCE_RUNTIME = RuntimeProfile(
    name="evidence",
    title="Evidence Runtime",
    category="C",
    description=(
        "Turn each AI decision into a signed, hash-chained, replayable record. The "
        "flagship — deployable without the physics/mind-loop. Proven by sim S3 "
        "(deterministic tamper detection)."
    ),
    active_blocks=(
        "kill_switch_gate", "input_safety_gate", "intent_classification",
        "knowledge_boundary_check", "confidence_fusion", "trust_evaluation",
        "response_revision_gate", "response_build",
        "phi_computation", "entropy_computation",  # minimal state to populate the record
        "audit_layer", "outcome_feedback", "learning_gate",
    ),
    fail_closed=True,
    execution_mode="hybrid",  # decision inline, record signing async
    target_types=("T1", "T2", "T5", "T8", "T10", "T11"),
    artifact="signed, replayable per-decision evidence record (AIREP/RGE envelope chain)",
)

# ── Profile B — Abstention & Boundary Runtime (Category D) ─────────────────────
ABSTENTION_BOUNDARY_RUNTIME = RuntimeProfile(
    name="abstention_boundary",
    title="Abstention & Boundary Runtime",
    category="D",
    description=(
        "When the system is outside its evidence boundary, make that boundary "
        "operational: hedge / ask / defer / refuse with a calibrated confidence. "
        "Value is the calibration (sim S1: real OOD signal required, else over-refuses)."
    ),
    active_blocks=(
        "kill_switch_gate", "input_safety_gate", "intent_classification",
        "context_retrieval_rag", "self_model_assessment", "knowledge_boundary_check",
        "trust_evaluation", "confidence_fusion", "response_revision_gate",
        "response_build", "audit_layer", "outcome_feedback",
    ),
    fail_closed=True,
    execution_mode="inline",  # the abstain/proceed decision must gate the response
    target_types=("T3", "T6"),
    artifact="calibrated abstention decision (proceed/hedge/ask/defer/refuse) + reason, recorded",
)

# ── Profile C — Safety Gate Profile (Category B, fail-closed) ──────────────────
SAFETY_GATE_PROFILE = RuntimeProfile(
    name="safety_gate",
    title="Safety Gate Profile",
    category="B",
    description=(
        "Gate the language/tool/action decision layer — fail-closed, with escalation. "
        "NOT a certified physical-safety controller. Proven by sim S4 (post-fix: "
        "missing/raising scorer now BLOCKS/DEFERS)."
    ),
    active_blocks=(
        "kill_switch_gate", "input_safety_gate", "intent_classification",
        "ethics_pre_response", "deliberative_ethics_gate", "action_intent_gate",
        "ethics_post_response", "arbitration_resolve", "response_revision_gate",
        "response_build", "audit_layer",
    ),
    fail_closed=True,  # sets PHIONYX_SAFETY_FAIL_CLOSED for the gate blocks
    execution_mode="inline",
    target_types=("T4", "T9", "T11"),
    artifact="fail-closed allow/deny/defer-to-human gate decision + escalation record",
)

# ── Full Cognition (baseline — all 46) ────────────────────────────────────────
# For products that genuinely need the physics/affect/memory substrate (NPC Studio,
# companions). The governance profiles above are subsets of this.
FULL_COGNITION = RuntimeProfile(
    name="full_cognition",
    title="Full Cognition (baseline)",
    category="full",
    description=(
        "All 46 canonical blocks. The research substrate — physics, mind-loop, memory. "
        "Use only when the affect/physics IS the product (NPC Studio, companions). The "
        "value study shows this is NOT where governance value lives — never the public "
        "governance pitch."
    ),
    active_blocks=CANONICAL_BLOCKS_V3_8_0,
    fail_closed=True,
    execution_mode="inline",
    target_types=("T9",),
    artifact="full cognitive trace (physics + affect + mind-loop) + signed record",
)

RUNTIME_PROFILES: dict[str, RuntimeProfile] = {
    p.name: p for p in (
        EVIDENCE_RUNTIME, ABSTENTION_BOUNDARY_RUNTIME, SAFETY_GATE_PROFILE, FULL_COGNITION,
    )
}

# Per-application-type → composed profile(s). Composition = union of active blocks
# (a deployment can layer Evidence under Safety-Gate under Abstention).
APPLICATION_PROFILE_MAP: dict[str, tuple[str, ...]] = {
    "T1_coding_agents": ("evidence",),
    "T2_support_chatbots": ("evidence", "abstention_boundary"),
    "T3_rag_assistants": ("abstention_boundary", "evidence"),
    "T4_autonomous_agents": ("safety_gate", "evidence"),
    "T5_multi_agent": ("evidence",),  # + per-agent keys (follow-up)
    "T6_high_stakes": ("abstention_boundary", "safety_gate", "evidence"),
    "T7_content_generation": ("evidence",),  # regulated slice only
    "T8_moderation": ("evidence", "abstention_boundary"),
    "T9_companions_education_npc": ("safety_gate", "evidence"),
    "T10_tool_api_agents": ("evidence", "safety_gate"),
    "T11_robotics_planner": ("evidence",),  # planner layer ONLY, never control path
    "T12_voice_realtime": ("evidence",),    # async + thin safety subset
    # Phionyx products (private repo):
    "product_trace_school_rpg": ("safety_gate", "evidence"),  # safeguarding-first
    "product_npc_studio": ("full_cognition", "safety_gate", "evidence"),  # affect IS the product
    "product_scenario_generator": ("evidence",),  # canon/version provenance
    # Soul Engine is a SHARED character-affect service, not a profile — consumed by
    # the products above (NPC Studio, optionally Trace) via its FastAPI interface.
}


def get_runtime_profile(name: str) -> RuntimeProfile:
    if name not in RUNTIME_PROFILES:
        raise KeyError(f"unknown runtime profile {name!r}; have {sorted(RUNTIME_PROFILES)}")
    return RUNTIME_PROFILES[name]


def compose(*names: str) -> frozenset[str]:
    """Union of active blocks across the named profiles (deployment layering)."""
    active: set[str] = set()
    for n in names:
        active |= set(get_runtime_profile(n).active_blocks)
    return frozenset(active)


def profiles_for_application(app_key: str) -> tuple[RuntimeProfile, ...]:
    if app_key not in APPLICATION_PROFILE_MAP:
        raise KeyError(f"unknown application {app_key!r}")
    return tuple(get_runtime_profile(n) for n in APPLICATION_PROFILE_MAP[app_key])


# ── The three profile LAYERS (how the older profile files compose with these) ──
# A product deployment selects all three, each answering a different question:
#   1. runtime_profile (THIS module) — WHICH canonical blocks run (bypass policy).
#   2. module_profile  (profiles/ package: load_profile / ProfileManager) — HOW the
#      active modules are configured: pedagogy / governance / routing / exec-guard.
#   3. physics_profile (physics/profiles.yaml via ProfileLoader/tuner) — the physics
#      PARAMETER values (reactivity↔gamma, resilience↔stability, …).
# These are orthogonal + complementary, not redundant. The bindings below name all
# three per product so the (previously dormant) module + physics profiles are used.
@dataclass(frozen=True)
class ProductProfileBinding:
    product: str
    runtime_profiles: tuple[str, ...]   # layer 1 (this module)
    module_profile: str                 # layer 2 (profiles.load_profile name)
    physics_profile: str                # layer 3 (physics/profiles.yaml name)


PRODUCT_PROFILE_BINDINGS: dict[str, ProductProfileBinding] = {
    "trace_school_rpg": ProductProfileBinding(
        "trace_school_rpg", ("safety_gate", "evidence"), "trace_school_rpg", "SCHOOL_STRICT"),
    "npc_studio": ProductProfileBinding(
        "npc_studio", ("full_cognition", "safety_gate", "evidence"), "npc_studio", "GAME_BALANCED"),
    "scenario_generator": ProductProfileBinding(
        "scenario_generator", ("evidence",), "scenario_generator", "GAME_BALANCED"),
    # HearthOS — bounded-authority household assistant (system proposes, the adult
    # decides). Same Safety-Gate+Evidence shape as Trace School RPG. It already ships
    # its own signed, hash-chained Bounded Authority Decision Record
    # (phionyx.bounded_authority_envelope.v1); aligning it to the kernel profiles is
    # the same path as the Trace local-mirror → live-kernel bridge.
    "hearthos": ProductProfileBinding(
        "hearthos", ("safety_gate", "evidence"), "hearthos", "THERAPY_SUPPORT"),
}


def binding_for_product(product: str) -> ProductProfileBinding:
    if product not in PRODUCT_PROFILE_BINDINGS:
        raise KeyError(f"unknown product {product!r}; have {sorted(PRODUCT_PROFILE_BINDINGS)}")
    return PRODUCT_PROFILE_BINDINGS[product]
