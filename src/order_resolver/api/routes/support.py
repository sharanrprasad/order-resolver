from fastapi import APIRouter, HTTPException, status

from order_resolver.api.schemas import SupportRequest

router = APIRouter(prefix="/support/requests", tags=["support"])


def not_implemented() -> None:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Workflow logic is ready to be implemented",
    )


@router.post("")
def create_support_request(request: SupportRequest) -> None:
    not_implemented()


@router.get("/{thread_id}")
def get_support_request(thread_id: str) -> None:
    not_implemented()


@router.post("/{thread_id}/approve")
def approve_support_request(thread_id: str) -> None:
    not_implemented()


@router.post("/{thread_id}/reject")
def reject_support_request(thread_id: str) -> None:
    not_implemented()
