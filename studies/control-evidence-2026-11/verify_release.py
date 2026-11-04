#!/usr/bin/env python3
"""Verify a control-evidence study archive without executing its contents."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import PurePosixPath
import tarfile


SCHEMA = "phionyx-control-evidence-release-manifest-v1"


def safe_member(name: str) -> tuple[str, str]:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or len(path.parts) < 2:
        raise ValueError(f"unsafe archive member: {name}")
    return path.parts[0], PurePosixPath(*path.parts[1:]).as_posix()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive")
    args = parser.parse_args()

    with tarfile.open(args.archive, mode="r:gz") as tar:
        members = tar.getmembers()
        if any(not member.isfile() for member in members):
            raise SystemExit("archive must contain regular files only")
        parsed = [safe_member(member.name) for member in members]
        roots = {root for root, _ in parsed}
        if len(roots) != 1:
            raise SystemExit(f"archive has multiple roots: {sorted(roots)}")
        by_name = {relative: member for (_, relative), member in zip(parsed, members)}
        if len(by_name) != len(members):
            raise SystemExit("duplicate archive path")
        manifest_member = by_name.get("RELEASE_MANIFEST.json")
        if manifest_member is None:
            raise SystemExit("missing RELEASE_MANIFEST.json")
        manifest_file = tar.extractfile(manifest_member)
        assert manifest_file is not None
        manifest = json.load(manifest_file)
        if manifest.get("schema") != SCHEMA:
            raise SystemExit("unexpected manifest schema")
        rows = {item["path"]: item for item in manifest["files"]}
        payload_names = set(by_name) - {"RELEASE_MANIFEST.json"}
        if set(rows) != payload_names or manifest["file_count"] != len(rows):
            raise SystemExit("manifest path set differs from archive")
        for name, expected in rows.items():
            stream = tar.extractfile(by_name[name])
            assert stream is not None
            data = stream.read()
            if len(data) != expected["bytes"]:
                raise SystemExit(f"byte count differs: {name}")
            if hashlib.sha256(data).hexdigest() != expected["sha256"]:
                raise SystemExit(f"sha256 differs: {name}")

    print(json.dumps({
        "status": "CONTROL_EVIDENCE_RELEASE_OK",
        "source_commit": manifest["source_commit"],
        "files": manifest["file_count"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
