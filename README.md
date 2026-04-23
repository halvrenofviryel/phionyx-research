# Phionyx Core SDK

**Deterministic AI Runtime Architecture**

[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](https://github.com/halvrenofviryel/phionyx-research)
[![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Phionyx Core SDK is a deterministic AI runtime derived from the Echoism ontological framework. It treats LLM outputs as noisy sensor measurements rather than direct decisions, enabling reproducible, auditable, and governance-grade AI systems.

---

## 🎯 Key Features

- **Deterministic Processing**: Reproducible behavior through structured state management
- **Structured State Vector**: Deterministic state evolution (A, V, H, dA, dV, t_local, t_global)
- **Cognitive Resonance Model**: Hybrid resonance calculation (Phi) — derived, non-persistent
- **Semantic Time-Based Memory**: Impact-weighted cache eviction (+24% vs LRU, +72% vs FIFO)
- **Safety & Governance Layer**: Pre-response control, cognitive envelopes, participant isolation
- **46-Block Canonical Pipeline**: Deterministic evaluation blocks (v3.8.0)
- **Profile Management**: Configurable profiles for different use cases (edu, game, clinical)

---

## 📚 Documentation

- **Architecture Paper**: Phionyx: A Deterministic AI Runtime Architecture — arXiv preprint (submission pending)
- **Evaluation Standard**: Phionyx Evaluation Standard v0.1 — Vendor-independent evaluation framework (publication pending)

---

## 🚀 Quick Start

### Installation

```bash
pip install phionyx-core
```

### Basic Usage

```python
from phionyx_core import EchoOrchestrator, EchoState2, OrchestratorServices

# Initialize orchestrator
services = OrchestratorServices()
orchestrator = EchoOrchestrator(services=services)

# Create initial state
state = EchoState2(
    A=0.5,  # Arousal
    V=0.0,  # Valence
    H=0.3,  # Entropy
    dA=0.0,
    dV=0.0,
    t_local=0.0,
    t_global=0.0
)

# Execute pipeline
result = orchestrator.execute_pipeline(
    input_text="Hello, how are you?",
    initial_state=state
)
```

---

## 🏗️ Architecture

Phionyx Core implements three integrated layers:

### 1. Deterministic Cognitive Kernel (Layer 1)

- **46-block canonical pipeline** (contract v3.8.0) for cognitive evaluation with state-driven response revision
- **Structured state management** (A, V, H, dA, dV, t_local, t_global)
- **Hybrid Resonance Model** for Phi calculation
- **Dynamic entropy** using Kolmogorov Complexity (Zlib)
- **Deterministic failure classification** and recovery

**Reference**: arXiv paper Section 4

### 2. Unified Safety & Governance Layer (Layer 2)

- **Pre-response control** with 4-gate structure (Outbound, Merge, Release, Data)
- **Cognitive envelopes** for secure agent communication
- **EthicsVector** and amplitude damping
- **Non-persistence doctrine** for derived metrics
- **Participant-scoped cognitive isolation**

**Reference**: arXiv paper Section 5

### 3. Semantic Time-Based Memory System (Layer 3)

- **Semantic time vector** (t_local, t_global)
- **Monotonic clock** mechanism (DT_FLOOR = 0.1s)
- **Impact-weighted cache eviction** using cognitive impact
- **Hybrid Resonance Model** for Phi decay
- **RAG service integration** with semantic time decay

**Reference**: arXiv paper Section 6

---

## 📖 Core Concepts

### Structured State

The system state is represented as a structured state vector:

```python
state = EchoState2(
    A=0.5,      # Arousal (0.0-1.0)
    V=0.0,      # Valence (-1.0 to 1.0)
    H=0.3,      # Entropy (0.0-1.0)
    dA=0.0,     # Arousal derivative
    dV=0.0,     # Valence derivative
    t_local=0.0,  # Semantic time (local)
    t_global=0.0  # Semantic time (global)
)
```

### Phi (Cognitive Resonance)

Phi represents the quality of cognitive resonance:

```python
from phionyx_core.physics.formulas import calculate_phi_v2_1

phi_result = calculate_phi_v2_1(
    valence=0.0,
    arousal=0.5,
    amplitude=5.0,
    time_delta=0.1,
    gamma=0.15,
    stability=0.9,
    entropy=0.3,
    w_c=0.75,  # Cognitive weight
    w_p=0.25   # Physical weight
)

phi = phi_result["phi"]  # 0.0-1.0
```

### Pipeline Blocks

The canonical pipeline consists of 46 blocks (contract v3.8.0; v3.7.0 remains loadable for runtime coexistence):

```python
from phionyx_core.contracts.telemetry import get_canonical_blocks

blocks = get_canonical_blocks()             # defaults to current version (v3.8.0)
# Returns: List of 46 block IDs in canonical order

legacy = get_canonical_blocks(version="3.7.0")  # 45 blocks, pre-revision-gate
```

**v3.8.0 additions:**

- New block: `response_revision_gate` (position 41, immediately before `response_build`). Consumes final-turn state (phi, entropy, confidence, arbitration conflict, drift, ethics, CEP flags) and emits a deterministic `revision_directive`: `pass` | `damp` | `rewrite` | `regenerate` | `reject`.
- Reordered blocks: `phi_computation`, `entropy_computation`, `confidence_fusion`, `arbitration_resolve` now run **before** `response_build` (closing the state→response feedback loop that previously carried a one-turn lag).
- Orchestrator: bounded narrative regenerate retry (max 1, deterministic seed, state-update idempotent).
- `AuditRecord` schema: optional `claim_refs` + `revision_directive` fields (hash-chain compatible with legacy records).

---

## 🔧 Configuration

### Profile Management

Phionyx Core supports configurable profiles:

```python
from phionyx_core import ProfileManager, get_active_profile

# Load profile
manager = ProfileManager()
profile = manager.load_profile("edu")  # or "game", "clinical"

# Get active profile
active = get_active_profile()
```

### Template Configurations

Example configurations are available in `phionyx_core/config/templates/`:

- `profile_templates.py` - Example profile configurations
- `kpi_thresholds_template.yaml` - Example KPI thresholds
- `physics_profiles_template.yaml` - Example physics profiles

**Note**: Replace example values with your own based on your use case requirements.

---

## 📊 Evaluation Framework

Phionyx Core implements the behavioral assessment framework described in the technical book:

- **6 Behavioral Assessment Axes**: Temporal Consistency, Behavioral Variance, Context Sensitivity, Decision Reversibility, Silent Failure Tendency, Behavior Boundary Violation
- **Determinism Grading (D0-D3)**: Classification from non-deterministic to fully deterministic
- **Evaluation Levels (L0-L3)**: From unmeasured to governance-grade

**Reference**: Phionyx Evaluation Standard v0.1

---

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=phionyx_core tests/
```

---

## 📝 API Reference

### Main Classes

- **`EchoOrchestrator`**: Main orchestrator for pipeline execution
- **`EchoState2`**: Canonical state model
- **`PipelineBlock`**: Base class for pipeline blocks
- **`ProfileManager`**: Profile management and configuration

### Physics Functions

- **`calculate_phi_v2_1()`**: Hybrid Resonance Model
- **`calculate_dynamic_entropy_v3()`**: Dynamic entropy calculation
- **`calculate_text_entropy_zlib()`**: Kolmogorov Complexity (Zlib)

### Utilities

- **`get_canonical_blocks()`**: Get canonical block order (46 blocks in v3.8.0; pass `version="3.7.0"` for legacy 45-block order)

See [API Reference Documentation](phionyx_core/docs/API_REFERENCE.md) for detailed API documentation.

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

**AGPL-3.0 License** — See [LICENSE](LICENSE) file for details.

**Dual-License Model**: The Core SDK is open source under AGPL-3.0. If the copyleft obligations of AGPL-3.0 are not suitable for your use case, a commercial license is available. Patent rights are retained by Phionyx Research. See [PATENT_NOTICE.md](PATENT_NOTICE.md) and [LICENSE_STRATEGY.md](LICENSE_STRATEGY.md) for details.

---

## 🔗 Links

- **Website**: https://phionyx.ai
- **arXiv Paper**: Submission pending
- **Evaluation Standard**: Publication pending
- **GitHub**: https://github.com/halvrenofviryel/phionyx-research

---

## 📚 References

1. **Phionyx: A Deterministic AI Runtime Architecture with Structured State Management and Pre-Response Governance**  
   Ali Toygar Abak. Phionyx Research, April 2026.

2. **Phionyx Evaluation Standard v0.1**  
   Ali Toygar Abak. Phionyx Research, 2026.

---

## 🙏 Acknowledgments

Phionyx Core SDK is derived from the Echoism ontological framework. It introduces a governance-first approach to AI engineering: treating LLM outputs as noisy sensor measurements rather than direct decisions.

---

**Last Updated**: 2026-04-23  
**Version**: 0.2.0

