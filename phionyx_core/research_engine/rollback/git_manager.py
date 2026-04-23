"""Git manager — commit and revert operations for experiments.

Uses git as the rollback mechanism. Every experiment is a single commit.
Revert = git reset --hard HEAD~1. Simple, proven, auditable.
"""
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GitResult:
    success: bool
    output: str
    error: str = ""


class GitManager:
    """Manages git operations for experiment tracking."""

    def __init__(self, repo_dir: str = "."):
        self._repo = Path(repo_dir).resolve()

    def _run(self, *args: str) -> GitResult:
        """Run a git command."""
        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=self._repo,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return GitResult(
                success=result.returncode == 0,
                output=result.stdout.strip(),
                error=result.stderr.strip(),
            )
        except subprocess.TimeoutExpired:
            return GitResult(success=False, output="", error="Git command timed out")
        except Exception as e:
            return GitResult(success=False, output="", error=str(e))

    def get_current_commit(self) -> str:
        """Get current HEAD commit hash."""
        result = self._run("rev-parse", "HEAD")
        return result.output if result.success else ""

    def get_current_branch(self) -> str:
        """Get current branch name."""
        result = self._run("rev-parse", "--abbrev-ref", "HEAD")
        return result.output if result.success else ""

    def create_branch(self, branch_name: str) -> GitResult:
        """Create and checkout a new branch."""
        return self._run("checkout", "-b", branch_name)

    def commit_experiment(
        self,
        experiment_id: str,
        hypothesis_summary: str,
        files: list[str],
    ) -> GitResult:
        """Stage files and commit with experiment metadata."""
        # Stage specific files only
        for f in files:
            result = self._run("add", f)
            if not result.success:
                return result

        message = f"exp: {hypothesis_summary}\n\nExperiment-ID: {experiment_id}"
        return self._run("commit", "-m", message)

    def revert_last_commit(self) -> GitResult:
        """Revert the last commit, preserving uncommitted data files.

        Uses stash to protect experiments.jsonl and other data files
        from being wiped by git reset --hard.
        """
        # Stash uncommitted changes (experiments.jsonl, audit, etc.)
        stash_result = self._run("stash", "push", "--include-untracked")
        had_stash = "No local changes" not in stash_result.output

        # Reset hard to undo the experiment commit
        reset_result = self._run("reset", "--hard", "HEAD~1")

        # Restore stashed data
        if had_stash:
            self._run("stash", "pop")

        return reset_result

    def tag_archived(self, experiment_id: str) -> GitResult:
        """Tag current commit as archived before reverting."""
        return self._run("tag", f"archived/{experiment_id}")

    def has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes."""
        result = self._run("status", "--porcelain")
        return bool(result.output)

    def stash(self) -> GitResult:
        """Stash current changes."""
        return self._run("stash", "push", "-m", "research-engine-backup")

    def stash_pop(self) -> GitResult:
        """Pop stashed changes."""
        return self._run("stash", "pop")
