from order_resolver.agent.state import (
    ApprovalStatus,
    ExecutedAction,
    SupportIntent,
    SupportState,
)
from order_resolver.agent.types import (
    SupportModelNode,
    SupportNodeReturnType,
)
from order_resolver.services import ResourceNotFoundError, Services


# Once the request is validated then we route here to actually execute the proposed action.
def create_execute_action_node(
    services: Services,
) -> SupportModelNode:

    async def execute_action(
        state: SupportState,
    ) -> SupportNodeReturnType:
        proposed_action = state.get("proposed_action")
        if proposed_action is None:
            raise RuntimeError("proposed_action is missing in execute_action node")

        requires_approval = state.get("requires_approval")
        if requires_approval is None:
            raise RuntimeError("requires_approval is missing in execute_action node")

        order_id = state.get("order_id")

        # Extra defense. Check if human approval was required and whether it was approved.
        if requires_approval:
            approval_status = state.get("approval_status")
            if approval_status is None:
                raise RuntimeError("approval_status is missing in execute_action node")
            if approval_status != ApprovalStatus.APPROVED:
                return {
                    "executed_action": ExecutedAction(
                        success=False,
                        action=proposed_action.action,
                        message="Required human approval was not granted.",
                    )
                }

        if proposed_action.action == "refund":
            customer_id = state.get("customer_id")
            if customer_id is None:
                raise RuntimeError("customer_id is missing in execute_action node")
            if order_id is None:
                raise RuntimeError("order_id is missing in execute_action node")
            if proposed_action.amount is None:
                raise RuntimeError("refund amount is missing in execute_action node")

            intent = state.get("intent")
            if intent is None:
                raise RuntimeError("intent is missing in execute_action node")

            try:
                refund = await services.refunds.issue(
                    customer_id=customer_id,
                    order_id=order_id,
                    amount=proposed_action.amount,
                    damaged_item_claim=(intent == SupportIntent.DAMAGED_ITEM),
                    approval_granted=(
                        state.get("approval_status") == ApprovalStatus.APPROVED
                    ),
                )
            except (ResourceNotFoundError, ValueError) as exc:
                return {
                    "executed_action": ExecutedAction(
                        action="refund",
                        success=False,
                        message=str(exc),
                    )
                }

            return {
                "executed_action": ExecutedAction(
                    action="refund",
                    success=True,
                    reference_id=refund.id,
                )
            }

        if proposed_action.action == "cancel":
            customer_id = state.get("customer_id")
            if customer_id is None:
                raise RuntimeError("customer_id is missing in execute_action node")
            if order_id is None:
                raise RuntimeError("order_id is missing in execute_action node")

            try:
                await services.orders.cancel(
                    customer_id=customer_id,
                    order_id=order_id,
                )
            except (ResourceNotFoundError, ValueError) as exc:
                return {
                    "executed_action": ExecutedAction(
                        action="cancel",
                        success=False,
                        message=str(exc),
                    )
                }

            return {
                "executed_action": ExecutedAction(
                    action="cancel",
                    success=True,
                )
            }

        return {
            "executed_action": ExecutedAction(
                action="no_action",
                success=True,
            )
        }

    return execute_action
