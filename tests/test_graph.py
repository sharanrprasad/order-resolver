from collections.abc import Callable
from typing import cast
from unittest.mock import MagicMock

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, START

from order_resolver.agent.graph import build_support_graph
from order_resolver.agent.node_names import SupportNodeName
from order_resolver.agent.nodes.edges import (
    route_after_approval,
    route_after_execution,
    route_after_investigation,
    route_after_validation,
)
from order_resolver.agent.state import (
    ApprovalStatus,
    ExecutedAction,
    ParsedRequest,
    ProposedAction,
    SupportIntent,
    SupportState,
    ValidationResult,
)
from order_resolver.services import Services


def test_support_graph_registers_expected_nodes_and_edges() -> None:
    model = MagicMock(spec=BaseChatModel)
    intent_model = RunnableLambda(
        lambda _: ParsedRequest(
            intent=SupportIntent.OTHER,
            explanation="Test intent",
        )
    )
    action_model = RunnableLambda(
        lambda _: ProposedAction(
            action="no_action",
            reason="Test action",
            confidence=1,
        )
    )
    model.with_structured_output.side_effect = [intent_model, action_model]
    model.bind_tools.return_value = RunnableLambda(
        lambda _: AIMessage(content="Investigation complete")
    )

    graph = build_support_graph(
        cast(BaseChatModel, model),
        cast(Services, object()),
        [],
    )

    assert set(graph.nodes) == {START, *SupportNodeName}
    assert {(edge.source, edge.target) for edge in graph.get_graph().edges} == {
        (START, SupportNodeName.UNDERSTAND_REQUEST),
        (
            SupportNodeName.UNDERSTAND_REQUEST,
            SupportNodeName.INVESTIGATE,
        ),
        (SupportNodeName.INVESTIGATE, SupportNodeName.READ_ONLY_TOOLS),
        (SupportNodeName.INVESTIGATE, SupportNodeName.VALIDATE_ACTION),
        (SupportNodeName.READ_ONLY_TOOLS, SupportNodeName.INVESTIGATE),
        (SupportNodeName.VALIDATE_ACTION, SupportNodeName.HUMAN_APPROVAL),
        (SupportNodeName.VALIDATE_ACTION, SupportNodeName.EXECUTE_ACTION),
        (SupportNodeName.VALIDATE_ACTION, SupportNodeName.FAILURE_RESPONSE),
        (SupportNodeName.HUMAN_APPROVAL, SupportNodeName.EXECUTE_ACTION),
        (SupportNodeName.HUMAN_APPROVAL, SupportNodeName.FAILURE_RESPONSE),
        (SupportNodeName.EXECUTE_ACTION, SupportNodeName.SUCCESS_RESPONSE),
        (SupportNodeName.EXECUTE_ACTION, SupportNodeName.FAILURE_RESPONSE),
        (SupportNodeName.SUCCESS_RESPONSE, END),
        (SupportNodeName.FAILURE_RESPONSE, END),
    }


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        (
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_order",
                        "args": {},
                        "id": "tool-call-id",
                        "type": "tool_call",
                    }
                ],
            ),
            SupportNodeName.READ_ONLY_TOOLS,
        ),
        (
            AIMessage(content="Investigation complete"),
            SupportNodeName.VALIDATE_ACTION,
        ),
    ],
)
def test_route_after_investigation(
    message: AIMessage,
    expected: SupportNodeName,
) -> None:
    state: SupportState = {"messages": [message]}

    assert route_after_investigation(state) is expected


@pytest.mark.parametrize(
    ("valid", "requires_approval", "expected"),
    [
        (False, False, SupportNodeName.FAILURE_RESPONSE),
        (True, True, SupportNodeName.HUMAN_APPROVAL),
        (True, False, SupportNodeName.EXECUTE_ACTION),
    ],
)
def test_route_after_validation(
    valid: bool,
    requires_approval: bool,
    expected: SupportNodeName,
) -> None:
    state: SupportState = {
        "validation_result": ValidationResult(valid=valid),
        "requires_approval": requires_approval,
    }

    assert route_after_validation(state) is expected


@pytest.mark.parametrize(
    ("approval_status", "expected"),
    [
        (ApprovalStatus.APPROVED, SupportNodeName.EXECUTE_ACTION),
        (ApprovalStatus.REJECTED, SupportNodeName.FAILURE_RESPONSE),
    ],
)
def test_route_after_approval(
    approval_status: ApprovalStatus,
    expected: SupportNodeName,
) -> None:
    state: SupportState = {"approval_status": approval_status}

    assert route_after_approval(state) is expected


@pytest.mark.parametrize(
    ("success", "expected"),
    [
        (True, SupportNodeName.SUCCESS_RESPONSE),
        (False, SupportNodeName.FAILURE_RESPONSE),
    ],
)
def test_route_after_execution(
    success: bool,
    expected: SupportNodeName,
) -> None:
    state: SupportState = {
        "executed_action": ExecutedAction(
            action="refund",
            success=success,
        )
    }

    assert route_after_execution(state) is expected


@pytest.mark.parametrize(
    ("route", "state", "missing_field"),
    [
        (route_after_investigation, {}, "messages"),
        (route_after_approval, {}, "approval_status"),
        (route_after_execution, {}, "executed_action"),
        (route_after_validation, {}, "validation_result"),
        (
            route_after_validation,
            {"validation_result": ValidationResult(valid=True)},
            "requires_approval",
        ),
    ],
)
def test_routes_reject_missing_required_state(
    route: Callable[[SupportState], SupportNodeName],
    state: SupportState,
    missing_field: str,
) -> None:
    with pytest.raises(
        RuntimeError,
        match=rf"{missing_field} (?:is|are) missing",
    ):
        route(state)
