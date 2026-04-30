"""
WASM-Ready Physics Functions
=============================

Wrapper layer for WASM compilation compatibility.
Ensures all functions are pure, typed, and SIMD-friendly.
"""


from .formulas import (
    calculate_functional_coherence_score,
    calculate_phi_v2,
)

# Type aliases for WASM compatibility
Float32Array = list[float]
Float64Array = list[float]


def calculate_phi_v2_batch(
    entropy_array: Float32Array,
    stability_array: Float32Array,
    amplitude_array: Float32Array,
    time_delta_array: Float32Array,
    gamma_array: Float32Array,
    context_mode: str = "DEFAULT"
) -> Float32Array:
    """
    Batch version of calculate_phi_v2 for SIMD optimization.

    Args:
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
        for arr in [stability_array, amplitude_array, time_delta_array, gamma_array]
    ):
        raise ValueError("All input arrays must have the same length")

    results = []
    for i in range(len(entropy_array)):
        result = calculate_phi_v2(
            entropy=entropy_array[i],
            stability=stability_array[i],
            amplitude=amplitude_array[i],
            time_delta=time_delta_array[i],
            gamma=gamma_array[i],
            context_mode=context_mode
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
    "calculate_phi_v2": {
        "pure": True,
        "side_effects": False,
        "inputs": ["float", "float", "float", "float", "float", "string"],
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
    "calculate_phi_v2_batch": {
        "pure": True,
        "side_effects": False,
        "inputs": ["Float32Array", "Float32Array", "Float32Array", "Float32Array", "Float32Array", "string"],
        "output": "Float32Array",
        "simd_ready": True,
        "optimized": True,
    },
}

