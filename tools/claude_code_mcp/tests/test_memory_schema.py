"""Tests for tools/claude_code_mcp/memory_schema.py (v0.7.1 F-MS1)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory_schema import (  # noqa: E402
    BODY_MAX_LINES,
    BODY_MIN_LINES,
    DESCRIPTION_MAX_CHARS,
    MemoryFrontmatter,
    validate_directory,
    validate_file,
)


def _write_md(path: Path, frontmatter: dict, body: str) -> None:
    lines = ["---"]
    for k, v in frontmatter.items():
        if isinstance(v, dict):
            lines.append(f"{k}:")
            for sk, sv in v.items():
                lines.append(f"  {sk}: {sv}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    lines.append(body)
    path.write_text("\n".join(lines))


def _good_body() -> str:
    return "\n".join(f"Line {i} — content." for i in range(BODY_MIN_LINES + 1))


# ── Pydantic model unit tests ────────────────────────────────────────


def test_frontmatter_accepts_valid_minimal():
    m = MemoryFrontmatter(
        name="user-foo-bar",
        description="A short description.",
        type="user",
    )
    assert m.name == "user-foo-bar"
    assert m.type == "user"
    assert m.linked == []
    assert m.last_verified is None


def test_frontmatter_rejects_non_kebab_name():
    try:
        MemoryFrontmatter(name="User_Foo", description="x", type="user")
    except Exception as e:
        assert "kebab-case" in str(e)
    else:  # pragma: no cover
        raise AssertionError("should have raised")


def test_frontmatter_rejects_oversize_description():
    try:
        MemoryFrontmatter(
            name="x", description="x" * (DESCRIPTION_MAX_CHARS + 1), type="user"
        )
    except Exception as e:
        assert "must be ≤" in str(e)
    else:  # pragma: no cover
        raise AssertionError("should have raised")


def test_frontmatter_rejects_unknown_type():
    try:
        MemoryFrontmatter(name="x", description="x", type="bogus")  # type: ignore
    except Exception:
        pass
    else:  # pragma: no cover
        raise AssertionError("should have raised")


def test_frontmatter_rejects_bad_link_form():
    try:
        MemoryFrontmatter(
            name="x", description="x", type="feedback", linked=["not-a-link"]
        )
    except Exception as e:
        assert "[[kebab-name]]" in str(e)
    else:  # pragma: no cover
        raise AssertionError("should have raised")


def test_frontmatter_rejects_bad_iso_date():
    try:
        MemoryFrontmatter(
            name="x", description="x", type="project", last_verified="May 27 2026"
        )
    except Exception as e:
        assert "YYYY-MM-DD" in str(e)
    else:  # pragma: no cover
        raise AssertionError("should have raised")


def test_frontmatter_accepts_reasoning_lesson_type():
    """The fifth type, added by F-MS1, must validate."""
    m = MemoryFrontmatter(
        name="rl-x", description="x", type="reasoning_lesson",
        last_verified="2026-05-27",
    )
    assert m.type == "reasoning_lesson"


# ── File-level validation tests ──────────────────────────────────────


def test_validate_file_clean_passes():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "user-foo.md"
        _write_md(
            p,
            {"name": "user-foo", "description": "ok", "type": "user"},
            _good_body(),
        )
        r = validate_file(p)
        assert r.ok, r.errors


def test_validate_file_short_body_fails():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "user-x.md"
        _write_md(
            p,
            {"name": "user-x", "description": "ok", "type": "user"},
            "Line 1\nLine 2",  # below BODY_MIN_LINES
        )
        r = validate_file(p)
        assert not r.ok
        assert any("body has" in e for e in r.errors)


def test_validate_file_long_body_warns_not_errors():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "user-x.md"
        body = "\n".join(f"L{i}" for i in range(BODY_MAX_LINES + 5))
        _write_md(
            p,
            {"name": "user-x", "description": "ok", "type": "user"},
            body,
        )
        r = validate_file(p)
        assert r.ok
        assert any("soft cap" in w for w in r.warnings)


def test_validate_file_missing_frontmatter_fails():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "user-x.md"
        p.write_text("just a plain markdown body without frontmatter\n" * 6)
        r = validate_file(p)
        assert not r.ok
        assert any("no frontmatter" in e for e in r.errors)


def test_validate_file_legacy_nested_metadata_type():
    """Files with type buried under 'metadata' should still validate.

    This is the actual shape used by many existing auto-memory files
    (frontmatter has `metadata.type: project`); we pull it up so the
    legacy shape passes the schema.
    """
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "project-legacy-foo.md"
        _write_md(
            p,
            {
                "name": "project-legacy-foo",
                "description": "legacy shape",
                "metadata": {"type": "project"},
            },
            _good_body(),
        )
        r = validate_file(p)
        assert r.ok, r.errors


def test_validate_file_name_mismatch_warns():
    """Filename stem and `name` field should match (in kebab translation)."""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "actual-file-name.md"
        _write_md(
            p,
            {
                "name": "different-name",  # mismatches filename stem
                "description": "x",
                "type": "user",
            },
            _good_body(),
        )
        r = validate_file(p)
        # mismatch is a warning, not an error
        assert r.ok
        assert any("does not match filename stem" in w for w in r.warnings)


def test_validate_file_project_without_last_verified_warns():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "project-x.md"
        _write_md(
            p,
            {"name": "project-x", "description": "x", "type": "project"},
            _good_body(),
        )
        r = validate_file(p)
        assert r.ok  # warning, not error (migration tolerance)
        assert any("last_verified" in w for w in r.warnings)


def test_validate_directory_report_shape():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        # 1 good
        _write_md(
            d / "user-a.md",
            {"name": "user-a", "description": "ok", "type": "user"},
            _good_body(),
        )
        # 1 bad
        _write_md(
            d / "user-b.md",
            {"name": "BAD_NAME", "description": "ok", "type": "user"},
            _good_body(),
        )
        # MEMORY.md (the index) is skipped
        (d / "MEMORY.md").write_text("# Index\n")
        report = validate_directory(d)
        assert report.files_checked == 2  # MEMORY.md skipped
        assert report.files_ok == 1
        assert report.files_failed == 1
        assert not report.is_clean()


def test_validate_directory_handles_missing_dir():
    report = validate_directory(Path("/no/such/dir"))
    assert report.files_checked == 0
    assert report.is_clean()
