"""Insert deterministic commerce demo records."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

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
from order_resolver.db.session import SessionLocal


def seed() -> None:
    with SessionLocal.begin() as session:
        if session.scalar(select(Customer.id).limit(1)) is not None:
            print("Database already contains customers; demo data seed skipped.")
            return
        now = datetime.now(UTC)
        today = now.date()
        customer = Customer(
            name="Alex Learner", email="alex@example.com", membership_tier="gold"
        )
        session.add(customer)
        session.flush()
        scenarios = [
            (
                101,
                OrderStatus.delivered,
                Decimal("49.99"),
                ShipmentStatus.delivered,
                today - timedelta(days=5),
            ),
            (
                102,
                OrderStatus.shipped,
                Decimal("79.00"),
                ShipmentStatus.in_transit,
                today - timedelta(days=7),
            ),
            (
                103,
                OrderStatus.shipped,
                Decimal("65.00"),
                ShipmentStatus.lost,
                today - timedelta(days=14),
            ),
            (104, OrderStatus.processing, Decimal("35.00"), None, None),
            (
                105,
                OrderStatus.delivered,
                Decimal("89.00"),
                ShipmentStatus.delivered,
                today - timedelta(days=3),
            ),
            (
                106,
                OrderStatus.delivered,
                Decimal("250.00"),
                ShipmentStatus.delivered,
                today - timedelta(days=2),
            ),
            (
                107,
                OrderStatus.delivered,
                Decimal("55.00"),
                ShipmentStatus.delivered,
                today - timedelta(days=45),
            ),
        ]
        orders_by_number: dict[int, Order] = {}
        for order_number, order_status, total, shipment_status, eta in scenarios:
            order_id = UUID(f"00000000-0000-0000-0000-{order_number:012d}")
            order = Order(
                id=order_id,
                customer_id=customer.id,
                status=order_status,
                total=total,
                created_at=now - timedelta(days=50 if order_number == 107 else 10),
            )
            order.items.append(
                OrderItem(
                    product_name=f"Demo product {order_number}",
                    quantity=1,
                    unit_price=total,
                )
            )
            if shipment_status:
                order.shipment = Shipment(
                    carrier="DemoPost",
                    tracking_number=f"TRACK-{order_number}",
                    status=shipment_status,
                    estimated_delivery=eta,
                    delivered_at=now - timedelta(days=3)
                    if shipment_status == ShipmentStatus.delivered
                    else None,
                )
            session.add(order)
            orders_by_number[order_number] = order
        session.add(
            Refund(
                order_id=orders_by_number[105].id,
                amount=Decimal("89.00"),
                reason="Previously refunded demo order",
                status=RefundStatus.completed,
            )
        )
    print("Demo data inserted.")


if __name__ == "__main__":
    seed()
