from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable

from order_resolver.agent.state import SupportState, ProposedAction
from order_resolver.agent.types import SupportModelNode


def create_investigator_node(
    investigation_model: Runnable, # Bound with tools here
    action_model: Runnable, # Structured Proposed Action bound model.
) -> SupportModelNode:

    async def investigate(
        state: SupportState,
    ) -> dict[str, Any]:

        response: AIMessage = await investigation_model.ainvoke(
            [
                {
                    "role": "system",
                    "content": (
                        "You are an e-commerce customer support investigator. "
                        "Investigate the customer's request and determine the "
                        "appropriate action. "
                        "Use the available read-only tools whenever you need "
                        "customer, order, shipment, refund, or company policy information. "
                        "Do not invent facts. "
                        "Do not perform any write operations. "
                        "If you need more information, call the appropriate tool. "
                        "If you have enough information to determine the appropriate "
                        "action, stop calling tools and summarize your conclusion."
                    ),
                },
                *state["messages"],
            ]
        )

        # The model needs more information.
        # The graph will route this AIMessage to ReadOnlyToolNode.
        if response.tool_calls:
            return {
                "messages": [response],
            }

        # No tool call means the investigation is complete.
        proposed_action: ProposedAction = await action_model.ainvoke(
            [
                {
                    "role": "system",
                    "content": (
                        "Based only on the customer request and the investigation "
                        "results below, determine the proposed support action. "
                        "Do not invent facts."
                    ),
                },
                *state["messages"],
                response,
            ]
        )

        return {
            "messages": [response],
            "proposed_action": proposed_action,
        }

    return investigate