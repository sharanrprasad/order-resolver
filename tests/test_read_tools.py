from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from order_resolver.agent.state import SupportState
from order_resolver.agent.tools import create_read_tools
from order_resolver.services import ReadServices, ResourceNotFoundError
from order_resolver.services.read_models import CustomerDetails, RefundCalculation

CUSTOMER_ID = UUID("00000000-0000-0000-0000-000000000001")
ORDER_ID = UUID("00000000-0000-0000-0000-000000000101")


class CustomerServiceStub:
    def __init__(self) -> None:
        self.requested_customer_id: UUID | None = None
        self.call_count = 0

    async def get(self, customer_id: UUID) -> CustomerDetails:
        self.requested_customer_id = customer_id
        self.call_count += 1
        return CustomerDetails(
            id=customer_id,
            name="Current Customer",
            email="current@example.com",
            membership_tier="gold",
            created_at=datetime.now(UTC),
        )


class OrderServiceStub:
    def __init__(self) -> None:
        self.requested_scope: tuple[UUID, UUID] | None = None

    async def get(self, customer_id: UUID, order_id: UUID):
        self.requested_scope = (customer_id, order_id)
        raise ResourceNotFoundError("Order not found.")

    async def get_items(self, customer_id: UUID, order_id: UUID):
        self.requested_scope = (customer_id, order_id)
        return []

    async def get_shipment(self, customer_id: UUID, order_id: UUID):
        self.requested_scope = (customer_id, order_id)
        raise ResourceNotFoundError("No shipment found for this order.")


class PolicyServiceStub:
    async def search(self, query: str):
        return []


class RefundServiceStub:
    async def calculate(
        self, customer_id: UUID, order_id: UUID
    ) -> RefundCalculation:
        return RefundCalculation(
            order_id=order_id,
            order_total=Decimal("49.99"),
            already_reserved=Decimal(0),
            refundable_amount=Decimal("49.99"),
        )


def make_services() -> tuple[ReadServices, CustomerServiceStub, OrderServiceStub]:
    customers = CustomerServiceStub()
    orders = OrderServiceStub()
    services = ReadServices(
        customers=customers,  # type: ignore[arg-type]
        orders=orders,  # type: ignore[arg-type]
        policies=PolicyServiceStub(),  # type: ignore[arg-type]
        refunds=RefundServiceStub(),  # type: ignore[arg-type]
    )
    return services, customers, orders


async def invoke_tool_node(tools, tool_call):
    graph_builder = StateGraph(SupportState)
    graph_builder.add_node("read_tools", ToolNode(tools))
    graph_builder.add_edge(START, "read_tools")
    graph_builder.add_edge("read_tools", END)
    graph = graph_builder.compile()
    return await graph.ainvoke(
        {
            "customer_id": CUSTOMER_ID,
            "messages": [AIMessage(content="", tool_calls=[tool_call])],
        }
    )


@pytest.mark.asyncio
async def test_customer_id_is_injected_and_hidden_from_tool_schema() -> None:
    services, customers, _ = make_services()
    tools = create_read_tools(services)
    customer_tool = next(tool for tool in tools if tool.name == "get_customer")

    assert len(tools) == 6
    assert all(isinstance(tool, BaseTool) for tool in tools)
    assert customer_tool.tool_call_schema.model_json_schema()["properties"] == {}

    result = await invoke_tool_node(
        tools,
        {"name": "get_customer", "args": {}, "id": "1"},
    )
    await invoke_tool_node(
        tools,
        {"name": "get_customer", "args": {}, "id": "2"},
    )

    assert customers.requested_customer_id == CUSTOMER_ID
    assert customers.call_count == 2
    assert '"ok": true' in result["messages"][-1].content


@pytest.mark.asyncio
async def test_order_lookup_always_uses_runtime_customer_scope() -> None:
    services, _, orders = make_services()
    tools = create_read_tools(services)
    result = await invoke_tool_node(
        tools,
        {
            "name": "get_order",
            "args": {"order_id": str(ORDER_ID)},
            "id": "2",
        },
    )

    assert orders.requested_scope == (CUSTOMER_ID, ORDER_ID)
    assert '"code": "not_found"' in result["messages"][-1].content
