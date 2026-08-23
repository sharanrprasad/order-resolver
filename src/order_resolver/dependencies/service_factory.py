from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from order_resolver.repositories.customer_repository import CustomerRepository
from order_resolver.repositories.order_repository import OrderRepository
from order_resolver.repositories.policy_repository import LocalPolicyRepository
from order_resolver.repositories.refund_repository import RefundRepository
from order_resolver.services.customer_service import CustomerService
from order_resolver.services.order_service import OrderService
from order_resolver.services.policy_service import PolicyService
from order_resolver.services.refund_service import RefundService
from order_resolver.services.services import Services


def build_services(
    session_factory: async_sessionmaker[AsyncSession],
    documents_path: Path,
) -> Services:
    """Construct application services from explicit infrastructure dependencies."""
    customer_repository = CustomerRepository(session_factory)
    order_repository = OrderRepository(session_factory)
    refund_repository = RefundRepository(session_factory)

    return Services(
        customers=CustomerService(customer_repository),
        orders=OrderService(order_repository),
        policies=PolicyService(LocalPolicyRepository(documents_path)),
        refunds=RefundService(order_repository, refund_repository),
    )
