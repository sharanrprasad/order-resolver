from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest
from sqlalchemy.sql import Select

from order_resolver.repositories import (
    LocalPolicyRepository,
    OrderRepository,
    RefundRepository,
)

CUSTOMER_ID = UUID("00000000-0000-0000-0000-000000000001")
ORDER_ID = UUID("00000000-0000-0000-0000-000000000101")


class CapturingSession:
    def __init__(self, scalar_results: list[object]) -> None:
        self.scalar_results = scalar_results
        self.statements: list[Select] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None

    async def scalar(self, statement: Select):
        self.statements.append(statement)
        return self.scalar_results.pop(0)

    async def scalars(self, statement: Select):
        self.statements.append(statement)
        return []


def assert_customer_and_order_are_bound(statement: Select) -> None:
    compiled = statement.compile()
    assert CUSTOMER_ID in compiled.params.values()
    assert ORDER_ID in compiled.params.values()
    assert "orders.customer_id" in str(compiled)


@pytest.mark.asyncio
async def test_all_order_repository_queries_enforce_customer_scope() -> None:
    session = CapturingSession([None, ORDER_ID, None])
    repository = OrderRepository(lambda: session)  # type: ignore[arg-type]

    await repository.get(CUSTOMER_ID, ORDER_ID)
    await repository.get_items(CUSTOMER_ID, ORDER_ID)
    await repository.get_shipment(CUSTOMER_ID, ORDER_ID)

    assert_customer_and_order_are_bound(session.statements[0])
    assert_customer_and_order_are_bound(session.statements[1])
    assert_customer_and_order_are_bound(session.statements[3])


@pytest.mark.asyncio
async def test_refund_total_query_enforces_customer_scope() -> None:
    session = CapturingSession([Decimal("10.00")])
    repository = RefundRepository(lambda: session)  # type: ignore[arg-type]

    amount = await repository.total_reserved(CUSTOMER_ID, ORDER_ID)

    assert amount == Decimal("10.00")
    assert_customer_and_order_are_bound(session.statements[0])


@pytest.mark.asyncio
async def test_policy_search_prioritizes_the_matching_policy() -> None:
    docs_path = Path(__file__).resolve().parents[1] / "docs"
    repository = LocalPolicyRepository(docs_path)

    matches = await repository.search("refund for a delivered order", limit=3)

    assert matches[0].source == "refund-policy.md"
