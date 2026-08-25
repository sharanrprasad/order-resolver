from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from order_resolver.db.models import CompanyPolicy


@dataclass(frozen=True)
class PolicyMatch:
    source: str
    content: str
    score: float


class PolicyRepository:
    """Search embedded company policies stored in Postgres."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def search(
        self,
        query_embedding: list[float],
        embedding_model_name: str,
        limit: int,
    ) -> list[PolicyMatch]:
        distance = CompanyPolicy.embedding.cosine_distance(query_embedding)
        statement = (
            select(
                CompanyPolicy.source,
                CompanyPolicy.content,
                (1 - distance).label("score"),
            )
            .where(CompanyPolicy.embedding_model == embedding_model_name)
            .order_by(distance, CompanyPolicy.source)
            .limit(limit)
        )

        async with self._session_factory() as session:
            rows = (await session.execute(statement)).all()

        return [
            PolicyMatch(source=source, content=content, score=float(score))
            for source, content, score in rows
        ]
