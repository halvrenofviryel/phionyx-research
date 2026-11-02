"""One-command offline tests plus deterministic output drift checking."""

import argparse
import json
import sys
import unittest

sys.dont_write_bytecode = True

from experiment import generate, markdown  # noqa: E402
from profile import ROOT  # noqa: E402


def main() -> int:
    """Test first, then write or check the committed reproducible artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="Regenerate results after tests pass")
    mode.add_argument("--check", action="store_true", help="Verify committed results (default)")
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        return 1
    data = generate()
    outputs = {
        "results.json": json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        "RESULTS.md": markdown(data),
    }
    for name, content in outputs.items():
        path = ROOT / name
        if args.write:
            path.write_text(content, encoding="utf-8")
        elif not path.exists() or path.read_bytes() != content.encode("utf-8"):
            print("OUTPUT DRIFT:", name, file=sys.stderr)
            return 1
    print(
        json.dumps(
            {
                "tests": result.testsRun,
                "scenario_routes": len(data["scenarios"]),
                "matrix_cells": len(data["matrix"]),
                "matrix_counts": data["matrix_counts"],
                "scenario_counts": data["scenario_counts"],
                "outputs": "WRITTEN" if args.write else "MATCH",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
