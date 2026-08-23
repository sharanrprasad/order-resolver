from order_resolver.agent.state import ResolutionStatus, SupportState
from order_resolver.agent.types import (
    ResponseModel,
    SupportModelNode,
    SupportNodeReturnType,
)


def create_success_node(
    response_model: ResponseModel,
) -> SupportModelNode:

    async def success(
        state: SupportState,
    ) -> SupportNodeReturnType:
        messages = state.get("messages")
        if not messages:
            raise RuntimeError("messages are missing in success_response node")

        executed_action = state.get("executed_action")
        if executed_action is None:
            raise RuntimeError("executed_action is missing in success_response node")

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
                *messages,
                {
                    "role": "system",
                    "content": f"Executed action: {executed_action}",
                },
            ]
        )

        return {
            "messages": [response],
            "final_response": response.text,
            "resolution_status": ResolutionStatus.SUCCEEDED,
        }

    return success
