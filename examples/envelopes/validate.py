"""Validate `governed_response.json` against `governed_response.schema.json`.

Run from the repo root:

    pip install jsonschema
    python examples/envelopes/validate.py

Exits 0 if the canonical envelope conforms. Exits 1 with a precise
JSON-Pointer location on failure. Use the same script against any other
envelope your pipeline emits:

    python examples/envelopes/validate.py path/to/your/envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent


def main(argv: list[str]) -> int:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print(
            "jsonschema is not installed. Install it with:\n"
            "    pip install jsonschema",
            file=sys.stderr,
        )
        return 2

    target = Path(argv[1]) if len(argv) > 1 else HERE / "governed_response.json"
    schema_path = HERE / "governed_response.schema.json"

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    instance = json.loads(target.read_text(encoding="utf-8"))

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    if not errors:
        print(f"✓ {target.relative_to(HERE.parent.parent)} validates against {schema_path.name}")
        return 0

    print(f"✗ {target} failed schema validation:", file=sys.stderr)
    for err in errors:
        path = "/" + "/".join(str(p) for p in err.absolute_path)
        print(f"  {path}: {err.message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
