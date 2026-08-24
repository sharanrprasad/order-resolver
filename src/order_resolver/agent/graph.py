from collections.abc import Sequence
from typing import TypeAlias, cast

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from order_resolver.agent.node_names import SupportNodeName
from order_resolver.agent.nodes.edges import (
    route_after_approval,
    route_after_execution,
    route_after_investigation,
    route_after_validation,
)
from order_resolver.agent.nodes.execute_action import create_execute_action_node
from order_resolver.agent.nodes.failure_response import create_failed_node
from order_resolver.agent.nodes.human_approval import create_human_approval_node
from order_resolver.agent.nodes.investigator_agent import create_investigator_node
from order_resolver.agent.nodes.read_only_tools import create_read_only_tool_node
from order_resolver.agent.nodes.success_response import create_success_node
from order_resolver.agent.nodes.understand_request import (
    create_understand_request_node,
)
from order_resolver.agent.nodes.validate_action import create_validate_action_node
from order_resolver.agent.state import ParsedRequest, ProposedAction, SupportState
from order_resolver.agent.types import ActionModel, IntentModel
from order_resolver.services import Services

SupportGraph: TypeAlias = CompiledStateGraph[
    SupportState,
    None,
    SupportState,
    SupportState,
]
SupportGraphBuilder: TypeAlias = StateGraph[
    SupportState,
    None,
    SupportState,
    SupportState,
]


def build_support_graph(
    model: BaseChatModel,
    services: Services,
    read_tools: Sequence[BaseTool],
    *,
    checkpointer: BaseCheckpointSaver,
) -> SupportGraph:
    """Build the support workflow from injected models and application dependencies."""
    intent_model = cast(
        IntentModel,
        model.with_structured_output(ParsedRequest),
    )
    investigation_model = model.bind_tools(read_tools)
    action_model = cast(
        ActionModel,
        model.with_structured_output(ProposedAction),
    )

    graph = SupportGraphBuilder(SupportState)
    graph.add_node(
        SupportNodeName.UNDERSTAND_REQUEST,
        create_understand_request_node(intent_model),
    )
    graph.add_node(
        SupportNodeName.INVESTIGATE,
        create_investigator_node(investigation_model, action_model),
    )
    graph.add_node(
        SupportNodeName.READ_ONLY_TOOLS,
        create_read_only_tool_node(read_tools),
    )
    graph.add_node(
        SupportNodeName.VALIDATE_ACTION,
        create_validate_action_node(services),
    )
    graph.add_node(
        SupportNodeName.HUMAN_APPROVAL,
        create_human_approval_node(),
    )
    graph.add_node(
        SupportNodeName.EXECUTE_ACTION,
        create_execute_action_node(services),
    )
    graph.add_node(
        SupportNodeName.SUCCESS_RESPONSE,
        create_success_node(model),
    )
    graph.add_node(
        SupportNodeName.FAILURE_RESPONSE,
        create_failed_node(model),
    )

    # Edges
    graph.add_edge(START, SupportNodeName.UNDERSTAND_REQUEST)

    # Start
    graph.add_edge(
        SupportNodeName.UNDERSTAND_REQUEST,
        SupportNodeName.INVESTIGATE,
    )

    # Investigator <-> tools loop
    graph.add_conditional_edges(
        SupportNodeName.INVESTIGATE,
        route_after_investigation,
    )
    graph.add_edge(
        SupportNodeName.READ_ONLY_TOOLS,
        SupportNodeName.INVESTIGATE,
    )

    # Business validation
    graph.add_conditional_edges(
        SupportNodeName.VALIDATE_ACTION,
        route_after_validation,
    )
    graph.add_conditional_edges(
        SupportNodeName.HUMAN_APPROVAL,
        route_after_approval,
    )

    graph.add_conditional_edges(
        SupportNodeName.EXECUTE_ACTION,
        route_after_execution,
    )
    graph.add_edge(SupportNodeName.SUCCESS_RESPONSE, END)
    graph.add_edge(SupportNodeName.FAILURE_RESPONSE, END)

    return graph.compile(
        checkpointer=checkpointer,
        name="order_resolver_support",
    )
