from order_resolver.agent.state import SupportState
from order_resolver.agent.types import (
    ActionModel,
    InvestigationModel,
    SupportModelNode,
    SupportNodeReturnType,
)


def create_investigator_node(
    investigation_model: InvestigationModel,
    action_model: ActionModel,
) -> SupportModelNode:

    async def investigate(
        state: SupportState,
    ) -> SupportNodeReturnType:
        messages = state.get("messages")
        if not messages:
            raise RuntimeError("messages are missing in investigate node")

        response = await investigation_model.ainvoke(
            [
                {
                    "role": "system",
                    "content": (
                        "You are an e-commerce customer support investigator. "
                        "Investigate the customer's request and determine the "
                        "appropriate action. "
                        "Use the available read-only tools whenever you need "
                        "customer, order, shipment, refund, or company policy information. "
                        "Use search_company_policy to retrieve the applicable policy "
                        "before reaching a conclusion about refunds, cancellations, "
                        "damaged items, or other policy-governed requests. Pass it a "
                        "concise natural-language description of the rule you need. "
                        "If policy search returns no result or is unavailable, do not "
                        "invent a policy or repeatedly retry the same search. "
                        "Do not invent facts. "
                        "Do not perform any write operations. "
                        "If you need more information, call the appropriate tool. "
                        "If you have enough information to determine the appropriate "
                        "action, stop calling tools and summarize your conclusion."
                    ),
                },
                *messages,
            ]
        )

        # The model needs more information.
        # The graph will route this AIMessage to ReadOnlyToolNode.
        if response.tool_calls:
            return {
                "messages": [response],
            }

        # No tool call means the investigation is complete.
        proposed_action = await action_model.ainvoke(
            [
                {
                    "role": "system",
                    "content": (
                        "Based only on the customer request and the investigation "
                        "results below, determine the proposed support action. "
                        "Do not invent facts."
                    ),
                },
                *messages,
                response,
            ]
        )

        return {
            "messages": [response],
            "proposed_action": proposed_action,
        }

    return investigate
