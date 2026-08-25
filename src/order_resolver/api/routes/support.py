from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Response, status
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import GraphOutput
from pydantic import ValidationError

from order_resolver.agent.state import ResolutionStatus, SupportState
from order_resolver.api.dependencies import ApplicationDependenciesDep
from order_resolver.api.schemas import (
    HumanApprovalResponse,
    SupportRequest,
    WorkflowResponse,
    WorkflowStatus,
)
from order_resolver.services import ResourceNotFoundError

router = APIRouter(prefix="/support/requests", tags=["support"])


def not_implemented() -> None:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Workflow logic is ready to be implemented",
    )


def _build_workflow_response(
    thread_id: UUID,
    result: GraphOutput[SupportState],
) -> WorkflowResponse:
    if result.interrupts:
        if len(result.interrupts) != 1:
            raise RuntimeError("Expected exactly one workflow interrupt")

        interrupt_value = result.interrupts[0].value
        if (
            not isinstance(interrupt_value, dict)
            or interrupt_value.get("type") != "approval_required"
        ):
            raise RuntimeError("Received an unexpected workflow interrupt")

        try:
            human_approval = HumanApprovalResponse.model_validate(interrupt_value)
        except ValidationError as exc:
            raise RuntimeError("Received an invalid approval interrupt") from exc

        return WorkflowResponse(
            thread_id=thread_id,
            status=WorkflowStatus.APPROVAL_REQUIRED,
            response=human_approval.message,
            human_approval=human_approval,
        )

    final_response = result.value.get("final_response")
    if not isinstance(final_response, str) or not final_response.strip():
        raise RuntimeError("final_response is missing from the completed workflow")

    resolution_status = result.value.get("resolution_status")
    if resolution_status == ResolutionStatus.SUCCEEDED:
        workflow_status = WorkflowStatus.SUCCEEDED
    elif resolution_status == ResolutionStatus.FAILED:
        workflow_status = WorkflowStatus.FAILED
    else:
        raise RuntimeError("resolution_status is missing from the completed workflow")

    return WorkflowResponse(
        thread_id=thread_id,
        status=workflow_status,
        response=final_response,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_support_request(
    request: SupportRequest,
    dependencies: ApplicationDependenciesDep,
    response: Response,
) -> WorkflowResponse:
    try:
        await dependencies.services.customers.get(request.customer_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        ) from exc

    thread_id = uuid4()
    config: RunnableConfig = {
        "configurable": {
            "thread_id": str(thread_id),
        }
    }
    initial_state: SupportState = {
        "customer_id": request.customer_id,
        "messages": [HumanMessage(content=request.message)],
    }

    result = await dependencies.support_graph.ainvoke(
        initial_state,
        config,
        version="v2",
    )

    response.headers["Location"] = f"/support/requests/{thread_id}"
    return _build_workflow_response(thread_id, result)


@router.get("/{thread_id}")
def get_support_request(thread_id: str) -> None:
    not_implemented()


@router.post("/{thread_id}/approve")
def approve_support_request(thread_id: str) -> None:
    not_implemented()


@router.post("/{thread_id}/reject")
def reject_support_request(thread_id: str) -> None:
    not_implemented()
