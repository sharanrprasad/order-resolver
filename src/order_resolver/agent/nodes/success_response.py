from typing import Any

from langchain_core.runnables import Runnable

from order_resolver.agent.state import SupportState
from order_resolver.agent.types import SupportModelNode


def create_success_node(
    response_model: Runnable,
) -> SupportModelNode:

    async def success(
        state: SupportState,
    ) -> dict[str, Any]:

        response = await response_model.ainvoke(
            [
                {
                    "role": "system",
                    "content": (
                        "Write a concise customer support response confirming "
                        "that the requested action was completed successfully. "
                        "Use only the information provided in the conversation "
                        "and workflow state. Do not invent any details."
                    ),
                },
                *state["messages"], # Unpack all the state messages here.
                {
                    "role": "system",
                    "content": (
                        f"Executed action: {state.get('executed_action')}"
                    ),
                },
            ]
        )

        return {
            "messages": [response],
            "final_response": response.content,
        }

    return success