"""Explicit online acquisition; offline reproduction never invokes this script."""

import datetime
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Reacquire into a NEW directory; never overwrite this experiment's pinned bytes."""
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, help="New empty acquisition directory")
    args = parser.parse_args()
    original = json.loads((ROOT / "SOURCE_PINS.json").read_bytes())
    destination = Path(args.output_dir).resolve()
    if destination.exists() and any(destination.iterdir()):
        raise SystemExit("Refusing to overwrite a nonempty acquisition directory")
    destination.mkdir(parents=True, exist_ok=True)
    records = []
    for old in original["sources"]:
        item = dict(
            id=old["id"],
            url=old["url"],
            role=old["role"],
            accessed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )
        try:
            with urllib.request.urlopen(old["url"], timeout=40) as response:
                data = response.read()
                item["resolved_url"] = response.url
            target = destination / old["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            item.update(
                status="AVAILABLE",
                path=old["path"],
                bytes=len(data),
                sha256=hashlib.sha256(data).hexdigest(),
                original_sha256=old["sha256"],
                byte_difference=hashlib.sha256(data).hexdigest() != old["sha256"],
            )
            if "expected_revision" in old:
                latest = json.loads(data).get("rev")
                item.update(
                    expected_revision=old["expected_revision"],
                    observed_latest_revision=latest,
                    revision_difference="NONE"
                    if latest == old["expected_revision"]
                    else "DIFFERENT",
                )
        except Exception as exc:
            item.update(status="UNAVAILABLE", error=str(exc))
        records.append(item)
    (destination / "SOURCE_PINS.json").write_text(json.dumps({"sources": records}, indent=2) + "\n")
    print("New acquisition written to", destination, "— original experiment unchanged")


if __name__ == "__main__":
    main()
