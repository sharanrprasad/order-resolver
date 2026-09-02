from datetime import UTC, datetime
from uuid import UUID

import pytest

from order_resolver.agent.tools.support import call_service
from order_resolver.services import ResourceNotFoundError
from order_resolver.services.models import CustomerDetails

CUSTOMER_ID = UUID("00000000-0000-0000-0000-000000000001")


def customer_details() -> CustomerDetails:
    return CustomerDetails(
        id=CUSTOMER_ID,
        name="Current Customer",
        email="current@example.com",
        membership_tier="gold",
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_call_service_serializes_models_and_model_lists() -> None:
    customer = customer_details()

    async def get_customer() -> CustomerDetails:
        return customer

    async def list_customers() -> list[CustomerDetails]:
        return [customer]

    single_result = await call_service(get_customer)
    list_result = await call_service(list_customers)

    assert single_result["data"]["id"] == str(CUSTOMER_ID)
    assert list_result["data"][0]["id"] == str(CUSTOMER_ID)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("exception", "expected_code"),
    [
        (ResourceNotFoundError("Missing"), "not_found"),
        (ValueError("Invalid"), "invalid_request"),
        (RuntimeError("Unavailable"), "service_unavailable"),
    ],
)
async def test_call_service_maps_errors(
    exception: Exception,
    expected_code: str,
) -> None:
    async def failing_operation() -> None:
        raise exception

    result = await call_service(failing_operation)

    assert result["ok"] is False
    assert result["error"]["code"] == expected_code
