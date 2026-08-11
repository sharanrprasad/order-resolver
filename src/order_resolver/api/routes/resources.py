from uuid import UUID

from fastapi import APIRouter, HTTPException, status

router = APIRouter(tags=["resources"])


@router.get("/orders/{order_id}")
def get_order(order_id: UUID) -> None:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Order lookup is ready to be implemented",
    )


@router.get("/customers/{customer_id}")
def get_customer(customer_id: UUID) -> None:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Customer lookup is ready to be implemented",
    )
