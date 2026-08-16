from typing import Any

from langchain_core.runnables import Runnable

from order_resolver.agent.state import SupportState
from order_resolver.agent.types import SupportModelNode


def create_failed_node(
    response_model: Runnable,
) -> SupportModelNode:

    async def failed(
        state: SupportState,
    ) -> dict[str, Any]:

        validation_result = state.get("validation_result")
        approval_status = state.get("approval_status")
        executed_action = state.get("executed_action")

        response = await response_model.ainvoke(
            [
                {
                    "role": "system",
                    "content": (
                        "Write a concise customer support response explaining "
                        "that the requested action could not be completed. "
                        "Explain the reason politely using only the supplied "
                        "workflow information. Do not invent details or promise "
                        "an action that was not completed."
                    ),
                },
                *state["messages"], # Unpack all the state messages here.
                # Add the below as this is only stored in the state.
                {
                    "role": "system",
                    "content": (
                        f"Validation result: {validation_result}. "
                        f"Approval status: {approval_status}. "
                        f"Execution result: {executed_action}."
                    ),
                },
            ]
        )

        return {
            "messages": [response],
            "final_response": response.content,
        }

    return failed