from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ReadModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CustomerDetails(ReadModel):
    id: UUID
    name: str
    email: str
    membership_tier: str
    created_at: datetime


class OrderDetails(ReadModel):
    id: UUID
    status: str
    total: Decimal
    created_at: datetime


class OrderItemDetails(ReadModel):
    id: UUID
    order_id: UUID
    product_name: str
    quantity: int
    unit_price: Decimal


class ShipmentDetails(ReadModel):
    id: UUID
    order_id: UUID
    carrier: str
    tracking_number: str
    status: str
    estimated_delivery: date | None
    delivered_at: datetime | None


class PolicyDetails(ReadModel):
    source: str
    content: str
    score: float


class RefundCalculation(ReadModel):
    order_id: UUID
    order_total: Decimal
    already_reserved: Decimal
    refundable_amount: Decimal
    note: str = (
        "This is an arithmetic estimate only; policy eligibility must be checked "
        "separately."
    )
