"""CLI: Show experiment results.

Usage:
    python -m phionyx_core.research_engine.cli.show_results [options]

Options:
    --session ID     Show results for specific session
    --last N         Show last N experiments (default: 20)
    --status STATUS  Filter by status (rejected|archived|candidate|promoted|gold)
    --surface FILE   Filter by surface file
"""
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Phionyx Research Engine — Show experiment results"
    )
    parser.add_argument("--session", help="Filter by session ID")
    parser.add_argument("--last", type=int, default=20, help="Show last N experiments")
    parser.add_argument("--status", help="Filter by status")
    parser.add_argument("--surface", help="Filter by surface file")
    parser.add_argument("--data-dir", default="data/research_engine", help="Data directory")

    args = parser.parse_args()

    from ..store.experiment_store import ExperimentStore
    store = ExperimentStore(args.data_dir)

    records = store.get_all()

    if args.session:
        records = [r for r in records if r.get("session_id") == args.session]
    if args.status:
        records = [r for r in records if r.get("status") == args.status]
    if args.surface:
        records = [r for r in records if r.get("surface_file") == args.surface]

    records = records[-args.last:]

    if not records:
        print("No experiments found.")
        return 0

    print(f"{'ID':<40} {'Decision':<10} {'Status':<12} {'CQS Delta':>10} {'Surface'}")
    print("-" * 100)

    for r in records:
        exp_id = r.get("experiment_id", "?")[:38]
        decision = r.get("decision", "?")
        status = r.get("status", "?")
        cqs_delta = r.get("cqs_delta", 0.0)
        surface = r.get("surface_file", "?")

        # Status symbol
        symbol = {"keep": "+", "revert": "-", "park": "o", "crash": "!"}.get(decision, "?")

        print(f"{symbol} {exp_id:<38} {decision:<10} {status:<12} {cqs_delta:>+10.6f} {surface}")

    print(f"\nTotal: {len(records)} experiments")
    kept = sum(1 for r in records if r.get("decision") == "keep")
    reverted = sum(1 for r in records if r.get("decision") == "revert")
    print(f"Kept: {kept} | Reverted: {reverted}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
