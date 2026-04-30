"""CLI: Run a research engine experiment session.

Usage:
    python -m phionyx_core.research_engine.cli.run_session [options]

Options:
    --surface FILE     Surface file to optimize (default: phionyx_core/physics/constants.py)
    --suite NAME       Benchmark suite (default: core_v1)
    --strategy TYPE    Hypothesis strategy: grid|random|boundary|all (default: grid)
    --max-experiments N  Maximum experiments (default: 50)
    --max-hours H      Maximum hours (default: 4)
    --dry-run          Preview without executing
"""
import argparse
import re
import sys
from pathlib import Path

import yaml


def load_surfaces(surfaces_file: str | None = None) -> list[dict]:
    """Load surface definitions from YAML."""
    if surfaces_file is None:
        # Default path relative to research engine
        surfaces_file = str(
            Path(__file__).parent.parent / "mutation" / "surfaces.yaml"
        )

    path = Path(surfaces_file)
    if not path.exists():
        print(f"Error: surfaces file not found: {surfaces_file}")
        sys.exit(1)

    with open(path) as f:
        data = yaml.safe_load(f)

    return data.get("surfaces", [])


def _read_actual_value(
    source_file: str, param_name: str, default: float, repo_dir: Path | None = None,
) -> float:
    """Read the actual current value of a parameter from its source file.

    This prevents desync between surfaces.yaml 'current' fields and actual
    source code — which happens after RE KEEPs or manual edits.
    """
    if repo_dir is None:
        repo_dir = Path(__file__).resolve().parent
        while repo_dir != repo_dir.parent:
            if (repo_dir / ".git").exists():
                break
            repo_dir = repo_dir.parent

    path = repo_dir / source_file
    if not path.exists():
        return default

    content = path.read_text()
    match = re.search(
        rf"^{re.escape(param_name)}\s*=\s*([\d.]+)",
        content,
        re.MULTILINE,
    )
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return default
    return default


def get_surface_params(surfaces: list[dict], file_path: str) -> list[dict]:
    """Get parameter definitions for a specific surface file.

    Reads actual current values from source files instead of relying on
    surfaces.yaml 'current' field, which can desync after RE optimizations.
    """
    for surface in surfaces:
        if surface.get("file") == file_path and surface.get("tier") == "A":
            params = surface.get("parameters", [])
            result = []
            for p in params:
                actual = _read_actual_value(
                    file_path, p["name"], p["current"],
                )
                # Convert to int for integer params (prevents regex mismatch: 2.0 vs 2)
                if p.get("type") == "int":
                    actual = int(actual)
                result.append({
                    "name": p["name"],
                    "type": p.get("type", "float"),
                    "current": actual,
                    "range_min": p["range_min"],
                    "range_max": p["range_max"],
                    "step": p["step"],
                })
            return result
    return []


def main():
    parser = argparse.ArgumentParser(
        description="Phionyx Research Engine — Run experiment session"
    )
    parser.add_argument(
        "--surface", default="phionyx_core/physics/constants.py",
        help="Surface file to optimize"
    )
    parser.add_argument(
        "--suite", default="core_v1",
        help="Benchmark suite name"
    )
    parser.add_argument(
        "--strategy", default="grid",
        choices=["grid", "random", "boundary", "all"],
        help="Hypothesis generation strategy"
    )
    parser.add_argument(
        "--max-experiments", type=int, default=50,
        help="Maximum experiments per session"
    )
    parser.add_argument(
        "--max-hours", type=float, default=4.0,
        help="Maximum session duration in hours"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview without executing edits or benchmarks"
    )
    parser.add_argument(
        "--surfaces-file", default=None,
        help="Path to surfaces.yaml"
    )

    args = parser.parse_args()

    # Load surfaces
    surfaces = load_surfaces(args.surfaces_file)
    parameters = get_surface_params(surfaces, args.surface)

    if not parameters:
        print(f"Error: No Tier A parameters found for surface '{args.surface}'")
        print("Available Tier A surfaces:")
        for s in surfaces:
            if s.get("tier") == "A" and s.get("parameters"):
                print(f"  - {s['file']} ({len(s['parameters'])} params)")
        sys.exit(1)

    print("Phionyx Research Engine v0.1.0")
    print(f"{'='*60}")
    print(f"Surface: {args.surface}")
    print(f"Suite:   {args.suite}")
    print(f"Strategy: {args.strategy}")
    print(f"Parameters: {len(parameters)}")
    for p in parameters:
        print(f"  - {p['name']}: {p['current']} [{p['range_min']}, {p['range_max']}] step={p['step']}")
    print(f"Max experiments: {args.max_experiments}")
    print(f"Max hours: {args.max_hours}")
    print(f"Dry run: {args.dry_run}")
    print(f"{'='*60}")

    # Import here to avoid slow startup for --help
    from ..config import EngineConfig, SessionConfig
    from ..loop import run_session

    config = EngineConfig(
        session=SessionConfig(
            max_experiments=args.max_experiments,
            max_session_seconds=args.max_hours * 3600,
        ),
    )

    result = run_session(
        config=config,
        surface_file=args.surface,
        suite_name=args.suite,
        strategy=args.strategy,
        surfaces=surfaces,
        parameters=parameters,
        dry_run=args.dry_run,
    )

    return 0 if result.get("error") is None else 1


if __name__ == "__main__":
    sys.exit(main())
