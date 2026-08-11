from order_resolver.agent.state import SupportState


def placeholder_node(state: SupportState) -> dict:
    """Graph seam for a future implementation; intentionally does no work."""
    return {}


understand_request = placeholder_node
resolve_customer_and_order = placeholder_node
investigate = placeholder_node
retrieve_relevant_policy = placeholder_node
determine_action = placeholder_node
validate_action = placeholder_node
check_approval_requirement = placeholder_node
execute_action = placeholder_node
generate_response = placeholder_node
