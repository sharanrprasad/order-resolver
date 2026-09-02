"""Deterministic commerce data for the integration suite.

One customer, seven orders covering the scenarios in ``docs/`` and
``AGENTS.md`` (lost shipment, cancellable order, already-refunded order,
high-value refund, and so on). IDs are fixed so tests can address a row by
name.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from order_resolver.db.models import (
    Customer,
    Order,
    OrderItem,
    OrderStatus,
    Refund,
    RefundStatus,
    Shipment,
    ShipmentStatus,
)

CUSTOMER_ID = UUID("00000000-0000-0000-0000-0000000000aa")
OTHER_CUSTOMER_ID = UUID("00000000-0000-0000-0000-0000000000bb")


def _order_id(order_number: int) -> UUID:
    return UUID(f"00000000-0000-0000-0000-{order_number:012d}")


ORDER_DELIVERED = _order_id(101)  # delivered, undamaged
ORDER_IN_TRANSIT = _order_id(102)  # shipped + in_transit: not cancellable, not lost
ORDER_LOST = _order_id(103)  # shipment lost: standalone refund, < $100
ORDER_PROCESSING = _order_id(104)  # processing, no shipment: cancellable
ORDER_REFUNDED = _order_id(105)  # delivered, already fully refunded
ORDER_HIGH_VALUE = _order_id(106)  # delivered, $250: refund needs approval
ORDER_OLD_DELIVERED = _order_id(107)  # delivered 45 days ago, undamaged

_NOW = datetime.now(UTC)


async def seed_commerce_data(session: AsyncSession) -> None:
    """Insert the fixed customer, orders, shipments and the pre-existing refund."""
    session.add(
        Customer(
            id=CUSTOMER_ID,
            name="Alex Learner",
            email="alex@example.com",
            membership_tier="gold",
        )
    )

    specs = [
        (ORDER_DELIVERED, OrderStatus.delivered, Decimal("49.99"), ShipmentStatus.delivered, 5),
        (ORDER_IN_TRANSIT, OrderStatus.shipped, Decimal("79.00"), ShipmentStatus.in_transit, 7),
        (ORDER_LOST, OrderStatus.shipped, Decimal("65.00"), ShipmentStatus.lost, 14),
        (ORDER_PROCESSING, OrderStatus.processing, Decimal("35.00"), None, None),
        (ORDER_REFUNDED, OrderStatus.delivered, Decimal("89.00"), ShipmentStatus.delivered, 3),
        (ORDER_HIGH_VALUE, OrderStatus.delivered, Decimal("250.00"), ShipmentStatus.delivered, 2),
        (ORDER_OLD_DELIVERED, OrderStatus.delivered, Decimal("55.00"), ShipmentStatus.delivered, 45),
    ]

    for order_id, status, total, shipment_status, shipped_days_ago in specs:
        order = Order(id=order_id, customer_id=CUSTOMER_ID, status=status, total=total)
        order.items.append(
            OrderItem(product_name=f"Demo product {order_id.int % 1000}", quantity=1, unit_price=total)
        )
        if shipment_status is not None:
            order.shipment = Shipment(
                carrier="DemoPost",
                tracking_number=f"TRACK-{order_id.int % 1000}",
                status=shipment_status,
                delivered_at=(
                    _NOW - timedelta(days=shipped_days_ago)
                    if shipment_status == ShipmentStatus.delivered
                    else None
                ),
            )
        session.add(order)

    session.add(
        Refund(
            order_id=ORDER_REFUNDED,
            amount=Decimal("89.00"),
            reason="Previously refunded demo order",
            status=RefundStatus.completed,
        )
    )
    await session.flush()
