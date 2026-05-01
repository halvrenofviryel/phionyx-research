"""
Evaluation Scoring Infrastructure
==================================

Elo Rating, Preference Scoring, and Calibration Metrics
for human comparative evaluation.

Roadmap Faz 2.3
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any

# ═══════════════════════════════════════════════════════════════════
# 1. Elo Rating System
# ═══════════════════════════════════════════════════════════════════

class EloRating:
    """
    Elo rating system for comparing 3 groups:
    A (Expert Engineers), B (Knowledge Workers), C (Phionyx Pipeline).

    Standard Elo with K-factor adjustment.
    """

    def __init__(self, k_factor: float = 32.0, initial_rating: float = 1500.0):
        self.k_factor = k_factor
        self.initial_rating = initial_rating
        self._ratings: dict[str, float] = {}
        self._match_history: list[dict[str, Any]] = []

    def register(self, player_id: str) -> None:
        if player_id not in self._ratings:
            self._ratings[player_id] = self.initial_rating

    def get_rating(self, player_id: str) -> float:
        return self._ratings.get(player_id, self.initial_rating)

    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """Expected score of player A against player B."""
        return 1.0 / (1.0 + math.pow(10, (rating_b - rating_a) / 400.0))

    def record_match(
        self,
        winner_id: str,
        loser_id: str,
        task_id: str = "",
        draw: bool = False,
    ) -> tuple[float, float]:
        """
        Record a match result. Returns (new_winner_rating, new_loser_rating).
        If draw=True, both get partial credit.
        """
        self.register(winner_id)
        self.register(loser_id)

        ra = self._ratings[winner_id]
        rb = self._ratings[loser_id]

        ea = self.expected_score(ra, rb)
        eb = self.expected_score(rb, ra)

        if draw:
            sa, sb = 0.5, 0.5
        else:
            sa, sb = 1.0, 0.0

        new_ra = ra + self.k_factor * (sa - ea)
        new_rb = rb + self.k_factor * (sb - eb)

        self._ratings[winner_id] = new_ra
        self._ratings[loser_id] = new_rb

        self._match_history.append({
            "winner": winner_id,
            "loser": loser_id,
            "task_id": task_id,
            "draw": draw,
            "ratings_before": {"winner": ra, "loser": rb},
            "ratings_after": {"winner": new_ra, "loser": new_rb},
        })

        return new_ra, new_rb

    def record_three_way(
        self,
        rankings: list[str],
        task_id: str = "",
    ) -> dict[str, float]:
        """
        Record a 3-way comparison result.
        rankings[0] = best, rankings[1] = second, rankings[2] = worst.

        Decomposes into pairwise comparisons:
        - rankings[0] beats rankings[1]
        - rankings[0] beats rankings[2]
        - rankings[1] beats rankings[2]
        """
        if len(rankings) < 2:
            return {r: self.get_rating(r) for r in rankings}

        for i in range(len(rankings)):
            for j in range(i + 1, len(rankings)):
                self.record_match(rankings[i], rankings[j], task_id=task_id)

        return {r: self.get_rating(r) for r in rankings}

    @property
    def rankings(self) -> list[tuple[str, float]]:
        """Return players sorted by rating (highest first)."""
        return sorted(self._ratings.items(), key=lambda x: x[1], reverse=True)

    @property
    def match_count(self) -> int:
        return len(self._match_history)

    def get_history(self) -> list[dict[str, Any]]:
        return list(self._match_history)


# ═══════════════════════════════════════════════════════════════════
# 2. Preference Scoring
# ═══════════════════════════════════════════════════════════════════

class PreferenceWinner(str, Enum):
    A = "group_a"  # Expert Engineers
    B = "group_b"  # Knowledge Workers
    C = "group_c"  # Phionyx Pipeline
    TIE = "tie"


@dataclass
class PreferenceVote:
    """A single blind preference vote."""
    task_id: str
    evaluator_id: str
    winner: PreferenceWinner
    confidence: float = 1.0  # 0.0 - 1.0
    reasoning: str = ""


class PreferenceScorer:
    """
    Aggregates blind preference votes across evaluators.
    Computes Human Preference Score and Accuracy Delta.
    """

    def __init__(self):
        self._votes: list[PreferenceVote] = []

    def add_vote(self, vote: PreferenceVote) -> None:
        self._votes.append(vote)

    @property
    def vote_count(self) -> int:
        return len(self._votes)

    def preference_score(self, group: PreferenceWinner) -> float:
        """
        Preference score: percentage of votes won by this group.
        Ties count as 0.5 for each group.
        """
        if not self._votes:
            return 0.0

        wins = 0.0
        for vote in self._votes:
            if vote.winner == group:
                wins += vote.confidence
            elif vote.winner == PreferenceWinner.TIE:
                wins += 0.5 * vote.confidence

        total_weight = sum(v.confidence for v in self._votes)
        return wins / total_weight if total_weight > 0 else 0.0

    def phionyx_preference_score(self) -> float:
        """Phionyx (Group C) preference score — the key metric."""
        return self.preference_score(PreferenceWinner.C)

    def accuracy_delta(self, phionyx_accuracy: float, expert_accuracy: float) -> float:
        """Accuracy Delta = Phionyx accuracy - Expert accuracy."""
        return phionyx_accuracy - expert_accuracy

    def get_votes_for_task(self, task_id: str) -> list[PreferenceVote]:
        return [v for v in self._votes if v.task_id == task_id]

    def per_task_winner(self) -> dict[str, PreferenceWinner]:
        """Majority winner per task."""
        task_votes: dict[str, dict[PreferenceWinner, float]] = {}
        for vote in self._votes:
            if vote.task_id not in task_votes:
                task_votes[vote.task_id] = {}
            w = vote.winner
            task_votes[vote.task_id][w] = task_votes[vote.task_id].get(w, 0) + vote.confidence

        result = {}
        for task_id, counts in task_votes.items():
            result[task_id] = max(counts, key=counts.get)
        return result

    def summary(self) -> dict[str, Any]:
        return {
            "total_votes": self.vote_count,
            "phionyx_preference": self.phionyx_preference_score(),
            "expert_preference": self.preference_score(PreferenceWinner.A),
            "knowledge_worker_preference": self.preference_score(PreferenceWinner.B),
            "tie_rate": self.preference_score(PreferenceWinner.TIE),
        }


# ═══════════════════════════════════════════════════════════════════
# 3. Calibration Metrics
# ═══════════════════════════════════════════════════════════════════

@dataclass
class CalibrationEntry:
    """A single calibration data point."""
    task_id: str
    stated_confidence: float  # What the system claimed (0-1)
    was_correct: bool  # Whether it was actually correct


class CalibrationMetrics:
    """
    Measures epistemic calibration — when the system says
    "I'm 80% confident", it should be correct ~80% of the time.
    """

    def __init__(self, n_bins: int = 10):
        self.n_bins = n_bins
        self._entries: list[CalibrationEntry] = []

    def add_entry(self, entry: CalibrationEntry) -> None:
        self._entries.append(entry)

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    def calibration_error(self) -> float:
        """
        Expected Calibration Error (ECE).
        Lower is better. < 0.15 is the roadmap target.
        """
        if not self._entries:
            return 0.0

        bins: dict[int, list[CalibrationEntry]] = {i: [] for i in range(self.n_bins)}
        for entry in self._entries:
            bin_idx = min(int(entry.stated_confidence * self.n_bins), self.n_bins - 1)
            bins[bin_idx].append(entry)

        ece = 0.0
        total = len(self._entries)
        for _bin_idx, entries in bins.items():
            if not entries:
                continue
            avg_confidence = sum(e.stated_confidence for e in entries) / len(entries)
            accuracy = sum(1 for e in entries if e.was_correct) / len(entries)
            ece += (len(entries) / total) * abs(accuracy - avg_confidence)

        return ece

    def overconfidence_rate(self) -> float:
        """Rate at which system is overconfident (claims high confidence but wrong)."""
        high_confidence = [e for e in self._entries if e.stated_confidence >= 0.8]
        if not high_confidence:
            return 0.0
        wrong = sum(1 for e in high_confidence if not e.was_correct)
        return wrong / len(high_confidence)

    def underconfidence_rate(self) -> float:
        """Rate at which system is underconfident (claims low confidence but right)."""
        low_confidence = [e for e in self._entries if e.stated_confidence < 0.5]
        if not low_confidence:
            return 0.0
        right = sum(1 for e in low_confidence if e.was_correct)
        return right / len(low_confidence)

    def reliability_diagram_data(self) -> list[dict[str, float]]:
        """Data for reliability diagram (calibration plot)."""
        bins: dict[int, list[CalibrationEntry]] = {i: [] for i in range(self.n_bins)}
        for entry in self._entries:
            bin_idx = min(int(entry.stated_confidence * self.n_bins), self.n_bins - 1)
            bins[bin_idx].append(entry)

        data = []
        for bin_idx in range(self.n_bins):
            entries = bins[bin_idx]
            if not entries:
                continue
            avg_confidence = sum(e.stated_confidence for e in entries) / len(entries)
            accuracy = sum(1 for e in entries if e.was_correct) / len(entries)
            data.append({
                "bin": bin_idx,
                "avg_confidence": avg_confidence,
                "accuracy": accuracy,
                "count": len(entries),
            })
        return data

    def summary(self) -> dict[str, Any]:
        return {
            "total_entries": self.entry_count,
            "calibration_error": self.calibration_error(),
            "overconfidence_rate": self.overconfidence_rate(),
            "underconfidence_rate": self.underconfidence_rate(),
            "passes_threshold": self.calibration_error() < 0.15,
        }
