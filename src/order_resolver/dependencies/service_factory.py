from langchain_core.embeddings import Embeddings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from order_resolver.repositories.customer_repository import CustomerRepository
from order_resolver.repositories.order_repository import OrderRepository
from order_resolver.repositories.policy_repository import PolicyRepository
from order_resolver.repositories.refund_repository import RefundRepository
from order_resolver.services.customer_service import CustomerService
from order_resolver.services.order_service import OrderService
from order_resolver.services.policy_service import PolicyService
from order_resolver.services.refund_service import RefundService
from order_resolver.services.services import Services


def build_services(
    session_factory: async_sessionmaker[AsyncSession],
    embedding_model: Embeddings,
    embedding_model_name: str,
) -> Services:
    """Construct application services from explicit infrastructure dependencies."""
    customer_repository = CustomerRepository(session_factory)
    order_repository = OrderRepository(session_factory)
    policy_repository = PolicyRepository(session_factory)
    refund_repository = RefundRepository(session_factory)

    return Services(
        customers=CustomerService(customer_repository),
        orders=OrderService(order_repository),
        policies=PolicyService(
            policy_repository,
            embedding_model,
            embedding_model_name,
        ),
        refunds=RefundService(order_repository, refund_repository),
    )
