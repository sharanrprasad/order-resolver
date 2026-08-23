from order_resolver.agent.state import ResolutionStatus, SupportState
from order_resolver.agent.types import (
    ResponseModel,
    SupportModelNode,
    SupportNodeReturnType,
)


def create_failed_node(
    response_model: ResponseModel,
) -> SupportModelNode:

    async def failed(
        state: SupportState,
    ) -> SupportNodeReturnType:
        messages = state.get("messages")
        if not messages:
            raise RuntimeError("messages are missing in failure_response node")

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
                *messages,
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
            "final_response": response.text,
            "resolution_status": ResolutionStatus.FAILED,
        }

    return failed
