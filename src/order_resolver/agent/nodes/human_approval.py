from typing import Any

from langgraph.types import interrupt

from order_resolver.agent.state import (
    ApprovalStatus,
    SupportState,
)
from order_resolver.agent.types import SupportModelNode


def create_human_approval_node() -> SupportModelNode:

    async def human_approval(
        state: SupportState,
    ) -> dict[str, Any]:

        proposed_action = state["proposed_action"]

       # When interruption is resumed this whole node is run again, so don't do any actions in this node that is not okay to run multiple times.
        decision = interrupt(
            {
                "type": "approval_required",
                "message": "This action requires human approval.",
                "proposed_action": proposed_action.model_dump(mode="json"),
            }
        )

        # When the graph is resumes the above function is skipped and this is what is returned.
        approved = decision["approved"]

        return {
            "approval_status": (
                ApprovalStatus.APPROVED
                if approved
                else ApprovalStatus.REJECTED
            )
        }

    return human_approval