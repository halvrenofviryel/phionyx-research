# Contributing to Phionyx Core SDK

Thank you for your interest in contributing to Phionyx Core SDK!

---

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Follow the project's coding standards

---

## Getting Started

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/your-username/phionyx-core.git
   cd phionyx-core
   ```
3. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## Development Setup

```bash
# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run linting
ruff check phionyx_core/
black phionyx_core/
```

---

## Coding Standards

### Python Style

- Follow **PEP 8** style guide
- Use **type hints** for all function signatures
- Write **docstrings** for all public functions and classes
- Use **Google-style** or **NumPy-style** docstrings

### Code Formatting

- Use **Black** for code formatting
- Use **Ruff** for linting
- Maximum line length: **100 characters**

### Example

```python
def calculate_phi(
    entropy: float,
    stability: float,
    valence: float = 0.0
) -> float:
    """
    Calculate Phi (cognitive resonance) using Hybrid Resonance Model.
    
    Args:
        entropy: System entropy (0.0-1.0)
        stability: System stability (0.0-1.0)
        valence: Emotional valence (-1.0 to 1.0), default 0.0
    
    Returns:
        Phi value (0.0-1.0), where higher values indicate stronger resonance
    
    Raises:
        ValueError: If entropy or stability are outside valid range
    """
    # Implementation...
```

---

## Testing

### Test Requirements

- All new code must include tests
- Aim for **>80% code coverage**
- Tests should be **deterministic** and **fast**

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=phionyx_core tests/

# Run specific test file
pytest tests/test_physics.py
```

### Writing Tests

```python
import pytest
from phionyx_core.physics.formulas import calculate_phi_v2_1

def test_calculate_phi():
    """Test Phi calculation."""
    result = calculate_phi_v2_1(
        valence=0.0,
        arousal=0.5,
        amplitude=5.0,
        time_delta=0.1,
        gamma=0.15,
        stability=0.9,
        entropy=0.3,
        w_c=0.75,
        w_p=0.25
    )
    
    assert 0.0 <= result["phi"] <= 1.0
    assert "phi_cognitive" in result
    assert "phi_physical" in result
```

---

## Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new features
3. **Ensure all tests pass**
4. **Update CHANGELOG.md** with your changes
5. **Create pull request** with clear description

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

---

## Documentation

### Docstring Standards

- **Module-level**: Describe the module's purpose
- **Class-level**: Describe the class and its main methods
- **Function-level**: Describe parameters, returns, and raises

### Example

```python
"""
Module for physics calculations.

This module contains pure mathematical functions for calculating
thermodynamic state metrics, entropy, and resonance.
"""

class PhysicsCalculator:
    """
    Calculator for physics metrics.
    
    This class provides methods for calculating Phi, entropy,
    and other thermodynamic state metrics.
    """
    
    def calculate_phi(self, state: EchoState2) -> float:
        """
        Calculate Phi from state.
        
        Args:
            state: EchoState2 instance
        
        Returns:
            Phi value (0.0-1.0)
        """
        # Implementation...
```

---

## Commit Messages

Use clear, descriptive commit messages:

```
feat: Add new physics calculation function
fix: Correct entropy calculation bug
docs: Update API reference documentation
test: Add tests for state management
refactor: Simplify orchestrator logic
```

---

## Questions?

- **Issues**: Open an issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Email**: contact@phionyx.ai

---

Thank you for contributing to Phionyx Core SDK!

---

**Last Updated**: 2026-01-29

