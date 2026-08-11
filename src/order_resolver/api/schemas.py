from uuid import UUID

from pydantic import BaseModel, Field


class SupportRequest(BaseModel):
    customer_id: UUID
    message: str = Field(min_length=1)


class WorkflowResponse(BaseModel):
    thread_id: str
    status: str
    response: str | None = None
