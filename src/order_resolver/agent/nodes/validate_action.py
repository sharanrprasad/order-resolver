from decimal import Decimal
from typing import Any

from order_resolver.agent.state import (
    SupportState,
    ValidationResult,
)
from order_resolver.agent.types import SupportModelNode
from order_resolver.services import ReadServices

# Amounts greater than this should not be approved for refund.
APPROVAL_THRESHOLD = Decimal("100")



def create_validate_action_node(
    services: ReadServices,
) -> SupportModelNode:

    async def validate_action(
        state: SupportState,
    ) -> dict[str, Any]:

        proposed_action = state["proposed_action"]
        customer_id = state["customer_id"]
        order_id = state.get("order_id")

        if proposed_action.action == "refund":
            if order_id is None:
                return {
                    "validation_result": ValidationResult(
                        valid=False,
                        reason="An order ID is required for a refund.",
                    ),
                    "requires_approval": False,
                }

            if proposed_action.amount is None:
                return {
                    "validation_result": ValidationResult(
                        valid=False,
                        reason="A refund amount is required.",
                    ),
                    "requires_approval": False,
                }

            # Not making this a tool call is intentional as tools return LLM friendly results but want the result directly here.
            refundable_amount = await services.refunds.calculate(
                customer_id,
                order_id,
            )

            if proposed_action.amount > refundable_amount.refundable_amount:
                return {
                    "validation_result": ValidationResult(
                        valid=False,
                        reason="The proposed refund exceeds the refundable amount.",
                    ),
                    "requires_approval": False,
                }

            return {
                "validation_result": ValidationResult(
                    valid=True,
                ),
                # Human approval action triggered.
                "requires_approval": (
                    proposed_action.amount > APPROVAL_THRESHOLD
                ),
            }

        if proposed_action.action == "cancel":
            if order_id is None:
                return {
                    "validation_result": ValidationResult(
                        valid=False,
                        reason="An order ID is required for cancellation.",
                    ),
                    "requires_approval": False,
                }

            order = await services.orders.get(
                customer_id,
                order_id,
            )

            if order.status not in {"pending", "processing"}:
                return {
                    "validation_result": ValidationResult(
                        valid=False,
                        reason="The order can no longer be cancelled.",
                    ),
                    "requires_approval": False,
                }

            return {
                "validation_result": ValidationResult(
                    valid=True,
                ),
                "requires_approval": False,
            }

        if proposed_action.action == "no_action":
            return {
                "validation_result": ValidationResult(
                    valid=True,
                ),
                "requires_approval": False,
            }

        return {
            "validation_result": ValidationResult(
                valid=False,
                reason="Unsupported proposed action.",
            ),
            "requires_approval": False,
        }

    return validate_action