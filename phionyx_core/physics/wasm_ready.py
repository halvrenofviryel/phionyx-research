"""
WASM-Ready Physics Functions
=============================

Wrapper layer for WASM compilation compatibility.
Ensures all functions are pure, typed, and SIMD-friendly.
"""

from typing import List
from .formulas import (
    calculate_phi_v2_1,
    get_context_weights,
    calculate_functional_coherence_score,
)


# Type aliases for WASM compatibility
Float32Array = List[float]
Float64Array = List[float]


def calculate_phi_v2_1_batch(
    valence_array: List[float],
    arousal_array: List[float],
    entropy_array: List[float],
    stability_array: List[float],
    amplitude_array: List[float],
    time_delta_array: List[float],
    gamma_array: List[float],
    context_mode: str = "DEFAULT",
) -> List[float]:
    """
    Batch version of calculate_phi_v2_1 for SIMD optimization.

    **Renamed and re-signed 2026-08-02** (was ``calculate_phi_v2_batch``).
    ``calculate_phi_v2`` is labelled "v2.0 (Legacy)" in formulas.py and this
    helper wrapped it, so the batch surface carried the legacy defaults:
    valence 0.0, arousal 1.0 — maximum arousal on every element — and
    ``entropy_penalty_k`` 0.0, which switches the entropy term off. With
    matched arguments the two functions are numerically identical, so this is
    an interface change; what it removes is the defaults standing in for
    values the caller has.

    ``valence_array`` and ``arousal_array`` are **required**, not defaulted.
    v2_1 takes no permissive defaults and neither does its batch form: a caller
    that does not have valence does not have a phi.

    ``context_mode`` is resolved to explicit weights once per call rather than
    per element, since it is constant across the batch.

    Args:
        valence_array: Array of valence values
        arousal_array: Array of arousal values
        entropy_array: Array of entropy values
        stability_array: Array of stability values
        amplitude_array: Array of amplitude values
        time_delta_array: Array of time deltas
        gamma_array: Array of gamma values
        context_mode: Context mode (same for all)

    Returns:
        Array of phi values
    """
    if not all(
        len(arr) == len(entropy_array)
        for arr in [valence_array, arousal_array, stability_array,
                    amplitude_array, time_delta_array, gamma_array]
    ):
        raise ValueError("All input arrays must have the same length")

    weights = get_context_weights(context_mode)
    results = []
    for i in range(len(entropy_array)):
        result = calculate_phi_v2_1(
            valence=valence_array[i],
            arousal=arousal_array[i],
            amplitude=amplitude_array[i],
            time_delta=time_delta_array[i],
            gamma=gamma_array[i],
            stability=stability_array[i],
            entropy=entropy_array[i],
            w_c=weights["wc"],
            w_p=weights["wp"],
        )
        results.append(result.get("phi", 0.0))

    return results


def calculate_fcs_batch(
    phi_current_array: Float32Array,
    phi_previous_array: Float32Array,
    time_delta_array: Float32Array,
    f_self: float = 0.5
) -> Float32Array:
    """
    Batch version of calculate_functional_coherence_score for SIMD optimization.

    Args:
        phi_current_array: Array of current phi values
        phi_previous_array: Array of previous phi values
        time_delta_array: Array of time deltas
        f_self: Self-frequency (same for all)

    Returns:
        Array of FCS values
    """
    if not all(
        len(arr) == len(phi_current_array)
        for arr in [phi_previous_array, time_delta_array]
    ):
        raise ValueError("All input arrays must have the same length")

    results = []
    for i in range(len(phi_current_array)):
        fcs = calculate_functional_coherence_score(
            phi_current=phi_current_array[i],
            phi_previous=phi_previous_array[i],
            time_delta=time_delta_array[i],
            f_self=f_self
        )
        results.append(fcs)

    return results


# WASM export metadata
WASM_EXPORTS = {
    # `calculate_phi_v2` is deprecated (see formulas.py) and is no longer
    # listed here: an export descriptor that advertises a legacy entry point is
    # a claim about the surface, not a note about it.
    "calculate_phi_v2_1": {
        "pure": True,
        "side_effects": False,
        "inputs": ["float", "float", "float", "float", "float", "float",
                   "float", "float", "float"],
        "output": "dict",
        "simd_ready": True,
    },
    "calculate_functional_coherence_score": {
        "pure": True,
        "side_effects": False,
        "inputs": ["float", "float", "float", "float"],
        "output": "float",
        "simd_ready": True,
    },
    "calculate_phi_v2_1_batch": {
        "pure": True,
        "side_effects": False,
        "inputs": ["Float32Array", "Float32Array", "Float32Array",
                   "Float32Array", "Float32Array", "Float32Array",
                   "Float32Array", "string"],
        "output": "Float32Array",
        "simd_ready": True,
        "optimized": True,
    },
}

