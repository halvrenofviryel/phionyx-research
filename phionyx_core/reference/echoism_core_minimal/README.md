# Echoism Core Minimal - Reference Implementation

**⚠️ WARNING: This is a didactic/reference implementation, NOT the production SDK.**

This is a minimal, standalone implementation of Echoism Core v1.1 principles for educational purposes.

## Purpose

- **Didactic**: Learn Echoism Core v1.1 concepts
- **Proof-of-concept**: Demonstrate core principles
- **Standalone**: Does NOT import production SDK modules
- **Target**: 400-600 LOC

## Structure

- `state.py`: EchoState2Plus implementation
- `ukf.py`: UKF filter (using FilterPy)
- `trace.py`: Trace/echo ontology
- `ethics.py`: Ethics vector and enforcement
- `main.py`: Example usage

## Dependencies

- `filterpy`: UKF implementation
- `numpy`: Numerical operations
- `sqlite3`: Event storage (standard library)

## Usage

```python
python main.py
```

## Note

This is NOT the production SDK. For production use, see `core-state`, `core-physics`, `core-memory` modules.

