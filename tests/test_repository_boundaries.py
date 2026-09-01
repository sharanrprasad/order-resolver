from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy.sql import Select

from order_resolver.repositories import (
    OrderRepository,
    PolicyRepository,
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


class PolicyRows:
    def all(self) -> list[tuple[str, str, float]]:
        return [("refund-policy.md", "Refund policy", 0.91)]


class PolicySession:
    def __init__(self) -> None:
        self.statement: Select | None = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None

    async def execute(self, statement: Select) -> PolicyRows:
        self.statement = statement
        return PolicyRows()


@pytest.mark.asyncio
async def test_policy_search_uses_pgvector_and_embedding_model_scope() -> None:
    session = PolicySession()
    repository = PolicyRepository(lambda: session)  # type: ignore[arg-type]
    query_embedding = [0.1, 0.2, 0.3]

    matches = await repository.search(
        query_embedding,
        embedding_model_name="test-embedding-model",
        limit=3,
    )

    assert matches[0].source == "refund-policy.md"
    assert matches[0].score == pytest.approx(0.91)
    assert session.statement is not None
    compiled = session.statement.compile()
    assert "<=>" in str(compiled)
    assert "company_policies.embedding_model" in str(compiled)
    assert "test-embedding-model" in compiled.params.values()
    assert query_embedding in compiled.params.values()
    assert 3 in compiled.params.values()
    # No similarity threshold is applied by default.
    assert ">=" not in str(compiled)


@pytest.mark.asyncio
async def test_policy_search_filters_by_min_score_in_sql() -> None:
    session = PolicySession()
    repository = PolicyRepository(lambda: session)  # type: ignore[arg-type]

    await repository.search(
        [0.1, 0.2, 0.3],
        embedding_model_name="test-embedding-model",
        limit=3,
        min_score=0.4,
    )

    assert session.statement is not None
    compiled = session.statement.compile()
    # The similarity floor (1 - cosine_distance >= :min_score) is enforced in the
    # query, not just by ordering.
    assert ">=" in str(compiled)
    assert 0.4 in compiled.params.values()
