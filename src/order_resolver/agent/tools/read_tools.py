from typing import cast
from uuid import UUID

from langchain_core.tools import BaseTool, tool
from langgraph.prebuilt import ToolRuntime

from order_resolver.agent.state import SupportState
from order_resolver.agent.tools.support import ToolResult, call_service
from order_resolver.services import ReadServices


def create_read_tools(services: ReadServices) -> list[BaseTool]:
    """Create the six read-only tools from an injected service collection."""

    @tool()
    async def get_customer(runtime: ToolRuntime[None, SupportState]) -> ToolResult:
        """Get the current customer's details."""
        customer_id = runtime.state["customer_id"]
        return await call_service(lambda: services.customers.get(customer_id))

    @tool()
    async def get_order(
        order_id: UUID,
        runtime: ToolRuntime[None, SupportState],
    ) -> ToolResult:
        """Get an order belonging to the current customer."""
        customer_id = runtime.state["customer_id"]
        return await call_service(
            lambda: services.orders.get(customer_id, order_id)
        )

    @tool()
    async def get_order_items(
        order_id: UUID,
        runtime: ToolRuntime[None, SupportState],
    ) -> ToolResult:
        """Get line items for an order belonging to the current customer."""
        customer_id = runtime.state["customer_id"]
        return await call_service(
            lambda: services.orders.get_items(customer_id, order_id)
        )

    @tool()
    async def get_shipment(
        order_id: UUID,
        runtime: ToolRuntime[None, SupportState],
    ) -> ToolResult:
        """Get shipment details for an order belonging to the current customer."""
        customer_id = runtime.state["customer_id"]
        return await call_service(
            lambda: services.orders.get_shipment(customer_id, order_id)
        )

    @tool()
    async def search_company_policy(
        query: str,
        runtime: ToolRuntime[None, SupportState],
    ) -> ToolResult:
        """Search read-only company policies relevant to a support question."""
        # Runtime is intentionally injected for a uniform trust boundary. Company
        # policies are not customer-specific, so no state value is used here.
        _ = runtime
        return await call_service(lambda: services.policies.search(query))

    @tool()
    async def calculate_refund(
        order_id: UUID,
        runtime: ToolRuntime[None, SupportState],
    ) -> ToolResult:
        """Calculate the remaining refundable amount without changing any data."""
        customer_id = runtime.state["customer_id"]
        return await call_service(
            lambda: services.refunds.calculate(customer_id, order_id)
        )

    tools = [
        get_customer,
        get_order,
        get_order_items,
        get_shipment,
        search_company_policy,
        calculate_refund,
    ]
    return tools
