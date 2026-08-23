from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ServiceModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CustomerDetails(ServiceModel):
    id: UUID
    name: str
    email: str
    membership_tier: str
    created_at: datetime


class OrderDetails(ServiceModel):
    id: UUID
    status: str
    total: Decimal
    created_at: datetime


class OrderItemDetails(ServiceModel):
    id: UUID
    order_id: UUID
    product_name: str
    quantity: int
    unit_price: Decimal


class ShipmentDetails(ServiceModel):
    id: UUID
    order_id: UUID
    carrier: str
    tracking_number: str
    status: str
    estimated_delivery: date | None
    delivered_at: datetime | None


class PolicyDetails(ServiceModel):
    source: str
    content: str
    score: float


class RefundCalculation(ServiceModel):
    order_id: UUID
    order_total: Decimal
    already_reserved: Decimal
    refundable_amount: Decimal
    note: str = (
        "This is an arithmetic estimate only; policy eligibility must be checked "
        "separately."
    )


class RefundDetails(ServiceModel):
    id: UUID
    order_id: UUID
    amount: Decimal
    reason: str
    status: str
    created_at: datetime
