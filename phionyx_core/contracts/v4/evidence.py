"""
EvidenceIdentifier — v4 Schema (F20)
====================================

The canonical, external, *verifiable* reference to ONE runtime decision's signed
evidence. Format::

    phionyx:trace:<YYYY-MM-DD>:sha256:<64-hex>

This module owns the **format only** — a pure, dependency-free contract. The
verify-and-export mechanism that resolves an identifier against the live RGE v0.2
envelope chain lives in the ``phionyx-mcp-server`` companion (where the chain,
``verify_chain``, and the AIREP projection already are). Core owns the format so it
has ONE home; the companion imports it. This keeps a single source of truth for the
string shape and prevents two divergent definitions.

Design choices (grounded, F20 plan 2026-06-10):

- ``<date>`` is the UTC calendar date of the envelope's ``subject.timestamp_utc``.
  Date-only **on purpose**: a full ISO-8601 timestamp contains ``:`` which would
  collide with the ``:`` field delimiter and make the id ambiguous to parse.
- ``<hash>`` is the envelope's ``integrity.current`` (the per-turn chain head),
  carried as the **full 64-hex** sha256 digest. An external evidence id must be the
  *actual* hash a third party recomputes (over the one RFC 8785 / JCS canonical
  form); truncation would weaken collision resistance. The internal session
  ``trace-<16hex>`` identifier is a *different*, session-grouping id and is left
  untouched.

Additive: this is a NEW standalone model. It does NOT touch any existing v4 schema
or hash domain (the same discipline as ``claim.py`` / ``abstention_record.py``).
Pure stdlib + pydantic — the Core import boundary is preserved. The model does not
resolve, sign, or verify anything; it is the *shape* of a citable reference.
"""

import re

from pydantic import BaseModel, Field

# phionyx:trace:<YYYY-MM-DD>:sha256:<64 lowercase hex>
EVIDENCE_ID_PATTERN = r"^phionyx:trace:\d{4}-\d{2}-\d{2}:sha256:[0-9a-f]{64}$"

_EVIDENCE_ID_RE = re.compile(EVIDENCE_ID_PATTERN)


class EvidenceIdentifier(BaseModel):
    """A citable, independently-verifiable reference to one signed envelope.

    Construct via :meth:`compose` or :meth:`parse`; render via :meth:`to_string`.
    The model is a *format* — given the same ``(date, digest)`` it always renders
    the same string, and the rendered string round-trips through :meth:`parse`.
    """

    date: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="UTC calendar date, YYYY-MM-DD (date component of the envelope timestamp)",
    )
    algo: str = Field(
        default="sha256",
        pattern=r"^sha256$",
        description="Hash algorithm; only 'sha256' is supported in v0.9.0",
    )
    digest: str = Field(
        ...,
        pattern=r"^[0-9a-f]{64}$",
        description="Lowercase hex digest of the envelope chain head (64 hex for sha256)",
    )

    def to_string(self) -> str:
        """Render the canonical ``phionyx:trace:<date>:<algo>:<digest>`` string."""
        return f"phionyx:trace:{self.date}:{self.algo}:{self.digest}"

    def __str__(self) -> str:  # pragma: no cover - thin delegation
        return self.to_string()

    @classmethod
    def compose(cls, date: str, digest: str, algo: str = "sha256") -> "EvidenceIdentifier":
        """Build from parts.

        ``digest`` may be a bare hex string or carry an algorithm prefix such as the
        envelope chain head's ``sha256:<hex>`` form — the prefix is split off and used
        as ``algo``. The digest is lower-cased so the canonical form is stable.
        """
        if ":" in digest:
            maybe_algo, _, rest = digest.partition(":")
            if maybe_algo:
                algo = maybe_algo
            digest = rest
        return cls(date=date, algo=algo, digest=digest.lower())

    @classmethod
    def parse(cls, value: str) -> "EvidenceIdentifier":
        """Parse a canonical evidence id string. Raises ``ValueError`` if malformed."""
        if not _EVIDENCE_ID_RE.match(value):
            raise ValueError(f"not a valid evidence id: {value!r}")
        # value == phionyx:trace:<date>:sha256:<hex> -> exactly 5 colon-separated parts
        # (<date> is hyphen-delimited, never colon-delimited, so the split is unambiguous)
        _, _, date, algo, digest = value.split(":")
        return cls(date=date, algo=algo, digest=digest)

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2026-06-10",
                "algo": "sha256",
                "digest": (
                    "f089edd19f321ada89c4794c494e78a575b5bb317d28e6096b87367af7978514"
                ),
            }
        }
