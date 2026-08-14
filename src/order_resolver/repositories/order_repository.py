from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from order_resolver.db.models import (
    Order,
    OrderItem,
    Shipment,
)


class OrderRepository:
    """Read order data through customer-scoped queries only."""

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
