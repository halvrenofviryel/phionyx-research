# Installation Guide

**Phionyx Core SDK Installation**

---

## Prerequisites

- **Python**: 3.9 or higher
- **pip**: Latest version recommended
- **Operating System**: Linux, macOS, or Windows

---

## Installation Methods

### Method 1: pip (Recommended)

```bash
pip install phionyx-core
```

### Method 2: From Source

```bash
# Clone repository
git clone https://github.com/phionyx/phionyx-core.git
cd phionyx-core

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Method 3: From GitHub (Latest)

```bash
pip install git+https://github.com/phionyx/phionyx-core.git
```

---

## Dependencies

Phionyx Core SDK has the following dependencies:

### Core Dependencies

- **pydantic**: Data validation and settings management
- **numpy**: Numerical computations
- **typing-extensions**: Extended type hints

### Optional Dependencies

- **asyncpg**: PostgreSQL state store (if using PostgreSQL)
- **opentelemetry**: Telemetry and observability (if using OpenTelemetry)

### Development Dependencies

- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **ruff**: Code linting
- **black**: Code formatting

---

## Verification

After installation, verify the installation:

```python
import phionyx_core
print(phionyx_core.__version__)

# Test import
from phionyx_core import EchoOrchestrator, EchoState2
print("✅ Phionyx Core SDK installed successfully!")
```

---

## Configuration

### Environment Variables

Phionyx Core SDK uses environment variables for configuration:

```bash
# Optional: Set log level
export PHIONYX_LOG_LEVEL=INFO

# Optional: Enable OpenTelemetry
export PHIONYX_OPENTELEMETRY_ENABLED=true
```

### Profile Configuration

Copy example profiles from `config/templates/` and customize:

```bash
# Copy template
cp phionyx_core/config/templates/profile_templates.py my_profile.py

# Edit my_profile.py with your values
```

---

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'phionyx_core'`

**Solution**: Ensure you're using the correct Python environment:
```bash
python --version  # Should be 3.9+
which python      # Check Python path
pip install phionyx-core
```

**Issue**: `ImportError: cannot import name 'EchoOrchestrator'`

**Solution**: Ensure you're importing from the correct module:
```python
from phionyx_core import EchoOrchestrator  # Correct
# Not: from phionyx_core.orchestrator import EchoOrchestrator
```

**Issue**: PostgreSQL connection errors

**Solution**: Install asyncpg if using PostgreSQL:
```bash
pip install asyncpg
```

---

## Next Steps

After installation:

1. Read the [README.md](README.md) for quick start
2. Check [API Reference](docs/API_REFERENCE.md) for detailed API documentation
3. Review [Usage Examples](docs/EXAMPLES.md) for code examples
4. See [Configuration Guide](docs/CONFIGURATION.md) for configuration options

---

**Last Updated**: 2026-01-29

