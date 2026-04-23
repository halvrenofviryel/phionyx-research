"""CLI: Show current baseline metrics.

Usage:
    python -m phionyx_core.research_engine.cli.show_baseline
"""
import argparse
import json
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Phionyx Research Engine — Show current baseline"
    )
    parser.add_argument("--data-dir", default="data/research_engine", help="Data directory")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    from ..store.baseline_store import BaselineStore
    store = BaselineStore(args.data_dir)

    baseline = store.load()

    if baseline is None:
        print("No baseline exists. Run a session with --baseline-only first.")
        return 1

    if args.json:
        print(json.dumps(baseline, indent=2))
        return 0

    print("Phionyx Research Engine — Current Baseline")
    print("=" * 50)
    print(f"Timestamp: {baseline.get('timestamp', '?')}")
    print(f"Git commit: {baseline.get('git_commit', '?')[:12]}")
    print()

    metrics = baseline.get("metrics", {})
    print("Metrics:")
    for key, value in sorted(metrics.items()):
        if isinstance(value, float):
            print(f"  {key:<35} {value:.6f}")
        else:
            print(f"  {key:<35} {value}")

    print()
    surface_values = baseline.get("surface_values", {})
    if surface_values:
        print("Surface Values:")
        for key, value in sorted(surface_values.items()):
            print(f"  {key:<35} {value}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
