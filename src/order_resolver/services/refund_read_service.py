from decimal import Decimal
from uuid import UUID

from order_resolver.repositories.order_repository import OrderRepository
from order_resolver.repositories.refund_repository import RefundRepository
from order_resolver.services.read_models import RefundCalculation
from order_resolver.services.resource_not_found_error import ResourceNotFoundError


class RefundReadService:
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
