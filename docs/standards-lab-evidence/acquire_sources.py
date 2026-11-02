"""Read-only HTTPS acquisition for G; never overwrites frozen experiment inputs."""

import concurrent.futures
import datetime
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
DRAFTS = {
    "draft-he-agentproto-verifier-evidence": "03",
    "draft-gruszka-audit-decision-receipts": "03",
    "draft-gruszka-signed-evaluation-receipts": "04",
    "draft-abak-ai-evaluation-claim-preservation": "00",
    "draft-gruszka-evaluation-receipt-mappings": "04",
    "draft-watts-eqr-conformance": "05",
    "draft-abak-agent-control-delivery-evidence": "02",
}


def acquire(item):
    name, url, revision, kind = item
    row = {
        "id": name,
        "url": url,
        "exact_revision": revision,
        "kind": kind,
        "accessed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "retrieval": "HTTPS GET; Accept-Encoding identity; SHA-256 of raw body bytes",
    }
    try:
        request = urllib.request.Request(
            url, headers={"User-Agent": "StandardsLab-local-audit/1", "Accept-Encoding": "identity"}
        )
        with urllib.request.urlopen(request, timeout=25) as response:
            body = response.read()
            row.update(
                status="AVAILABLE",
                http_status=response.status,
                resolved_url=response.url,
                sha256=hashlib.sha256(body).hexdigest(),
                bytes=len(body),
            )
        path = OUT / "sources" / name
        path.write_bytes(body)
        row["path"] = str(path.relative_to(ROOT))
        if kind == "mutable-datatracker-metadata":
            meta = json.loads(body)
            row["observed_revision"] = meta.get("rev")
            row["expected_revision"] = revision
            row["revision_difference"] = "NONE" if meta.get("rev") == revision else "CHANGED"
    except (urllib.error.URLError, OSError, ValueError) as error:
        row.update(status="UNKNOWN", error=str(error), sha256=None, bytes=None, path=None)
    return row


if __name__ == "__main__":
    items = []
    for name, rev in DRAFTS.items():
        items += [
            (
                f"{name}-{rev}.txt",
                f"https://www.ietf.org/archive/id/{name}-{rev}.txt",
                rev,
                "revision-pinned-draft",
            ),
            (
                f"{name}-metadata.json",
                f"https://datatracker.ietf.org/api/v1/doc/document/{name}/",
                rev,
                "mutable-datatracker-metadata",
            ),
        ]
    for name in [
        "draft-abak-agent-control-delivery-evidence",
        "draft-abak-ai-evaluation-claim-preservation",
    ]:
        items.append(
            (
                name + "-referencedby.html",
                f"https://datatracker.ietf.org/doc/{name}/referencedby/",
                "snapshot-only",
                "mutable-reference-surface",
            )
        )
    items += [
        (
            "airep-arxiv-v2.html",
            "https://arxiv.org/abs/2608.21363v2",
            "2608.21363v2",
            "publication-metadata",
        ),
        (
            "airep-beta-release.json",
            "https://api.github.com/repos/halvrenofviryel/ai-runtime-evidence-protocol/releases/tags/v0.2.0-beta.1",
            "v0.2.0-beta.1",
            "mutable-release-metadata",
        ),
        (
            "airep-zenodo-v01.json",
            "https://zenodo.org/api/records/20475137",
            "20475137",
            "publication-metadata",
        ),
        (
            "airep-zenodo-alpha.json",
            "https://zenodo.org/api/records/22101986",
            "22101986",
            "publication-metadata",
        ),
    ]
    rows = list(concurrent.futures.ThreadPoolExecutor(max_workers=6).map(acquire, items))
    (OUT / "http_sources.json").write_text(json.dumps({"sources": rows}, indent=2) + "\n")
    for row in rows:
        print(row["id"], row["status"], row.get("sha256"), row.get("revision_difference", ""))
