"""End-to-end tests for ``POST /support/requests``.

The LLM is scripted (``LLMScript``); everything else - the LangGraph workflow,
deterministic validation, and the refund / cancellation writes - runs for real
against Postgres. Each test asserts on both the HTTP response and the resulting
database rows.
"""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from order_resolver.agent.state import SupportIntent
from order_resolver.db.models import Order, OrderStatus, Refund, RefundStatus
from tests.integration.fake_llm import LLMScript, scripted_action
from tests.integration.seed import (
    CUSTOMER_ID,
    ORDER_HIGH_VALUE,
    ORDER_IN_TRANSIT,
    ORDER_LOST,
    ORDER_PROCESSING,
    ORDER_REFUNDED,
)

ClientFactory = Callable[[LLMScript], AsyncClient]


def _payload(message: str, customer_id: str | None = None) -> dict[str, str]:
    return {"customer_id": customer_id or str(CUSTOMER_ID), "message": message}


async def _refund_count(session: AsyncSession, order_id: object) -> int:
    result = await session.scalar(
        select(func.count()).select_from(Refund).where(Refund.order_id == order_id)
    )
    return result or 0


async def test_track_order_returns_a_reply_and_writes_nothing(
    support_client: ClientFactory,
    db_session: AsyncSession,
) -> None:
    script = LLMScript(
        intent=SupportIntent.TRACK_ORDER,
        proposed_action=scripted_action("no_action"),
        customer_reply="Your order 101 was delivered five days ago.",
    )
    client = support_client(script)

    response = await client.post("/support/requests", json=_payload("Where is order 101?"))

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "succeeded"
    assert body["response"]
    assert body["human_approval"] is None
    total_refunds = await db_session.scalar(select(func.count()).select_from(Refund))
    assert total_refunds == 1  # only the pre-seeded refund on order 105


async def test_lost_shipment_refund_is_persisted(
    support_client: ClientFactory,
    db_session: AsyncSession,
) -> None:
    script = LLMScript(
        intent=SupportIntent.REFUND,
        order_id=ORDER_LOST,
        proposed_action=scripted_action("refund", amount=Decimal("65.00")),
        customer_reply="We've refunded $65.00 for your lost shipment.",
    )
    client = support_client(script)

    response = await client.post(
        "/support/requests", json=_payload("Order 103 is lost, please refund")
    )

    assert response.status_code == 201
    assert response.json()["status"] == "succeeded"

    refunds = (
        await db_session.scalars(
            select(Refund).where(Refund.order_id == ORDER_LOST)
        )
    ).all()
    assert len(refunds) == 1
    assert refunds[0].amount == Decimal("65.00")
    assert refunds[0].status == RefundStatus.completed


async def test_processing_order_is_cancelled(
    support_client: ClientFactory,
    db_session: AsyncSession,
) -> None:
    script = LLMScript(
        intent=SupportIntent.CANCEL_ORDER,
        order_id=ORDER_PROCESSING,
        proposed_action=scripted_action("cancel"),
        customer_reply="Order 104 has been cancelled.",
    )
    client = support_client(script)

    response = await client.post(
        "/support/requests", json=_payload("Cancel order 104 please")
    )

    assert response.status_code == 201
    assert response.json()["status"] == "succeeded"

    order = await db_session.get(Order, ORDER_PROCESSING)
    assert order is not None
    assert order.status == OrderStatus.cancelled
    assert await _refund_count(db_session, ORDER_PROCESSING) == 0


async def test_high_value_refund_requires_human_approval(
    support_client: ClientFactory,
    db_session: AsyncSession,
) -> None:
    script = LLMScript(
        intent=SupportIntent.DAMAGED_ITEM,
        order_id=ORDER_HIGH_VALUE,
        proposed_action=scripted_action(
            "refund", amount=Decimal("250.00"), reason="Item arrived cracked"
        ),
    )
    client = support_client(script)

    response = await client.post(
        "/support/requests", json=_payload("Order 106 arrived damaged")
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "approval_required"
    assert body["human_approval"]["proposed_action"]["action"] == "refund"
    assert body["human_approval"]["proposed_action"]["amount"] == "250.00"
    # The write must not happen before a human approves.
    assert await _refund_count(db_session, ORDER_HIGH_VALUE) == 0


async def test_cancel_after_shipment_fails_without_writes(
    support_client: ClientFactory,
    db_session: AsyncSession,
) -> None:
    script = LLMScript(
        intent=SupportIntent.CANCEL_ORDER,
        order_id=ORDER_IN_TRANSIT,
        proposed_action=scripted_action("cancel"),
    )
    client = support_client(script)

    response = await client.post(
        "/support/requests", json=_payload("Cancel order 102")
    )

    assert response.status_code == 201
    assert response.json()["status"] == "failed"

    order = await db_session.get(Order, ORDER_IN_TRANSIT)
    assert order is not None
    assert order.status == OrderStatus.shipped


async def test_duplicate_refund_is_rejected(
    support_client: ClientFactory,
    db_session: AsyncSession,
) -> None:
    script = LLMScript(
        intent=SupportIntent.DAMAGED_ITEM,
        order_id=ORDER_REFUNDED,
        proposed_action=scripted_action("refund", amount=Decimal("89.00")),
    )
    client = support_client(script)

    response = await client.post(
        "/support/requests", json=_payload("Refund order 105 again")
    )

    assert response.status_code == 201
    assert response.json()["status"] == "failed"
    # Still just the single pre-seeded refund - no duplicate.
    assert await _refund_count(db_session, ORDER_REFUNDED) == 1


async def test_unknown_customer_is_rejected(support_client: ClientFactory) -> None:
    script = LLMScript(
        intent=SupportIntent.OTHER,
        proposed_action=scripted_action("no_action"),
    )
    client = support_client(script)

    response = await client.post(
        "/support/requests", json=_payload("Hello", customer_id=str(uuid4()))
    )

    assert response.status_code == 404
