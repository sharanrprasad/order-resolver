from uuid import UUID

from order_resolver.repositories.order_repository import OrderRepository
from order_resolver.services.models import (
    OrderDetails,
    OrderItemDetails,
    ShipmentDetails,
)
from order_resolver.services.resource_not_found_error import ResourceNotFoundError


class OrderService:
    _CANCELLABLE_STATUSES = frozenset({"pending", "paid", "processing"})
    _STARTED_SHIPMENT_STATUSES = frozenset({
        "shipped",
        "in_transit",
        "delivered",
        "lost",
    })

    def __init__(self, repository: OrderRepository) -> None:
        self._repository = repository

    async def get(self, customer_id: UUID, order_id: UUID) -> OrderDetails:
        order = await self._repository.get(customer_id, order_id)
        if order is None:
            raise ResourceNotFoundError("Order not found.")
        return OrderDetails.model_validate(order)

    async def get_items(
        self, customer_id: UUID, order_id: UUID
    ) -> list[OrderItemDetails]:
        items = await self._repository.get_items(customer_id, order_id)
        if items is None:
            raise ResourceNotFoundError("Order not found.")
        return [OrderItemDetails.model_validate(item) for item in items]

    async def get_shipment(
        self, customer_id: UUID, order_id: UUID
    ) -> ShipmentDetails:
        # Check the order separately so "no shipment" is distinguishable from an
        # unknown/cross-customer order without weakening the ownership boundary.
        await self.get(customer_id, order_id)
        shipment = await self._repository.get_shipment(customer_id, order_id)
        if shipment is None:
            raise ResourceNotFoundError("No shipment found for this order.")
        return ShipmentDetails.model_validate(shipment)

    async def cancel(self, customer_id: UUID, order_id: UUID) -> OrderDetails:
        """Cancel an owned order only while fulfilment has not started."""
        order = await self.get(customer_id, order_id)
        if order.status == "cancelled":
            return order
        if order.status not in self._CANCELLABLE_STATUSES:
            raise ValueError("The order can no longer be cancelled.")

        shipment = await self._repository.get_shipment(customer_id, order_id)
        if (
            shipment is not None
            and shipment.status.value in self._STARTED_SHIPMENT_STATUSES
        ):
            raise ValueError("The order cannot be cancelled after shipment.")

        cancelled_order = await self._repository.cancel(customer_id, order_id)
        if cancelled_order is None:
            raise ResourceNotFoundError("Order not found.")
        return OrderDetails.model_validate(cancelled_order)
