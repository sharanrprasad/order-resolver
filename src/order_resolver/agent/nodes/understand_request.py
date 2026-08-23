from order_resolver.agent.state import SupportState
from order_resolver.agent.types import (
    IntentModel,
    SupportModelNode,
    SupportNodeReturnType,
)


# Using factory function method to help with testing.
def create_understand_request_node(
    intent_model: IntentModel,
) -> SupportModelNode:

    async def understand_request(
        state: SupportState,
    ) -> SupportNodeReturnType:
        messages = state.get("messages")
        if not messages:
            raise RuntimeError("messages are missing in understand_request node")

        user_message = messages[-1]

        result = await intent_model.ainvoke(
            [
                {
                    "role": "system",
                    "content": (
                        "Classify the customer's support request. "
                        "Extract an order ID if one is explicitly provided. "
                        "Do not invent an order ID."
                    ),
                },
                user_message,
            ]
        )

        updates: SupportNodeReturnType = {
            "intent": result.intent,
        }

        # TODO - Figure out the logic when order id is not present in the request.
        if result.order_id is not None:
            updates["order_id"] = result.order_id

        return updates

    return understand_request
