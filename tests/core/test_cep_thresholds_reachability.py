"""What the CEP thresholds actually decide, measured by running them.

Written after OD-16 closed, because tracing the last three placeholders to
their consumers meant reading `_apply_thresholds`, and reading it raised a
question the placeholders had hidden: **if the inputs were wrong, were the
thresholds ever reachable?**

Three answers, each measured rather than reasoned:

1. **The phi-gated self-narrative branch cannot fire.** `phi_echo_quality` is
   `phi / 10`, and `phi_self_threshold` is 0.72, so the branch needs a phi of
   **7.2**. The pipeline produces phi in roughly [0.1, 0.9] — `formulas.py:508`
   documents the cognitive value as 0-1 with a 0.05 floor, and every
   `phi_total_range` in the seed data falls inside [0.1, 0.9]. Zero of 81
   sampled values reach the threshold. Filed as OD-19; **not fixed here**,
   because moving either the divisor or the threshold changes when a safety
   block fires and that is the founder's call.

2. **The entropy substitution is not inert.** An absent entropy became 0.0 in
   the bridge, which makes `phi_echo_density` 1.0 — its maximum. Swept over
   `_apply_thresholds`, that flips `is_self_narrative_blocked` at 18 points,
   all in the window the code predicts: `0.24 < self_reference <= 0.30` with
   novelty below 0.2, where the density branch's looser self-reference bound
   reaches something the novelty branch does not. The direction is
   over-blocking, not under-blocking, which is worth stating precisely.

3. **The stability substitution is inert.** `echo_stability` is read zero
   times by `_apply_thresholds`, and flags are identical at stability 0.0,
   0.8 and 1.0. It is a reported metric, not a gate input.

These are pinned, not asserted-as-fixed. Each fails when the property it
measured stops holding, which is when the classification has to be revisited.
"""
from __future__ import annotations

import pytest

from phionyx_core.cep.cep_config import load_cep_config
from phionyx_core.cep.cep_engine import ConsciousEchoProofEngine


@pytest.fixture(scope="module")
def engine() -> ConsciousEchoProofEngine:
    return ConsciousEchoProofEngine()


#: The range the pipeline actually produces. `formulas.py:508` documents the
#: cognitive phi as 0-1 with a 0.05 floor; every `phi_total_range` in the seed
#: data sits inside this.
PIPELINE_PHI = [round(v * 0.01, 2) for v in range(10, 91)]


class TestThePhiGateIsUnreachable:
    """OD-19. The measurement, kept so the finding cannot quietly go stale."""

    def test_no_pipeline_phi_reaches_the_self_narrative_threshold(self, engine):
        threshold = engine.config.thresholds.phi_self_threshold

        reaching = [
            phi for phi in PIPELINE_PHI
            if engine.evaluate_response(
                raw_text="I remember.", phi=phi, entropy=0.3
            ).metrics.phi_echo_quality >= threshold
        ]

        assert reaching == [], (
            f"phi values {reaching} now reach phi_self_threshold "
            f"({threshold}). OD-19 has been acted on — record which of the "
            "divisor or the threshold moved, and why, then delete this test.")

    def test_the_threshold_needs_a_phi_the_pipeline_does_not_produce(self, engine):
        """Names the number, so the gap is a quantity rather than a worry."""
        threshold = engine.config.thresholds.phi_self_threshold
        required_phi = threshold * 10.0

        assert required_phi == pytest.approx(7.2)
        assert required_phi > max(PIPELINE_PHI), (
            f"the threshold needs phi={required_phi} and the pipeline tops "
            f"out at {max(PIPELINE_PHI)}. If that is no longer true, the "
            "scale changed and OD-19 needs re-measuring, not re-asserting.")

    def test_the_flag_still_has_live_paths(self, engine):
        """The control, and the reason OD-19 is a dead *branch*, not a dead flag.

        Without this, "the phi gate cannot fire" would read as "self-narrative
        blocking does not work", which is false and would be a worse claim
        than the one it replaced.
        """
        config = load_cep_config()
        metrics = engine.evaluate_response(
            raw_text="x", phi=0.5, entropy=0.5).metrics
        metrics.mirror_self_score = config.thresholds.mirror_self_max_score + 0.1

        flags = engine._apply_thresholds(metrics, config)

        assert flags.is_self_narrative_blocked, (
            "the mirror-self path must still reach the flag; if it does not, "
            "self-narrative blocking is entirely dead and OD-19 is urgent")


class TestTheEntropySubstitutionChangesDecisions:
    """Why an absent entropy is worth recording rather than defaulting."""

    @staticmethod
    def _flags(engine, config, density, self_ref, novelty):
        metrics = engine.evaluate_response(
            raw_text="x", phi=0.5, entropy=0.5).metrics
        metrics.phi_echo_quality = 0.05
        metrics.phi_echo_density = density
        metrics.self_reference_ratio = self_ref
        metrics.trauma_language_score = 0.0
        metrics.mirror_self_score = 0.0
        metrics.variation_novelty_score = novelty
        return engine._apply_thresholds(metrics, config)

    def test_an_absent_entropy_flips_the_self_narrative_flag(self, engine):
        config = load_cep_config()
        flips = [
            (self_ref, novelty)
            for self_ref in [round(v * 0.01, 2) for v in range(0, 51)]
            for novelty in (0.0, 0.1, 0.19, 0.25, 0.5)
            if self._flags(engine, config, 1.0, self_ref,
                           novelty).is_self_narrative_blocked
            != self._flags(engine, config, 0.05, self_ref,
                           novelty).is_self_narrative_blocked
        ]

        assert flips, (
            "the entropy substitution no longer changes any decision. If the "
            "density branch was removed or subsumed, this finding is closed — "
            "delete the test rather than leaving a claim that is not true.")
        assert all(0.24 < self_ref <= 0.30 for self_ref, _ in flips), (
            f"flips outside the predicted window: {flips}. The window is "
            "where the density branch's 0.8x self-reference bound reaches "
            "something the novelty branch does not; flips elsewhere mean the "
            "reading of _apply_thresholds is wrong, not just incomplete.")

    def test_the_substitution_over_blocks_rather_than_under_blocks(self, engine):
        """Direction matters: this is not a safety hole, it is noise."""
        config = load_cep_config()

        absent = self._flags(engine, config, 1.0, 0.26, 0.1)
        measured_high = self._flags(engine, config, 0.05, 0.26, 0.1)

        assert absent.is_self_narrative_blocked
        assert not measured_high.is_self_narrative_blocked


class TestTheStabilitySubstitutionIsInert:
    def test_stability_changes_no_flag(self, engine):
        text = "I was hurt. I suffer. I remember what happened to me."

        outcomes = {
            engine.evaluate_response(
                raw_text=text, phi=0.5, entropy=0.3,
                unified_state={"stability": s, "time_delta": 1.0},
            ).flags.__dict__.__str__()
            for s in (0.0, 0.8, 1.0)
        }

        assert len(outcomes) == 1, (
            "echo_stability now reaches a decision, so the 0.8 substitution "
            "in guard_processor.py stopped being a reporting-only fabrication "
            "and needs the same handling phi and entropy got")

    def test_it_still_reaches_the_reported_metrics(self, engine):
        """The control: inert as a gate is not the same as unused."""
        metrics = engine.evaluate_response(
            raw_text="x", phi=0.5, entropy=0.3,
            unified_state={"stability": 0.42, "time_delta": 1.0}).metrics

        assert metrics.echo_stability == pytest.approx(0.42), (
            "a fabricated stability still lands in the reported metrics even "
            "though it gates nothing — which is why it is recorded rather "
            "than dismissed")
