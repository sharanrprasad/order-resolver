from typing import Literal

from order_resolver.agent.state import SupportState


# Have decided to have a dedicated Tools node. This Edge routes the investigator node to that tool node.

def route_after_investigation(
    state: SupportState,
) -> Literal["read_tools", "investigation_complete"]:

    """ Routing the investigation to read tools """
    last_message = state["messages"][-1]

    if getattr(last_message, "tool_calls", None):
        return "read_tools"

    return "investigation_complete"



# Edge to decide the final action. 
def route_after_validation(
    state: SupportState,
) -> Literal["approval","execute_action","final_response"]:

    result = state["validation_result"]

    if not result.valid:
        return "final_response"

    if state["requires_approval"]:
        return "approval"

    return "execute_action"