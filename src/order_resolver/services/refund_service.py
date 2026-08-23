from decimal import Decimal
from uuid import UUID

from order_resolver.repositories.order_repository import OrderRepository
from order_resolver.repositories.refund_repository import RefundRepository
from order_resolver.services.models import RefundCalculation, RefundDetails
from order_resolver.services.resource_not_found_error import ResourceNotFoundError


class RefundService:
    _APPROVAL_THRESHOLD = Decimal(100)

    def __init__(
        self,
        order_repository: OrderRepository,
        refund_repository: RefundRepository,
    ) -> None:
        self._order_repository = order_repository
        self._refund_repository = refund_repository

    async def calculate(
        self, customer_id: UUID, order_id: UUID
    ) -> RefundCalculation:
        order = await self._order_repository.get(customer_id, order_id)
        if order is None:
            raise ResourceNotFoundError("Order not found.")

        reserved = await self._refund_repository.total_reserved(customer_id, order_id)
        refundable = max(order.total - reserved, Decimal("0.00"))
        return RefundCalculation(
            order_id=order.id,
            order_total=order.total,
            already_reserved=reserved,
            refundable_amount=refundable,
        )

    async def issue(
        self,
        customer_id: UUID,
        order_id: UUID,
        amount: Decimal,
        *,
        damaged_item_claim: bool = False,
        approval_granted: bool = False,
    ) -> RefundDetails:
        """Issue an eligible standalone refund through the trusted write boundary."""
        if amount <= 0:
            raise ValueError("The refund amount must be greater than zero.")
        if amount != amount.quantize(Decimal("0.01")):
            raise ValueError("The refund amount cannot have more than two decimals.")

        order = await self._order_repository.get(customer_id, order_id)
        if order is None:
            raise ResourceNotFoundError("Order not found.")
        shipment = await self._order_repository.get_shipment(customer_id, order_id)
        lost_shipment = shipment is not None and shipment.status.value == "lost"
        delivered_damaged_item = damaged_item_claim and (
            order.status.value == "delivered"
            or (
                shipment is not None
                and shipment.status.value == "delivered"
            )
        )
        if not lost_shipment and not delivered_damaged_item:
            raise ValueError(
                "Refunds are allowed only for lost shipments or delivered items "
                "reported damaged."
            )

        if (
            damaged_item_claim or amount > self._APPROVAL_THRESHOLD
        ) and not approval_granted:
            raise ValueError("Required human approval was not granted.")

        refund = await self._refund_repository.issue(
            customer_id,
            order_id,
            amount,
            damaged_item_claim=damaged_item_claim,
        )
        if refund is None:
            raise ResourceNotFoundError("Order not found.")
        return RefundDetails.model_validate(refund)
