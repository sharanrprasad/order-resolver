from typing import Annotated, Any, TypedDict
from uuid import UUID

from langgraph.graph.message import add_messages


class SupportState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    customer_id: UUID
    order_id: UUID
    intent: str
    customer: dict[str, Any]
    order: dict[str, Any]
    shipment: dict[str, Any]
    relevant_policies: list[str]
    proposed_action: dict[str, Any]
    requires_approval: bool
    approval_status: str
    final_response: str
