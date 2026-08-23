from typing import Literal

from order_resolver.agent.node_names import SupportNodeName
from order_resolver.agent.state import ApprovalStatus, SupportState


def route_after_investigation(
    state: SupportState,
) -> Literal[
    SupportNodeName.READ_ONLY_TOOLS,
    SupportNodeName.VALIDATE_ACTION,
]:
    """Route tool calls to the read-only ToolNode."""
    messages = state.get("messages")
    if not messages:
        raise RuntimeError("messages are missing after investigate node")

    last_message = messages[-1]

    if getattr(last_message, "tool_calls", None):
        return SupportNodeName.READ_ONLY_TOOLS

    return SupportNodeName.VALIDATE_ACTION


def route_after_approval(
    state: SupportState,
) -> Literal[
    SupportNodeName.EXECUTE_ACTION,
    SupportNodeName.FAILURE_RESPONSE,
]:
    approval_status = state.get("approval_status")
    if approval_status is None:
        raise RuntimeError("approval_status is missing after human_approval node")

    if approval_status == ApprovalStatus.APPROVED:
        return SupportNodeName.EXECUTE_ACTION

    return SupportNodeName.FAILURE_RESPONSE


def route_after_execution(
    state: SupportState,
) -> Literal[
    SupportNodeName.SUCCESS_RESPONSE,
    SupportNodeName.FAILURE_RESPONSE,
]:
    executed_action = state.get("executed_action")

    if executed_action is None:
        raise RuntimeError("executed_action is missing after execute_action node")

    return (
        SupportNodeName.SUCCESS_RESPONSE
        if executed_action.success
        else SupportNodeName.FAILURE_RESPONSE
    )


def route_after_validation(
    state: SupportState,
) -> Literal[
    SupportNodeName.HUMAN_APPROVAL,
    SupportNodeName.EXECUTE_ACTION,
    SupportNodeName.FAILURE_RESPONSE,
]:
    result = state.get("validation_result")

    if result is None:
        raise RuntimeError("validation_result is missing after validate_action node")

    if not result.valid:
        return SupportNodeName.FAILURE_RESPONSE

    requires_approval = state.get("requires_approval")

    if requires_approval is None:
        raise RuntimeError("requires_approval is missing after validate_action node")

    if requires_approval:
        return SupportNodeName.HUMAN_APPROVAL

    return SupportNodeName.EXECUTE_ACTION
