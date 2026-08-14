from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from order_resolver.db.models import Customer


class CustomerRepository:
    """Read customers without exposing an unscoped list operation."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get(self, customer_id: UUID) -> Customer | None:
        async with self._session_factory() as session:
            return await session.scalar(
                select(Customer).where(Customer.id == customer_id)
            )
