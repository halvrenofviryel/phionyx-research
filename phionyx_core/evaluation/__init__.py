"""
Human Comparative Evaluation Framework
=======================================

Framework for structured comparison between Phionyx pipeline outputs,
human expert responses, and knowledge worker responses.

Roadmap Faz 2: Human Comparative Evaluation
"""

from .task_set import EvalTask, TaskCategory, TaskSet
from .scoring import EloRating, PreferenceScorer, CalibrationMetrics
from .report_generator import EvalReport, EvalReportGenerator

__all__ = [
    "EvalTask",
    "TaskCategory",
    "TaskSet",
    "EloRating",
    "PreferenceScorer",
    "CalibrationMetrics",
    "EvalReport",
    "EvalReportGenerator",
]
