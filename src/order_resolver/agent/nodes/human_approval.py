from langgraph.types import interrupt

from order_resolver.agent.state import (
    ApprovalStatus,
    SupportState,
)
from order_resolver.agent.types import SupportModelNode, SupportNodeReturnType


def create_human_approval_node() -> SupportModelNode:

    async def human_approval(
        state: SupportState,
    ) -> SupportNodeReturnType:
        proposed_action = state.get("proposed_action")
        if proposed_action is None:
            raise RuntimeError("proposed_action is missing in human_approval node")

        # When interruption is resumed this whole node is run again, so don't do
        # anything here that cannot be safely repeated.
        decision = interrupt(
            {
                "type": "approval_required",
                "message": "This action requires human approval.",
                "proposed_action": proposed_action.model_dump(mode="json"),
            }
        )

        # When the graph resumes, interrupt returns the supplied decision.
        if not isinstance(decision, dict) or "approved" not in decision:
            raise RuntimeError("approved is missing from the human approval decision")

        approved = decision.get("approved")
        if not isinstance(approved, bool):
            raise TypeError("approved must be a boolean in the human approval decision")

        return {
            "approval_status": (
                ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
            )
        }

    return human_approval
