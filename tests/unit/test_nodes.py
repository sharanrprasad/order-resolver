from decimal import Decimal
from typing import Literal, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableLambda

from order_resolver.agent.nodes.execute_action import create_execute_action_node
from order_resolver.agent.nodes.failure_response import create_failed_node
from order_resolver.agent.nodes.human_approval import create_human_approval_node
from order_resolver.agent.nodes.investigator_agent import create_investigator_node
from order_resolver.agent.nodes.success_response import create_success_node
from order_resolver.agent.nodes.understand_request import (
    create_understand_request_node,
)
from order_resolver.agent.nodes.validate_action import create_validate_action_node
from order_resolver.agent.state import (
    ExecutedAction,
    ParsedRequest,
    ProposedAction,
    ResolutionStatus,
    SupportIntent,
    SupportState,
)
from order_resolver.agent.types import SupportModelNode
from order_resolver.services import Services


def proposed_action(
    action: Literal["refund", "cancel", "no_action"] = "refund",
) -> ProposedAction:
    return ProposedAction(
        action=action,
        reason="Test action",
        amount=Decimal("10.00") if action == "refund" else None,
        confidence=1,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("node_name", "node"),
    [
        (
            "understand_request",
            create_understand_request_node(
                RunnableLambda(
                    lambda _: ParsedRequest(
                        intent=SupportIntent.OTHER,
                        explanation="Test intent",
                    )
                )
            ),
        ),
        (
            "investigate",
            create_investigator_node(
                RunnableLambda(lambda _: AIMessage(content="Done")),
                RunnableLambda(lambda _: proposed_action("no_action")),
            ),
        ),
        (
            "success_response",
            create_success_node(RunnableLambda(lambda _: AIMessage(content="Success"))),
        ),
        (
            "failure_response",
            create_failed_node(RunnableLambda(lambda _: AIMessage(content="Failure"))),
        ),
    ],
)
async def test_message_nodes_reject_missing_messages(
    node_name: str,
    node: SupportModelNode,
) -> None:
    with pytest.raises(
        RuntimeError,
        match=rf"messages are missing in {node_name} node",
    ):
        await node({})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "node",
    [
        create_validate_action_node(MagicMock(spec=Services)),
        create_execute_action_node(MagicMock(spec=Services)),
        create_human_approval_node(),
    ],
)
async def test_action_nodes_reject_missing_proposed_action(
    node: SupportModelNode,
) -> None:
    with pytest.raises(RuntimeError, match="proposed_action is missing"):
        await node({})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("state", "missing_field"),
    [
        (
            {"proposed_action": proposed_action("no_action")},
            "requires_approval",
        ),
        (
            {
                "proposed_action": proposed_action(),
                "requires_approval": False,
                "order_id": uuid4(),
            },
            "customer_id",
        ),
        (
            {
                "proposed_action": proposed_action(),
                "requires_approval": False,
                "customer_id": uuid4(),
                "order_id": uuid4(),
            },
            "intent",
        ),
        (
            {
                "proposed_action": proposed_action("cancel"),
                "requires_approval": False,
                "customer_id": uuid4(),
            },
            "order_id",
        ),
    ],
)
async def test_execute_action_rejects_missing_required_state(
    state: SupportState,
    missing_field: str,
) -> None:
    node = create_execute_action_node(MagicMock(spec=Services))

    with pytest.raises(
        RuntimeError,
        match=rf"{missing_field} is missing in execute_action node",
    ):
        await node(state)


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["refund", "cancel"])
async def test_validate_action_handles_missing_order_id(
    action: Literal["refund", "cancel"],
) -> None:
    node = create_validate_action_node(MagicMock(spec=Services))
    state: SupportState = {"proposed_action": proposed_action(action)}

    result = await node(state)

    assert result["validation_result"].valid is False
    assert result["requires_approval"] is False


@pytest.mark.asyncio
async def test_success_response_handles_no_action_conversationally() -> None:
    response_model = MagicMock()
    response_model.ainvoke = AsyncMock(
        return_value=AIMessage(content="Hey! How can I help with your order today?")
    )
    node = create_success_node(response_model)
    state = cast(
        SupportState,
        {
            "messages": [HumanMessage(content="What's up bro?")],
            "executed_action": ExecutedAction(
                action="no_action",
                success=True,
            ),
        },
    )

    result = await node(state)

    prompt = response_model.ainvoke.await_args.args[0]
    assert not any(
        isinstance(message, dict)
        and str(message.get("content", "")).startswith("Executed action:")
        for message in prompt
    )
    assert result.get("final_response") == "Hey! How can I help with your order today?"
    assert result.get("resolution_status") == ResolutionStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_success_response_includes_completed_action() -> None:
    response_model = MagicMock()
    response_model.ainvoke = AsyncMock(
        return_value=AIMessage(content="Your refund was completed successfully.")
    )
    node = create_success_node(response_model)
    state = cast(
        SupportState,
        {
            "messages": [HumanMessage(content="Please refund my order")],
            "executed_action": ExecutedAction(
                action="refund",
                success=True,
                reference_id=uuid4(),
            ),
        },
    )

    await node(state)

    prompt = response_model.ainvoke.await_args.args[0]
    assert any(
        isinstance(message, dict)
        and str(message.get("content", "")).startswith("Executed action:")
        for message in prompt
    )
