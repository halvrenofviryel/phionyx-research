"""Memory frontmatter schema — v0.7.1 F-MS1.

Applies the schema discipline Phionyx already enforces on its evidence
envelopes (Pydantic v4 contracts, additionalProperties: false) to the
Claude Code auto-memory directory. ~30 markdown files live under
``~/.claude/projects/<project>/memory/``; each carries a YAML frontmatter
block. Until now those frontmatters were free-text — no validation, no
length bounds, no required-field check.

This module:

  * Declares the schema (Pydantic v2 ``MemoryFrontmatter``).
  * Parses a Markdown file into ``(frontmatter, body)``.
  * Validates a single file and returns ``ValidationResult``.
  * Walks a directory and produces a ``DirectoryReport``.

Used by:

  * ``check_memory_schema.py`` — pre-commit hook (CI gate).
  * Future ``/api/memory-health`` if the Founder Console wants to surface
    schema-discipline status alongside the runtime-evidence panel.

Design intent — the 5/5 light version of Zep's 10/10/10:

  * 5 fixed memory types (``user``, ``feedback``, ``project``,
    ``reference``, ``reasoning_lesson``). ``reasoning_lesson`` is the
    fifth type added by F-MS1; the first four already exist in the
    auto-memory taxonomy.
  * 5 frontmatter fields: ``name``, ``description``, ``type``, optional
    ``linked``, optional ``last_verified``.
  * Body bounds: ``5 <= line_count <= 200``.

No stdlib violations; pure pydantic + stdlib.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

MemoryType = Literal["user", "feedback", "project", "reference", "reasoning_lesson"]

_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")
_LINK_RE = re.compile(r"^\[\[[a-z][a-z0-9-]*\]\]$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_FRONTMATTER_OPEN = "---"
_REQUIRES_LAST_VERIFIED = {"project", "reference", "reasoning_lesson"}

DESCRIPTION_MAX_CHARS = 200
BODY_MIN_LINES = 5
BODY_MAX_LINES = 200


class MemoryFrontmatter(BaseModel):
    """Required + optional fields for a memory file's frontmatter block."""

    name: str = Field(..., description="kebab-case slug, must match filename stem")
    description: str = Field(..., description="single-line summary, ≤ 200 chars")
    type: MemoryType = Field(..., description="memory category")
    linked: list[str] = Field(
        default_factory=list,
        description="optional list of [[other-name]] cross-references",
    )
    last_verified: Optional[str] = Field(
        default=None, description="ISO date YYYY-MM-DD"
    )

    model_config = {"extra": "allow"}  # tolerate metadata/originSessionId for legacy files

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        if not _SLUG_RE.match(v):
            raise ValueError(
                f"name must be kebab-case (lowercase, digits, hyphens); got: {v!r}"
            )
        return v

    @field_validator("description")
    @classmethod
    def _validate_description(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("description must not be empty")
        if len(v) > DESCRIPTION_MAX_CHARS:
            raise ValueError(
                f"description must be ≤ {DESCRIPTION_MAX_CHARS} chars; got {len(v)}"
            )
        return v

    @field_validator("linked")
    @classmethod
    def _validate_linked(cls, v: list[str]) -> list[str]:
        for item in v:
            if not _LINK_RE.match(item):
                raise ValueError(
                    f"linked items must be [[kebab-name]] form; got: {item!r}"
                )
        return v

    @field_validator("last_verified")
    @classmethod
    def _validate_last_verified(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not _ISO_DATE_RE.match(v):
            raise ValueError(
                f"last_verified must be ISO YYYY-MM-DD; got: {v!r}"
            )
        return v


@dataclass
class ValidationResult:
    """Per-file validation outcome."""

    path: str
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    body_lines: int = 0


@dataclass
class DirectoryReport:
    """Summary across a directory walk."""

    directory: str
    files_checked: int = 0
    files_ok: int = 0
    files_failed: int = 0
    results: list[ValidationResult] = field(default_factory=list)

    def is_clean(self) -> bool:
        return self.files_failed == 0


# ── parser + validator ───────────────────────────────────────────────


def _parse_frontmatter_and_body(text: str) -> tuple[dict, str]:
    """Split a Markdown file into (frontmatter dict, body string).

    The frontmatter is a YAML-ish block between two ``---`` lines. We
    deliberately use a hand-rolled parser (no PyYAML dep) because the
    schema is shallow: top-level scalar keys and an optional nested
    ``metadata`` mapping. The grammar matches every existing memory
    file's frontmatter as of 2026-05-27.
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != _FRONTMATTER_OPEN:
        return {}, text
    fm_end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == _FRONTMATTER_OPEN:
            fm_end = i
            break
    if fm_end is None:
        return {}, text
    fm_lines = lines[1:fm_end]
    body = "\n".join(lines[fm_end + 1 :])

    fm: dict = {}
    nested: Optional[str] = None  # name of nested mapping currently being filled
    for ln in fm_lines:
        if not ln.strip():
            continue
        # Comments (rare in practice but tolerate)
        if ln.lstrip().startswith("#"):
            continue
        if ln.startswith("  ") and nested is not None:
            # nested key:value under current mapping
            key, _, val = ln.strip().partition(":")
            if val.strip():
                fm.setdefault(nested, {})[key.strip()] = _strip_quotes(val.strip())
            continue
        # Top-level key
        key, _, val = ln.partition(":")
        key = key.strip()
        val = val.strip()
        if not key:
            continue
        if not val:
            # Mapping or list follows
            nested = key
            continue
        nested = None
        # list inline (rare): "linked: [[a]], [[b]]"
        if val.startswith("[") and val.endswith("]") and "," in val:
            items = [x.strip() for x in val[1:-1].split(",") if x.strip()]
            fm[key] = items
        else:
            fm[key] = _strip_quotes(val)
    return fm, body


def _strip_quotes(s: str) -> str:
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    return s


def validate_file(path: Path) -> ValidationResult:
    """Validate one memory markdown file against the schema."""
    rel = str(path)
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return ValidationResult(path=rel, ok=False, errors=[f"could not read file: {e}"])

    fm_raw, body = _parse_frontmatter_and_body(text)

    errors: list[str] = []
    warnings: list[str] = []

    # Frontmatter must exist
    if not fm_raw:
        errors.append("no frontmatter block found (file must begin with '---')")
        return ValidationResult(path=rel, ok=False, errors=errors, body_lines=0)

    # If 'type' is buried inside 'metadata' (legacy shape), pull it up to top-level
    # so the Pydantic model can see it.
    if "type" not in fm_raw and isinstance(fm_raw.get("metadata"), dict):
        meta = fm_raw["metadata"]
        if "type" in meta:
            fm_raw = {**fm_raw, "type": meta["type"]}

    try:
        fm = MemoryFrontmatter.model_validate(fm_raw)
    except Exception as e:
        errors.append(f"frontmatter schema: {e}")
        # Still count body for context
        body_lines = sum(1 for ln in body.splitlines() if ln.strip())
        return ValidationResult(path=rel, ok=False, errors=errors, body_lines=body_lines)

    # name must match filename stem
    expected_name = path.stem.replace("_", "-")
    if fm.name != expected_name:
        warnings.append(
            f"name {fm.name!r} does not match filename stem {expected_name!r} "
            f"(would expect kebab-case translation)"
        )

    # Body bounds (non-blank lines only)
    body_lines = sum(1 for ln in body.splitlines() if ln.strip())
    if body_lines < BODY_MIN_LINES:
        errors.append(
            f"body has {body_lines} non-blank lines; must be ≥ {BODY_MIN_LINES}"
        )
    elif body_lines > BODY_MAX_LINES:
        warnings.append(
            f"body has {body_lines} non-blank lines; soft cap is {BODY_MAX_LINES}"
        )

    # last_verified required for some types
    if fm.type in _REQUIRES_LAST_VERIFIED and not fm.last_verified:
        # Tolerate: legacy files often have last_verified mentioned in body.
        # Surface as warning, not error, so existing memory passes initially.
        warnings.append(
            f"type={fm.type} should declare last_verified in frontmatter "
            f"(found only in body or absent)"
        )

    return ValidationResult(
        path=rel,
        ok=not errors,
        errors=errors,
        warnings=warnings,
        body_lines=body_lines,
    )


def validate_directory(memory_dir: Path) -> DirectoryReport:
    """Walk a memory directory and validate every .md file (excluding MEMORY.md)."""
    report = DirectoryReport(directory=str(memory_dir))
    if not memory_dir.is_dir():
        return report
    for f in sorted(memory_dir.glob("*.md")):
        # MEMORY.md is the index, not a memory file — different shape (no frontmatter)
        if f.name == "MEMORY.md":
            continue
        result = validate_file(f)
        report.results.append(result)
        report.files_checked += 1
        if result.ok:
            report.files_ok += 1
        else:
            report.files_failed += 1
    return report


__all__ = [
    "MemoryType",
    "MemoryFrontmatter",
    "ValidationResult",
    "DirectoryReport",
    "validate_file",
    "validate_directory",
    "BODY_MIN_LINES",
    "BODY_MAX_LINES",
    "DESCRIPTION_MAX_CHARS",
]
