"""Validate the example compliance-mapping row against the schema.

Usage::

    pip install jsonschema
    python docs/mappings/schema/validate.py

Returns exit code 0 on success, non-zero on validation failure.
"""
from __future__ import annotations

import json
import os
import sys


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(here, "compliance_mapping_row.schema.json")
    example_path = os.path.join(here, "example_row.json")

    with open(schema_path, encoding="utf-8") as fh:
        schema = json.load(fh)
    with open(example_path, encoding="utf-8") as fh:
        row = json.load(fh)

    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print("jsonschema not installed; run: pip install jsonschema", file=sys.stderr)
        return 2

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(row), key=lambda e: list(e.path))

    if errors:
        print(f"FAIL: {len(errors)} validation error(s) in example_row.json")
        for err in errors:
            path = ".".join(str(p) for p in err.path) or "<root>"
            print(f"  - {path}: {err.message}")
        return 1

    print(f"OK: example_row.json validates against compliance_mapping_row.schema.json")
    print(f"     framework            = {row['framework']} {row.get('framework_version', '')}")
    print(f"     identifier           = {row['framework_identifier']}")
    print(f"     coverage             = {row['coverage']} ({row.get('coverage_scope', '-')})")
    print(f"     mechanisms           = {len(row['phionyx_mechanism'])}")
    print(f"     evidence_items       = {len(row['evidence'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
