from uuid import UUID

from order_resolver.repositories.order_repository import OrderRepository
from order_resolver.services.read_models import (
    OrderDetails,
    OrderItemDetails,
    ShipmentDetails,
)
from order_resolver.services.resource_not_found_error import ResourceNotFoundError


class OrderReadService:
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
