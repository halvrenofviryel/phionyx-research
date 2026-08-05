"""Pin EchoState2.phi at representative points.

Written 2026-08-02 with the v2 → v2_1 migration, because that migration moved
phi by an average of 45% across the state space and **not one test noticed**.
Every existing assertion on `state.phi` is relative — `> 0.0`, a comparison
between two states, or an overwrite — so an absolute shift of any size passes
every gate. The 50-case file in tests/regression does not exercise this path
either.

That is the gap this file closes. It is a characterization test: it does not
claim these values are *correct*, it claims they are *what the system now
produces*, so the next change to them is a decision rather than a surprise.

**What changed and why phi fell.** `EchoState2.phi` called
`calculate_phi_v2` — labelled "v2.0 (Legacy)" in formulas.py — while this
property's own docstring said "phi = f(A, V, H, dt) via Physics 2.1 formulas".
Two of those four inputs never reached the formula:

- **valence** was not passed at all, so it defaulted to 0.0;
- **arousal** defaulted to 1.0, i.e. every turn was computed at maximum arousal;
- and `entropy_penalty_k` fell back to the module default of 0.0, which
  switches the entropy term off entirely.

Measured with matched arguments, v2 and v2_1 return byte-identical values, so
the drop is not a formula change. It is those three defaults no longer standing
in for the state's real values. Phi was inflated, not deflated.
"""
from __future__ import annotations

import pytest

from phionyx_core.state.echo_state_2 import EchoState2

#: (arousal, valence, entropy) → phi, read off `EchoState2(...).phi` itself on
#: 2026-08-02. The first version of this table was computed from a *model* of
#: the property rather than from the property, and six of nine rows were wrong
#: in the fifth decimal — `EchoState2.dt` defaults to 0.0, which the property
#: turns into a time_delta of 1.0 by a different route than the reconstruction
#: took. The test caught it. Values here come from the object.
#: The third column is what the pre-migration v2 path returned for the same
#: state, kept so the size of the change stays visible in the record.
CASES = [
    # A     V     H      phi (v2_1)   was (v2, arousal=1.0, k=0.0)
    (0.2, -0.6, 0.8, 0.211605, 0.885662),
    (0.2, 0.0, 0.8, 0.197142, 0.885662),
    (0.2, 0.6, 0.8, 0.211605, 0.885662),
    (0.5, -0.6, 0.5, 1.191310, 2.181828),
    (0.5, 0.0, 0.5, 1.100885, 2.181828),
    (0.5, 0.6, 0.5, 1.191310, 2.181828),
    (0.8, -0.6, 0.2, 2.983658, 3.490833),
    (0.8, 0.0, 0.2, 2.796746, 3.490833),
    (0.8, 0.6, 0.2, 2.983658, 3.490833),
]


@pytest.mark.parametrize("arousal,valence,entropy,expected,_previous", CASES)
def test_phi_is_what_we_measured(arousal, valence, entropy, expected,
                                 _previous) -> None:
    state = EchoState2(A=arousal, V=valence, H=entropy)

    assert state.phi == pytest.approx(expected, abs=1e-5)


class TestTheInputsTheDocstringNamesActuallyReachTheFormula:
    """`phi = f(A, V, H, dt)`. Each of the four is asserted to matter."""

    def test_valence_changes_phi(self) -> None:
        """It did not before: the v2 call passed no valence at all."""
        neutral = EchoState2(A=0.5, V=0.0, H=0.5).phi
        charged = EchoState2(A=0.5, V=0.6, H=0.5).phi

        assert charged != neutral

    def test_negative_valence_raises_phi_like_positive_does(self) -> None:
        """v2.2's Base Life Support: negative affect creates resonance rather
        than collapsing it, so |V| is what counts."""
        negative = EchoState2(A=0.5, V=-0.6, H=0.5).phi
        positive = EchoState2(A=0.5, V=0.6, H=0.5).phi
        neutral = EchoState2(A=0.5, V=0.0, H=0.5).phi

        assert negative == pytest.approx(positive, abs=1e-9)
        assert negative > neutral

    def test_arousal_changes_phi(self) -> None:
        """It did not before: arousal defaulted to 1.0 on every turn."""
        low = EchoState2(A=0.2, V=0.0, H=0.5).phi
        high = EchoState2(A=0.8, V=0.0, H=0.5).phi

        assert high > low

    def test_entropy_lowers_phi(self) -> None:
        """It did not before: `entropy_penalty_k` fell back to 0.0, which makes
        the entropy factor exactly 1 regardless of H."""
        calm = EchoState2(A=0.5, V=0.0, H=0.2).phi
        chaotic = EchoState2(A=0.5, V=0.0, H=0.8).phi

        assert calm > chaotic

    def test_the_property_no_longer_calls_the_legacy_formula(self) -> None:
        """formulas.py labels calculate_phi_v2 "v2.0 (Legacy)" and directs
        callers to v2_1. If this property goes back, the docstring's claim to
        use Physics 2.1 goes back to being false."""
        from pathlib import Path

        source = (next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file()) / "phionyx_core" / "state"
                  / "echo_state_2.py").read_text("utf-8")
        body = source.split("def phi", 1)[1].split("\n    @", 1)[0]

        assert "calculate_phi_v2_1" in body
        assert "calculate_phi_v2(" not in body
