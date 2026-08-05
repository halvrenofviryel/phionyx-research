"""Action Intent Gate — canonical block 22.

Gates proposed actions through ethics and safety checks.

**`ethics_cleared` no longer defaults to True.** It was
``not ethics_result.get("enforced", False)``, so a turn where the ethics blocks
never ran — or ran and raised, writing ``ethics_result: None`` — produced an
intent marked *cleared by ethics*. When the value was actually ``None`` the
``.get`` raised, the broad handler caught it, and the block still returned
``status="ok"``: two silent failures in a row, ending in an affirmative safety
claim about a check that did not happen.

**This is currently record-only.** ``context.v4_action_intent`` is written here
and read by no code in the repository; ``governance/human_in_the_loop.py:5``
documents ``ActionIntent.requires_approval == True`` as a HITL trigger and that
wiring does not exist. So setting ``ethics_cleared=False`` when ethics was not
measured is inert at runtime and honest on the record. **If the HITL wiring is
ever connected this block moves from the oversight class to safety/ethics
authority and its failure policy must be re-decided** — an unmeasured ethics
result would then hold the turn rather than annotate it.
"""

import logging
from typing import Optional

from ..base import PipelineBlock, BlockContext, BlockResult
from ..outcome import (
    BlockOutcome,
    BlockRunStatus,
    Observation,
    RecoveryAction,
    errored,
    measured_fail,
    measured_pass,
    not_measured,
)

logger = logging.getLogger(__name__)


class ActionIntentGateBlock(PipelineBlock):
    """
    Gates system action intents through safety checks.

    Constructs ActionIntent from cognitive/narrative output and
    verifies ethics clearance before allowing execution.
    """

    def __init__(self):
        super().__init__("action_intent_gate")

    def should_skip(self, context: BlockContext) -> Optional[str]:
        if context.pipeline_version < "3.0.0":
            return "v4_block_requires_pipeline_v3"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        try:
            from ...contracts.v4.action_intent import ActionIntent, ActionType, ReversibilityLevel

            metadata = context.metadata or {}
            ethics_result = metadata.get("ethics_result")
            if isinstance(ethics_result, dict) and ethics_result:
                # `enforced` missing from a result that exists is a legitimate
                # "not enforced". A result that is absent or None is not.
                ethics_ran = True
                cleared = not ethics_result.get("enforced", False)
                measurement = (measured_pass(1, source="ethics_result")
                               if cleared else
                               measured_fail("ethics enforcement was triggered",
                                             items_checked=1))
            else:
                # Not measured, therefore not cleared.
                ethics_ran = False
                cleared = False
                measurement = not_measured(
                    "no ethics result on the turn — clearance was not established",
                    cause="input_absent")

            intent = ActionIntent(
                action_type=ActionType.RESPOND,
                description="Generate response to user",
                reversibility=ReversibilityLevel.FULLY_REVERSIBLE,
                sandbox_required=False,
                confidence=metadata.get("confidence_score", 0.5),
                ethics_cleared=cleared,
            )

            # Check ethics gate
            if not intent.ethics_cleared:
                intent.requires_approval = True
                logger.info(
                    "Action intent requires approval — ethics %s",
                    "enforcement triggered" if ethics_ran else "was not measured")

            context.v4_action_intent = intent

            outcome = BlockOutcome(
                block_id=self.block_id,
                legacy_control_status="ok",
                block_run_status=BlockRunStatus.COMPLETED,
                measurement=measurement,
            )
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "intent_id": intent.intent_id,
                    "action_type": intent.action_type.value,
                    "ethics_cleared": intent.ethics_cleared,
                    "block_outcome": outcome.to_record_fields(),
                },
            )
        except Exception as e:
            logger.error(f"Action intent gate failed: {e}", exc_info=True)
            outcome = BlockOutcome(
                block_id=self.block_id,
                legacy_control_status="skipped",
                block_run_status=BlockRunStatus.FAILED,
                measurement=errored(
                    f"action intent construction raised {type(e).__name__}: {e}"),
                recovery_action=RecoveryAction.FALLBACK,
                observation=Observation.RECORDED,
                operating_mode="degraded",
            )
            return BlockResult(
                block_id=self.block_id,
                status="skipped",
                skip_reason=f"action intent raised {type(e).__name__}",
                error=e,
                data={"action_intent_created": False, "error": str(e),
                      "block_outcome": outcome.to_record_fields()},
            )

    def get_dependencies(self) -> list[str]:
        return ["ethics_post_response"]
