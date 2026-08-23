from decimal import Decimal

from order_resolver.agent.state import (
    SupportIntent,
    SupportState,
    ValidationResult,
)
from order_resolver.agent.types import SupportModelNode, SupportNodeReturnType
from order_resolver.services import ResourceNotFoundError, Services

# Amounts greater than this should not be approved for refund.
APPROVAL_THRESHOLD = Decimal(100)


def create_validate_action_node(
    services: Services,
) -> SupportModelNode:

    async def validate_action(
        state: SupportState,
    ) -> SupportNodeReturnType:
        proposed_action = state.get("proposed_action")
        if proposed_action is None:
            raise RuntimeError("proposed_action is missing in validate_action node")

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

            if proposed_action.amount <= 0:
                return {
                    "validation_result": ValidationResult(
                        valid=False,
                        reason="The refund amount must be greater than zero.",
                    ),
                    "requires_approval": False,
                }

            customer_id = state.get("customer_id")
            if customer_id is None:
                raise RuntimeError("customer_id is missing in validate_action node")

            intent = state.get("intent")
            if intent is None:
                raise RuntimeError("intent is missing in validate_action node")

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

            damaged_item_claim = intent == SupportIntent.DAMAGED_ITEM
            order = await services.orders.get(customer_id, order_id)
            try:
                shipment = await services.orders.get_shipment(
                    customer_id,
                    order_id,
                )
            except ResourceNotFoundError:
                shipment = None

            lost_shipment = shipment is not None and shipment.status == "lost"
            delivered_damaged_item = damaged_item_claim and (
                order.status == "delivered"
                or (shipment is not None and shipment.status == "delivered")
            )
            if not lost_shipment and not delivered_damaged_item:
                return {
                    "validation_result": ValidationResult(
                        valid=False,
                        reason=(
                            "Refunds are allowed only for lost shipments or delivered "
                            "items reported damaged."
                        ),
                    ),
                    "requires_approval": False,
                }

            return {
                "validation_result": ValidationResult(
                    valid=True,
                ),
                # Human approval action triggered.
                "requires_approval": (
                    damaged_item_claim or proposed_action.amount > APPROVAL_THRESHOLD
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

            customer_id = state.get("customer_id")
            if customer_id is None:
                raise RuntimeError("customer_id is missing in validate_action node")

            order = await services.orders.get(
                customer_id,
                order_id,
            )

            if order.status not in {"pending", "paid", "processing"}:
                return {
                    "validation_result": ValidationResult(
                        valid=False,
                        reason="The order can no longer be cancelled.",
                    ),
                    "requires_approval": False,
                }

            try:
                shipment = await services.orders.get_shipment(
                    customer_id,
                    order_id,
                )
            except ResourceNotFoundError:
                shipment = None

            if shipment is not None and shipment.status in {
                "shipped",
                "in_transit",
                "delivered",
                "lost",
            }:
                return {
                    "validation_result": ValidationResult(
                        valid=False,
                        reason="The order cannot be cancelled after shipment.",
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
