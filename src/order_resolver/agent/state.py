from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal, Required
from uuid import UUID

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class SupportIntent(StrEnum):
    TRACK_ORDER = "track_order"
    CANCEL_ORDER = "cancel_order"
    REFUND = "refund"
    DAMAGED_ITEM = "damaged_item"
    OTHER = "other"


# This is an intermediate state. Doesn't belong to the final Support State. Only the initial request node uses this.
class ParsedRequest(BaseModel):
    intent: SupportIntent
    order_id: UUID | None = None
    explanation: str


class Customer(BaseModel):
    id: UUID
    name: str
    email: str
    membership_tier: str


class Order(BaseModel):
    id: UUID
    customer_id: UUID
    status: str
    total: Decimal


class Shipment(BaseModel):
    id: UUID
    order_id: UUID
    carrier: str
    tracking_number: str
    status: str


class ProposedAction(BaseModel):
    action: Literal[
        "refund",
        "cancel",
        "no_action",
    ]

    reason: str
    amount: Decimal | None = None

    confidence: float = Field(
        ge=0,
        le=1,
    )


class ValidationResult(BaseModel):
    valid: bool
    reason: str | None = None


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ExecutedAction(BaseModel):
    action: str
    success: bool
    reference_id: UUID | None = None
    message: str | None = None


class ResolutionStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


# All fields are optional because nodes return partial state updates.
class SupportStateBase(TypedDict, total=False):
    order_id: UUID
    intent: SupportIntent

    customer: Customer
    order: Order
    shipment: Shipment

    relevant_policies: list[str]

    proposed_action: ProposedAction
    validation_result: ValidationResult

    requires_approval: bool
    approval_status: ApprovalStatus

    executed_action: ExecutedAction
    final_response: str
    resolution_status: ResolutionStatus


class SupportState(SupportStateBase):
    # Messages sent to and by to the LLM.
    # add_messages appends new messages and safely handles message IDs/updates.
    messages: Required[Annotated[list[BaseMessage], add_messages]]
    customer_id: Required[UUID]
