"""Config snapshot — backup and restore config files before experiments."""
import json
import shutil
from pathlib import Path


class ConfigSnapshot:
    """Backs up and restores config files.

    Provides an additional safety layer beyond git.
    Snapshots are stored in data/research_engine/snapshots/.
    """

    def __init__(self, data_dir: str = "data/research_engine"):
        self._dir = Path(data_dir) / "snapshots"
        self._dir.mkdir(parents=True, exist_ok=True)

    def snapshot(self, experiment_id: str, files: list[str]) -> str:
        """Create a snapshot of the given files.

        Returns the snapshot directory path.
        """
        snap_dir = self._dir / experiment_id
        snap_dir.mkdir(parents=True, exist_ok=True)

        manifest = {"experiment_id": experiment_id, "files": []}

        for file_path in files:
            src = Path(file_path)
            if src.exists():
                # Preserve directory structure
                dest = snap_dir / src.name
                shutil.copy2(src, dest)
                manifest["files"].append({
                    "original": str(src),
                    "snapshot": str(dest),
                })

        with open(snap_dir / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)

        return str(snap_dir)

    def restore(self, experiment_id: str) -> bool:
        """Restore files from a snapshot."""
        snap_dir = self._dir / experiment_id
        manifest_file = snap_dir / "manifest.json"

        if not manifest_file.exists():
            return False

        with open(manifest_file) as f:
            manifest = json.load(f)

        for entry in manifest["files"]:
            src = Path(entry["snapshot"])
            dest = Path(entry["original"])
            if src.exists():
                shutil.copy2(src, dest)

        return True

    def cleanup(self, experiment_id: str) -> None:
        """Remove a snapshot after it's no longer needed."""
        snap_dir = self._dir / experiment_id
        if snap_dir.exists():
            shutil.rmtree(snap_dir)
