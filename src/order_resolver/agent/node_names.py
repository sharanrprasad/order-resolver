from enum import StrEnum, unique


@unique
class SupportNodeName(StrEnum):
    UNDERSTAND_REQUEST = "understand_request"
    INVESTIGATE = "investigate"
    READ_ONLY_TOOLS = "read_only_tools"
    VALIDATE_ACTION = "validate_action"
    HUMAN_APPROVAL = "human_approval"
    EXECUTE_ACTION = "execute_action"
    SUCCESS_RESPONSE = "success_response"
    FAILURE_RESPONSE = "failure_response"
