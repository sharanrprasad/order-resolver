from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from order_resolver.db.models import (
    Order,
    OrderItem,
    OrderStatus,
    Refund,
    RefundStatus,
    Shipment,
    ShipmentStatus,
)


class OrderRepository:
    """Access orders through customer-scoped queries only."""

    _CANCELLABLE_STATUSES = (
        OrderStatus.pending,
        OrderStatus.paid,
        OrderStatus.processing,
    )
    _STARTED_SHIPMENT_STATUSES = (
        ShipmentStatus.shipped,
        ShipmentStatus.in_transit,
        ShipmentStatus.delivered,
        ShipmentStatus.lost,
    )

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get(self, customer_id: UUID, order_id: UUID) -> Order | None:
        async with self._session_factory() as session:
            return await session.scalar(
                select(Order).where(
                    Order.id == order_id,
                    Order.customer_id == customer_id,
                )
            )

    async def get_items(
        self, customer_id: UUID, order_id: UUID
    ) -> list[OrderItem] | None:
        async with self._session_factory() as session:
            owns_order = await session.scalar(
                select(Order.id).where(
                    Order.id == order_id,
                    Order.customer_id == customer_id,
                )
            )
            if owns_order is None:
                return None

            result = await session.scalars(
                select(OrderItem)
                .where(OrderItem.order_id == order_id)
                .order_by(OrderItem.id)
            )
            return list(result)

    async def get_shipment(
        self, customer_id: UUID, order_id: UUID
    ) -> Shipment | None:
        async with self._session_factory() as session:
            return await session.scalar(
                select(Shipment)
                .join(Order, Shipment.order_id == Order.id)
                .where(
                    Shipment.order_id == order_id,
                    Order.customer_id == customer_id,
                )
            )

    async def cancel(self, customer_id: UUID, order_id: UUID) -> Order | None:
        """Cancel an owned order after rechecking current state."""
        async with self._session_factory() as session, session.begin():
            order = await session.scalar(
                select(Order).where(
                    Order.id == order_id,
                    Order.customer_id == customer_id,
                )
            )
            if order is None:
                return None

            # Returning an already-cancelled order makes retries harmless.
            if order.status == OrderStatus.cancelled:
                return order

            if order.status not in self._CANCELLABLE_STATUSES:
                raise ValueError("The order can no longer be cancelled.")

            shipment_status = await session.scalar(
                select(Shipment.status).where(Shipment.order_id == order_id)
            )
            if shipment_status in self._STARTED_SHIPMENT_STATUSES:
                raise ValueError("The order cannot be cancelled after shipment.")

            if order.status == OrderStatus.paid:
                session.add(
                    Refund(
                        order_id=order.id,
                        amount=order.total,
                        reason="Payment reversal for cancelled order",
                        status=RefundStatus.completed,
                    )
                )

            order.status = OrderStatus.cancelled
            await session.flush()
            return order
