# Usage Examples

**Phionyx Core SDK Code Examples**

---

## Table of Contents

1. [Basic Usage](#basic-usage)
2. [State Management](#state-management)
3. [Pipeline Execution](#pipeline-execution)
4. [Physics Calculations](#physics-calculations)
5. [Profile Configuration](#profile-configuration)
6. [Custom Pipeline Blocks](#custom-pipeline-blocks)

---

## Basic Usage

### Simple Pipeline Execution

```python
from phionyx_core import EchoOrchestrator, EchoState2, OrchestratorServices

# Initialize services
services = OrchestratorServices()
orchestrator = EchoOrchestrator(services=services)

# Create initial state
state = EchoState2(
    A=0.5,      # Arousal
    V=0.0,      # Valence
    H=0.3,      # Entropy
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

print(f"Final state: {result.state}")
print(f"Success: {result.success}")
```

---

## State Management

### Creating and Updating State

```python
from phionyx_core import EchoState2

# Create initial state
state = EchoState2(
    A=0.5,
    V=0.0,
    H=0.3,
    dA=0.0,
    dV=0.0,
    t_local=0.0,
    t_global=0.0
)

# Access properties
print(f"Arousal: {state.A}")
print(f"Valence: {state.V}")
print(f"Entropy: {state.H}")

# Computed properties
print(f"Resonance: {state.resonance}")
print(f"Stability: {state.stability}")

# Convert to dictionary
state_dict = state.to_dict()

# Create from dictionary
new_state = EchoState2.from_dict(state_dict)
```

### State Evolution

```python
from phionyx_core import EchoState2

# Initial state
state = EchoState2(A=0.5, V=0.0, H=0.3, dA=0.0, dV=0.0, t_local=0.0, t_global=0.0)

# After processing
state.A = 0.6  # Arousal increased
state.V = 0.2  # Valence became positive
state.H = 0.4  # Entropy increased
state.t_local += 0.1  # Time advanced

print(f"Updated state: {state}")
```

---

## Pipeline Execution

### Executing with Profile

```python
from phionyx_core import EchoOrchestrator, EchoState2, OrchestratorServices

services = OrchestratorServices()
orchestrator = EchoOrchestrator(services=services)

state = EchoState2(A=0.5, V=0.0, H=0.3, dA=0.0, dV=0.0, t_local=0.0, t_global=0.0)

# Execute with specific profile
result = orchestrator.execute_pipeline(
    input_text="How can I help you today?",
    initial_state=state,
    profile="edu"  # Use educational profile
)
```

### Executing with Context

```python
from phionyx_core import EchoOrchestrator, EchoState2, OrchestratorServices

services = OrchestratorServices()
orchestrator = EchoOrchestrator(services=services)

state = EchoState2(A=0.5, V=0.0, H=0.3, dA=0.0, dV=0.0, t_local=0.0, t_global=0.0)

# Execute with additional context
context = {
    "user_id": "user123",
    "session_id": "session456",
    "metadata": {"source": "web", "language": "en"}
}

result = orchestrator.execute_pipeline(
    input_text="What is the weather today?",
    initial_state=state,
    context=context
)
```

---

## Physics Calculations

### Calculating Phi (Cognitive Resonance)

```python
from phionyx_core.physics.formulas import calculate_phi_v2_1

# Calculate Phi using Hybrid Resonance Model
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

print(f"Phi: {phi_result['phi']}")
print(f"Phi Cognitive: {phi_result['phi_cognitive']}")
print(f"Phi Physical: {phi_result['phi_physical']}")
print(f"Weight Cognitive: {phi_result['weight_cognitive']}")
print(f"Weight Physical: {phi_result['weight_physical']}")
```

### Calculating Dynamic Entropy

```python
from phionyx_core.physics.dynamics import calculate_dynamic_entropy_v3

# Calculate dynamic entropy
entropy = calculate_dynamic_entropy_v3(
    input_text="Hello, how are you today?",
    phi_variance=0.0,
    negative_emotion_ratio=0.0
)

print(f"Entropy: {entropy}")
```

### Calculating Text Entropy (Zlib)

```python
from phionyx_core.physics.text_physics import calculate_text_entropy_zlib

# Calculate text entropy using Kolmogorov Complexity (Zlib)
entropy = calculate_text_entropy_zlib("Hello, how are you?")

print(f"Text Entropy: {entropy}")
```

---

## Profile Configuration

### Loading Profiles

```python
from phionyx_core import ProfileManager

# Initialize profile manager
manager = ProfileManager()

# Load profile
edu_profile = manager.load_profile("edu")
game_profile = manager.load_profile("game")
clinical_profile = manager.load_profile("clinical")

print(f"Edu Profile: {edu_profile}")
```

### Using Active Profile

```python
from phionyx_core import get_active_profile

# Get currently active profile
active_profile = get_active_profile()

print(f"Active Profile: {active_profile.name}")
print(f"Profile Config: {active_profile.config}")
```

### Custom Profile

```python
from phionyx_core import ProfileManager, Profile

# Create custom profile
custom_profile = Profile(
    name="custom",
    config={
        "physics": "v2.1",
        "memory": "standard",
        "physics_v2_1": {
            "valence": 0.1,
            "arousal": 0.6,
            "amplitude": 6.0,
            "entropy": 0.35,
            "stability": 0.85,
            "gamma": 0.18,
            "w_c": 0.7,
            "w_p": 0.3
        }
    }
)

# Register profile
manager = ProfileManager()
manager.register_profile(custom_profile)
```

---

## Custom Pipeline Blocks

### Creating a Custom Block

```python
from phionyx_core import PipelineBlock, BlockContext, BlockResult

class MyCustomBlock(PipelineBlock):
    """Custom pipeline block example."""
    
    def __init__(self, block_id: str):
        super().__init__(block_id)
    
    def execute(self, context: BlockContext) -> BlockResult:
        """Execute the custom block."""
        # Access input
        input_text = context.input_text
        state = context.state
        
        # Perform custom processing
        # ... your logic here ...
        
        # Update state if needed
        state.A = 0.6  # Example: update arousal
        
        # Return result
        return BlockResult(
            success=True,
            state=state,
            output={"custom_output": "value"}
        )
```

### Using Custom Block

```python
from phionyx_core import EchoOrchestrator, OrchestratorServices
from my_blocks import MyCustomBlock

# Create custom block
custom_block = MyCustomBlock(block_id="my_custom_block")

# Register block (implementation depends on orchestrator)
# orchestrator.register_block(custom_block)
```

---

## Advanced Examples

### Multi-Turn Conversation

```python
from phionyx_core import EchoOrchestrator, EchoState2, OrchestratorServices

services = OrchestratorServices()
orchestrator = EchoOrchestrator(services=services)

# Initial state
state = EchoState2(A=0.5, V=0.0, H=0.3, dA=0.0, dV=0.0, t_local=0.0, t_global=0.0)

# Turn 1
result1 = orchestrator.execute_pipeline(
    input_text="Hello",
    initial_state=state
)
state1 = result1.state

# Turn 2
result2 = orchestrator.execute_pipeline(
    input_text="How are you?",
    initial_state=state1
)
state2 = result2.state

# Turn 3
result3 = orchestrator.execute_pipeline(
    input_text="What's the weather?",
    initial_state=state2
)

print(f"Final state after 3 turns: {result3.state}")
```

### State Persistence

```python
from phionyx_core import EchoState2
from phionyx_core.persistence import InMemoryStateStore

# Create state store
state_store = InMemoryStateStore()

# Save state
state = EchoState2(A=0.5, V=0.0, H=0.3, dA=0.0, dV=0.0, t_local=0.0, t_global=0.0)
state_store.save("session123", state)

# Load state
loaded_state = state_store.load("session123")
print(f"Loaded state: {loaded_state}")
```

---

## Error Handling

### Handling Pipeline Errors

```python
from phionyx_core import EchoOrchestrator, EchoState2, OrchestratorServices

services = OrchestratorServices()
orchestrator = EchoOrchestrator(services=services)

state = EchoState2(A=0.5, V=0.0, H=0.3, dA=0.0, dV=0.0, t_local=0.0, t_global=0.0)

try:
    result = orchestrator.execute_pipeline(
        input_text="Hello",
        initial_state=state
    )
    
    if result.success:
        print(f"Success: {result.state}")
    else:
        print(f"Pipeline failed: {result.error}")
        
except ValueError as e:
    print(f"Invalid parameter: {e}")
except RuntimeError as e:
    print(f"Runtime error: {e}")
```

---

## Best Practices

1. **Always initialize state properly**: Set all required fields (A, V, H, dA, dV, t_local, t_global)

2. **Use appropriate profiles**: Select profiles (edu, game, clinical) based on your use case

3. **Handle errors gracefully**: Wrap pipeline execution in try-except blocks

4. **Persist state between turns**: Use state stores for multi-turn conversations

5. **Monitor state evolution**: Track state changes to understand system behavior

---

**Last Updated**: 2026-01-29

