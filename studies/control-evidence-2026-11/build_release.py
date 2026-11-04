#!/usr/bin/env python3
"""Build a deterministic, offline-verifiable control-evidence study archive."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import stat
import subprocess
import tarfile


ROOT = Path(__file__).resolve().parents[2]
VERSION = "1.0.0"
STEM = f"control-evidence-study-v{VERSION}"
PUBLICATION_MERGE = "54682cfd312dc8c7935e926539811cfc29ea6568"
FILES = (
    "LICENSE",
    "docs/CONTROL_EVIDENCE_RESEARCH.md",
    "docs/EXTERNAL_IMPACT_LEDGER.md",
    "docs/external_impact_ledger.json",
)
DIRECTORIES = (
    "docs/external-replication",
    "experiments/ietf/acder02-control-benchmark",
    "reports/external-replication",
    "studies/control-evidence-2026-11",
)
EXCLUDED_NAMES = {"__pycache__", ".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def selected_files() -> list[Path]:
    paths = [ROOT / name for name in FILES]
    for dirname in DIRECTORIES:
        paths.extend(path for path in (ROOT / dirname).rglob("*") if path.is_file())
    result = []
    for path in sorted(set(paths)):
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_NAMES for part in relative.parts):
            continue
        if path.suffix in EXCLUDED_SUFFIXES:
            continue
        if path.is_symlink():
            raise SystemExit(f"release does not admit symlinks: {relative}")
        result.append(path)
    return result


def row(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def add_bytes(tar: tarfile.TarFile, name: str, data: bytes, mode: int = 0o644) -> None:
    info = tarfile.TarInfo(name=f"{STEM}/{name}")
    info.size = len(data)
    info.mode = mode
    info.mtime = 0
    info.uid = info.gid = 0
    info.uname = info.gname = "root"
    tar.addfile(info, io.BytesIO(data))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    dirty = git("status", "--porcelain")
    if dirty:
        raise SystemExit("release build requires a clean committed worktree")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", PUBLICATION_MERGE, "HEAD"], cwd=ROOT
    ).returncode:
        raise SystemExit("publication merge is not an ancestor of HEAD")

    source_commit = git("rev-parse", "HEAD")
    paths = selected_files()
    manifest = {
        "schema": "phionyx-control-evidence-release-manifest-v1",
        "study": "control-delivery-is-not-execution",
        "version": VERSION,
        "source_commit": source_commit,
        "publication_merge": PUBLICATION_MERGE,
        "file_count": len(paths),
        "files": [row(path) for path in paths],
    }
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    archive = args.out_dir / f"{STEM}.tar.gz"
    if archive.exists():
        raise SystemExit(f"refusing to overwrite {archive}")
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w", format=tarfile.PAX_FORMAT) as tar:
                add_bytes(tar, "RELEASE_MANIFEST.json", manifest_bytes)
                for path in paths:
                    mode = 0o755 if stat.S_IMODE(path.stat().st_mode) & 0o111 else 0o644
                    add_bytes(tar, path.relative_to(ROOT).as_posix(), path.read_bytes(), mode)

    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (args.out_dir / f"{STEM}.tar.gz.sha256").write_text(
        f"{digest}  {archive.name}\n"
    )
    (args.out_dir / f"{STEM}.manifest.json").write_bytes(manifest_bytes)
    print(json.dumps({
        "archive": str(archive),
        "bytes": archive.stat().st_size,
        "sha256": digest,
        "files": len(paths),
        "source_commit": source_commit,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
