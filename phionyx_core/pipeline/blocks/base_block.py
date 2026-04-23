"""
Base Block Implementation
=========================

Base implementation for pipeline blocks.
"""

from ...pipeline.base import PipelineBlock


class BaseBlock(PipelineBlock):
    """
    Base implementation with common functionality.
    """

    def __init__(self, block_id: str):
        super().__init__(block_id)

