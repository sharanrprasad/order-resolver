from typing import Any, cast
from uuid import UUID

from langchain_core.tools import BaseTool, tool
from langgraph.prebuilt import ToolRuntime

from order_resolver.agent.state import SupportState
from order_resolver.agent.tools.support import ToolResult, call_service
from order_resolver.services import Services


def create_read_tools(services: Services) -> list[BaseTool]:
    """Create the six read-only tools from an injected service collection."""

    @tool()
    async def get_customer(runtime: ToolRuntime[None, Any]) -> ToolResult:
        """Get the current customer's details."""
        state = cast(SupportState, runtime.state)
        customer_id = state["customer_id"]
        return await call_service(lambda: services.customers.get(customer_id))

    @tool()
    async def get_order(
        order_id: UUID,
        runtime: ToolRuntime[None, Any],
    ) -> ToolResult:
        """Get an order belonging to the current customer."""
        state = cast(SupportState, runtime.state)
        customer_id = state["customer_id"]
        return await call_service(lambda: services.orders.get(customer_id, order_id))

    @tool()
    async def get_order_items(
        order_id: UUID,
        runtime: ToolRuntime[None, Any],
    ) -> ToolResult:
        """Get line items for an order belonging to the current customer."""
        state = cast(SupportState, runtime.state)
        customer_id = state["customer_id"]
        return await call_service(
            lambda: services.orders.get_items(customer_id, order_id)
        )

    @tool()
    async def get_shipment(
        order_id: UUID,
        runtime: ToolRuntime[None, Any],
    ) -> ToolResult:
        """Get shipment details for an order belonging to the current customer."""
        state = cast(SupportState, runtime.state)
        customer_id = state["customer_id"]
        return await call_service(
            lambda: services.orders.get_shipment(customer_id, order_id)
        )

    @tool()
    async def search_company_policy(
        query: str,
        runtime: ToolRuntime[None, Any],
    ) -> ToolResult:
        """Semantically search company policy using a concise support-related query."""
        # Runtime is intentionally injected for a uniform trust boundary. Company
        # policies are not customer-specific, so no state value is used here.
        _ = runtime
        return await call_service(lambda: services.policies.search(query))

    @tool()
    async def calculate_refund(
        order_id: UUID,
        runtime: ToolRuntime[None, Any],
    ) -> ToolResult:
        """Calculate the remaining refundable amount without changing any data."""
        state = cast(SupportState, runtime.state)
        customer_id = state["customer_id"]
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
