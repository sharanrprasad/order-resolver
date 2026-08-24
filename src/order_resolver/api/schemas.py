from decimal import Decimal
from enum import StrEnum
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SupportRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    customer_id: UUID
    message: str = Field(min_length=1, max_length=4_000)


class WorkflowStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    APPROVAL_REQUIRED = "approval_required"


class ProposedActionResponse(BaseModel):
    action: Literal["refund", "cancel", "no_action"]
    reason: str
    amount: Decimal | None = None


class HumanApprovalResponse(BaseModel):
    message: str
    proposed_action: ProposedActionResponse


class WorkflowResponse(BaseModel):
    thread_id: UUID
    status: WorkflowStatus
    response: str = Field(min_length=1)
    human_approval: HumanApprovalResponse | None = None

    @model_validator(mode="after")
    def validate_human_approval(self) -> Self:
        approval_required = self.status == WorkflowStatus.APPROVAL_REQUIRED
        if approval_required != (self.human_approval is not None):
            raise ValueError(
                "human_approval must be present only when approval is required"
            )
        return self
