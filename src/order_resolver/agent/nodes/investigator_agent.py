from typing import Any
from langchain_core.messages import SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel

from order_resolver.agent.state import SupportState


def create_investigator_node(
    model: BaseChatModel,
    read_tools: list,
):
    """Create the investigator agent. This can call the ReadTools repeatedly to get the correct information."""
    investigator_model = model.bind_tools(read_tools)

    async def investigate(
        state: SupportState,
    ) -> dict[str, Any]:

        intent = state["intent"]
        order_id = state.get("order_id", "")

        system_message = SystemMessage(
            content=(
                "You are a customer support investigator. "
                "Investigate the customer's request using the available "
                "read-only tools. "
                "Do not invent customer, order, shipment, refund, or policy data. "
                "Use tools whenever factual business data is required. "
                "Do not attempt to perform any write actions. "
                f"The parsed support intent is: {intent}. "
                f"The parsed order ID is: {order_id}. "
                "Once you have enough information to understand the request, "
                "stop calling tools and summarize your findings."
            )
        )

        response = await investigator_model.ainvoke(
            [
                system_message,
                *state["messages"],
            ]
        )

        return {
            "messages": [response],
        }

    return investigate







