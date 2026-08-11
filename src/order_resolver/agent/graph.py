from itertools import pairwise

from langgraph.graph import END, START, StateGraph

from order_resolver.agent import nodes
from order_resolver.agent.state import SupportState


def build_support_graph():
    """Define topology only. Add a durable checkpointer when wiring persistence."""
    graph = StateGraph(SupportState)
    node_names = (
        "understand_request",
        "resolve_customer_and_order",
        "investigate",
        "retrieve_relevant_policy",
        "determine_action",
        "validate_action",
        "check_approval_requirement",
        "execute_action",
        "generate_response",
    )
    for name in node_names:
        graph.add_node(name, getattr(nodes, name))
    graph.add_edge(START, "understand_request")
    for source, target in pairwise(node_names):
        graph.add_edge(source, target)
    graph.add_edge("generate_response", END)
    return graph


support_graph = build_support_graph().compile()
