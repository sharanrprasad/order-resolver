from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from order_resolver.db.models import (
    Order,
    OrderStatus,
    Refund,
    RefundStatus,
    Shipment,
    ShipmentStatus,
)


class RefundRepository:
    """Access refunds only after proving customer ownership."""

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

    async def issue(
        self,
        customer_id: UUID,
        order_id: UUID,
        amount: Decimal,
        *,
        damaged_item_claim: bool,
    ) -> Refund | None:
        """Create a refund or return an existing matching refund."""
        async with self._session_factory() as session, session.begin():
            order = await session.scalar(
                select(Order).where(
                    Order.id == order_id,
                    Order.customer_id == customer_id,
                )
            )
            if order is None:
                return None

            shipment_status = await session.scalar(
                select(Shipment.status).where(Shipment.order_id == order_id)
            )
            lost_shipment = shipment_status == ShipmentStatus.lost
            delivered_damaged_item = damaged_item_claim and (
                order.status == OrderStatus.delivered
                or shipment_status == ShipmentStatus.delivered
            )
            if not lost_shipment and not delivered_damaged_item:
                raise ValueError(
                    "Refunds are allowed only for lost shipments or delivered "
                    "items reported damaged."
                )

            reason = (
                "Confirmed lost shipment"
                if lost_shipment
                else "Delivered item reported damaged"
            )
            existing_refund = await session.scalar(
                select(Refund).where(
                    Refund.order_id == order_id,
                    Refund.amount == amount,
                    Refund.reason == reason,
                    Refund.status.in_(self._RESERVED_STATUSES),
                )
            )
            if existing_refund is not None:
                return existing_refund

            reserved = await session.scalar(
                select(func.coalesce(func.sum(Refund.amount), 0)).where(
                    Refund.order_id == order_id,
                    Refund.status.in_(self._RESERVED_STATUSES),
                )
            )
            refundable = max(
                order.total - Decimal(reserved or 0),
                Decimal("0.00"),
            )
            if amount > refundable:
                raise ValueError(
                    "The refund amount exceeds the remaining refundable amount."
                )

            refund = Refund(
                order_id=order_id,
                amount=amount,
                reason=reason,
                status=RefundStatus.completed,
            )
            session.add(refund)
            await session.flush()
            return refund
