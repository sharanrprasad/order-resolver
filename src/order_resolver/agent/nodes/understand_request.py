from typing import Any, Awaitable, Callable
from langchain_core.runnables import Runnable
from order_resolver.agent.state import SupportState, ParsedRequest
from order_resolver.agent.types import SupportModelNode


# Using factory function method to help with testing.
def create_understand_request_node(
        intent_model: Runnable,
) -> SupportModelNode:

    async def understand_request(
        state: SupportState,
    ) -> dict[str, Any]:
        user_message = state["messages"][-1]

        result: ParsedRequest = await intent_model.ainvoke([
            {
                "role": "system",
                "content": (
                    "Classify the customer's support request. "
                    "Extract an order ID if one is explicitly provided. "
                    "Do not invent an order ID."
                ),
            },
            user_message,
        ])

        updates: dict[str, Any] = {
            "intent": result.intent,
        }

        # TODO - Figure out the logic when order id is not present in the request.
        if result.order_id is not None:
            updates["order_id"] = result.order_id

        return updates

    return understand_request
