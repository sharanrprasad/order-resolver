from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from order_resolver.db.models import Order, Refund, RefundStatus


class RefundRepository:
    """Read refund totals only after proving ownership in the same query."""

    _RESERVED_STATUSES = (
        RefundStatus.pending,
        RefundStatus.approved,
        RefundStatus.completed,
    )

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def total_reserved(self, customer_id: UUID, order_id: UUID) -> Decimal:
        async with self._session_factory() as session:
            amount = await session.scalar(
                select(func.coalesce(func.sum(Refund.amount), 0))
                .join(Order, Refund.order_id == Order.id)
                .where(
                    Refund.order_id == order_id,
                    Order.customer_id == customer_id,
                    Refund.status.in_(self._RESERVED_STATUSES),
                )
            )
            return Decimal(amount or 0)
