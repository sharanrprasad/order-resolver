from collections.abc import Sequence
from langchain_core.tools import BaseTool
from langgraph.prebuilt import ToolNode

# Tools Node that is going to be called from the understand_request agent.
def create_read_only_tool_node(
    tools: Sequence[BaseTool],
) -> ToolNode:
    """Create the investigator's tool node from explicitly injected tools."""
    return ToolNode(tools, name="read_only_tools")
