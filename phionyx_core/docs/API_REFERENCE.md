# API Reference

**Phionyx Core SDK API Documentation**

---

## Table of Contents

1. [Main Classes](#main-classes)
2. [State Management](#state-management)
3. [Physics Functions](#physics-functions)
4. [Pipeline Blocks](#pipeline-blocks)
5. [Profile Management](#profile-management)
6. [Utilities](#utilities)

---

## Main Classes

### EchoOrchestrator

Main orchestrator for pipeline execution.

```python
from phionyx_core import EchoOrchestrator, OrchestratorServices

orchestrator = EchoOrchestrator(services=services)
```

#### Methods

**`execute_pipeline(input_text: str, initial_state: EchoState2, ...) -> BlockResult`**

Execute the canonical pipeline with given input and initial state.

**Parameters:**
- `input_text` (str): Input text to process
- `initial_state` (EchoState2): Initial thermodynamic state
- `context` (Optional[Dict]): Additional context
- `profile` (Optional[str]): Profile name to use

**Returns:**
- `BlockResult`: Pipeline execution result with final state

**Example:**
```python
result = orchestrator.execute_pipeline(
    input_text="Hello, how are you?",
    initial_state=state
)
```

---

### EchoState2

Canonical state model representing thermodynamic state.

```python
from phionyx_core import EchoState2

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

#### Properties

- **`A`** (float): Arousal (0.0-1.0)
- **`V`** (float): Valence (-1.0 to 1.0)
- **`H`** (float): Entropy (0.0-1.0)
- **`dA`** (float): Arousal derivative
- **`dV`** (float): Valence derivative
- **`t_local`** (float): Semantic time (local)
- **`t_global`** (float): Semantic time (global)
- **`resonance`** (float): Computed resonance (0.0-1.0)
- **`stability`** (float): Computed stability (0.0-1.0)

#### Methods

**`to_dict() -> Dict`**

Convert state to dictionary.

**`from_dict(data: Dict) -> EchoState2`**

Create state from dictionary.

---

### PipelineBlock

Base class for pipeline blocks.

```python
from phionyx_core import PipelineBlock, BlockContext, BlockResult

class MyBlock(PipelineBlock):
    def execute(self, context: BlockContext) -> BlockResult:
        # Block implementation
        return BlockResult(success=True, state=context.state)
```

#### Methods

**`execute(context: BlockContext) -> BlockResult`**

Execute the block with given context.

**Parameters:**
- `context` (BlockContext): Block execution context

**Returns:**
- `BlockResult`: Block execution result

---

## State Management

### EchoState2Plus

Extended state model with additional metrics.

```python
from phionyx_core import EchoState2Plus

state_plus = EchoState2Plus(
    A=0.5,
    V=0.0,
    H=0.3,
    # ... base state fields ...
    # Additional metrics
    coherence=0.8,
    dominance=0.6
)
```

---

## Physics Functions

### calculate_phi_v2_1

Calculate Phi (cognitive resonance) using Hybrid Resonance Model.

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

**Returns:**
- `Dict[str, float]`: Dictionary with `phi`, `phi_cognitive`, `phi_physical`, `weight_cognitive`, `weight_physical`

---

### calculate_dynamic_entropy_v3

Calculate dynamic entropy using Kolmogorov Complexity.

```python
from phionyx_core.physics.dynamics import calculate_dynamic_entropy_v3

entropy = calculate_dynamic_entropy_v3(
    input_text="Hello, how are you?",
    phi_variance=0.0,
    negative_emotion_ratio=0.0
)
```

**Returns:**
- `float`: Entropy value (0.0-1.0)

---

### calculate_text_entropy_zlib

Calculate text entropy using Zlib compression (Kolmogorov Complexity approximation).

```python
from phionyx_core.physics.text_physics import calculate_text_entropy_zlib

entropy = calculate_text_entropy_zlib("Hello, how are you?")
```

**Returns:**
- `float`: Entropy value (0.0-1.0)

---

## Pipeline Blocks

### get_canonical_blocks

Get canonical block order (46 blocks, contract v3.8.0).

```python
from phionyx_core.contracts.telemetry import get_canonical_blocks

blocks = get_canonical_blocks()
# Returns: List[str] of 46 block IDs
```

**Returns:**
- `List[str]`: List of 46 block IDs in canonical order

---

## Profile Management

### ProfileManager

Profile management and configuration.

```python
from phionyx_core import ProfileManager

manager = ProfileManager()
profile = manager.load_profile("edu")
```

#### Methods

**`load_profile(name: str) -> Profile`**

Load profile by name.

**Parameters:**
- `name` (str): Profile name ("edu", "game", "clinical")

**Returns:**
- `Profile`: Profile configuration

---

### get_active_profile

Get currently active profile.

```python
from phionyx_core import get_active_profile

profile = get_active_profile()
```

**Returns:**
- `Profile`: Currently active profile

---

## Utilities

### OrchestratorServices

Service dependencies for orchestrator.

```python
from phionyx_core import OrchestratorServices

services = OrchestratorServices(
    processor=processor,
    response_generator=generator,
    phi_engine=phi_engine,
    # ... other services
)
```

#### Attributes

- `processor`: Engine processor
- `response_generator`: Response generator
- `phi_engine`: Phi calculation engine
- `entropy_engine`: Entropy calculation engine
- `emotion_estimator`: Emotion estimation service
- `state_store`: State persistence store
- `time_managers`: Time management services

---

## Type Definitions

### PhysicsInput

Input for physics calculations.

```python
from phionyx_core.physics.types import PhysicsInput

input_data = PhysicsInput(
    text="Hello",
    state=state,
    time_delta=0.1
)
```

### PhysicsOutput

Output from physics calculations.

```python
from phionyx_core.physics.types import PhysicsOutput

output = PhysicsOutput(
    phi=0.5,
    entropy=0.3,
    resonance=0.7
)
```

### PhysicsState

Physics state representation.

```python
from phionyx_core.physics.types import PhysicsState

physics_state = PhysicsState(
    A=0.5,
    V=0.0,
    H=0.3
)
```

---

## Error Handling

### Common Exceptions

**`ValueError`**: Invalid parameter values (e.g., entropy outside 0.0-1.0 range)

**`TypeError`**: Invalid type for parameter

**`RuntimeError`**: Runtime errors during pipeline execution

---

## Examples

See [Usage Examples](EXAMPLES.md) for detailed code examples.

---

**Last Updated**: 2026-01-29

