"""
Pipeline Package
================

Defines the 46-block canonical pipeline architecture (v3.8.0).
"""

from .base import BlockContext, BlockResult, PipelineBlock

__all__ = [
    'PipelineBlock',
    'BlockResult',
    'BlockContext',
]

