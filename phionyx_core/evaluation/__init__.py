"""
Human Comparative Evaluation Framework
=======================================

Framework for structured comparison between Phionyx pipeline outputs,
human expert responses, and knowledge worker responses.

Roadmap Faz 2: Human Comparative Evaluation
"""

from .report_generator import EvalReport, EvalReportGenerator
from .scoring import CalibrationMetrics, EloRating, PreferenceScorer
from .task_set import EvalTask, TaskCategory, TaskSet

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
