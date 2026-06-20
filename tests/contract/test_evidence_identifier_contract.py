"""
Contract tests — EvidenceIdentifier (v4, F20)
=============================================

The evidence identifier is the EXTERNAL, citable handle for one signed envelope:
``phionyx:trace:<YYYY-MM-DD>:sha256:<64-hex>``. These tests pin the format so a
reviewer who receives an id can rely on its shape, and so the companion's
verify-and-export layer composes ids that round-trip.

Format only — this contract resolves/verifies nothing (that is the companion's job).
"""

import pytest
from pydantic import ValidationError

from phionyx_core.contracts.v4 import EvidenceIdentifier, EVIDENCE_ID_PATTERN

_HEX = "f089edd19f321ada89c4794c494e78a575b5bb317d28e6096b87367af7978514"
_CANON = f"phionyx:trace:2026-06-10:sha256:{_HEX}"


class TestEvidenceIdentifierFormat:
    def test_compose_renders_canonical_string(self):
        eid = EvidenceIdentifier.compose(date="2026-06-10", digest=_HEX)
        assert eid.to_string() == _CANON
        assert str(eid) == _CANON
        assert eid.algo == "sha256"

    def test_compose_strips_sha256_prefix_from_chain_head(self):
        # The envelope chain head is carried as 'sha256:<hex>' — compose must accept it.
        eid = EvidenceIdentifier.compose(date="2026-06-10", digest=f"sha256:{_HEX}")
        assert eid.digest == _HEX
        assert eid.algo == "sha256"
        assert eid.to_string() == _CANON

    def test_compose_lowercases_digest(self):
        eid = EvidenceIdentifier.compose(date="2026-06-10", digest=_HEX.upper())
        assert eid.digest == _HEX
        assert eid.to_string() == _CANON

    def test_parse_round_trips(self):
        eid = EvidenceIdentifier.parse(_CANON)
        assert eid.date == "2026-06-10"
        assert eid.algo == "sha256"
        assert eid.digest == _HEX
        assert eid.to_string() == _CANON

    def test_compose_parse_are_inverse(self):
        eid = EvidenceIdentifier.compose(date="2026-06-10", digest=_HEX)
        assert EvidenceIdentifier.parse(eid.to_string()).to_string() == eid.to_string()

    def test_pattern_matches_canonical(self):
        import re

        assert re.match(EVIDENCE_ID_PATTERN, _CANON)


class TestEvidenceIdentifierRejection:
    @pytest.mark.parametrize(
        "bad",
        [
            "phionyx:trace:2026-6-10:sha256:" + _HEX,        # non-zero-padded date
            "phionyx:trace:2026-06-10:sha256:" + _HEX[:-1],  # short digest
            "phionyx:trace:2026-06-10:sha256:" + _HEX + "a",  # long digest
            "phionyx:trace:2026-06-10:sha512:" + _HEX,        # wrong algo
            "phionyx:trace:2026-06-10T12:00:00Z:sha256:" + _HEX,  # full timestamp (colon collision)
            "trace:2026-06-10:sha256:" + _HEX,                # missing prefix
            "phionyx:trace:2026-06-10:sha256:" + _HEX.upper(),  # uppercase digest
            "",
        ],
    )
    def test_parse_rejects_malformed(self, bad):
        with pytest.raises(ValueError):
            EvidenceIdentifier.parse(bad)

    def test_model_rejects_bad_date(self):
        with pytest.raises(ValidationError):
            EvidenceIdentifier(date="10-06-2026", digest=_HEX)

    def test_model_rejects_bad_digest(self):
        with pytest.raises(ValidationError):
            EvidenceIdentifier(date="2026-06-10", digest="nothex")

    def test_model_rejects_bad_algo(self):
        with pytest.raises(ValidationError):
            EvidenceIdentifier(date="2026-06-10", algo="md5", digest=_HEX)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
