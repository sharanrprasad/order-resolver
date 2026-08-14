from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from order_resolver.repositories.customer_repository import CustomerRepository
from order_resolver.repositories.order_repository import OrderRepository
from order_resolver.repositories.policy_repository import LocalPolicyRepository
from order_resolver.repositories.refund_repository import RefundRepository
from order_resolver.services.customer_read_service import CustomerReadService
from order_resolver.services.order_read_service import OrderReadService
from order_resolver.services.policy_read_service import PolicyReadService
from order_resolver.services.read_services import ReadServices
from order_resolver.services.refund_read_service import RefundReadService


def build_read_services(
    session_factory: async_sessionmaker[AsyncSession],
    documents_path: Path,
) -> ReadServices:
    """Construct read services from explicit infrastructure dependencies."""
    customer_repository = CustomerRepository(session_factory)
    order_repository = OrderRepository(session_factory)
    refund_repository = RefundRepository(session_factory)

    return ReadServices(
        customers=CustomerReadService(customer_repository),
        orders=OrderReadService(order_repository),
        policies=PolicyReadService(LocalPolicyRepository(documents_path)),
        refunds=RefundReadService(order_repository, refund_repository),
    )
