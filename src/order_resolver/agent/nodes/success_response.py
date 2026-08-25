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

        if executed_action.action == "no_action":
            response = await response_model.ainvoke(
                [
                    {
                        "role": "system",
                        "content": (
                            "Write a concise, natural response directly to the "
                            "customer's request. No business action was needed or "
                            "performed. Do not claim that an action was completed, "
                            "and do not mention no_action, workflow state, internal "
                            "reasoning, investigation, or reference IDs. If the "
                            "customer sent a casual greeting, respond warmly and "
                            "invite them to ask for order support."
                        ),
                    },
                    *messages,
                ]
            )
        else:
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
