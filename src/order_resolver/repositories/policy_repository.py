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
        min_score: float = 0.0,
    ) -> list[PolicyMatch]:
        """Return the closest policies ordered by similarity.

        ``min_score`` is the minimum cosine similarity (``1 - cosine_distance``,
        in ``[-1, 1]``) a row must reach to be returned; ``0.0`` disables the
        filter and keeps the previous behaviour.
        """
        distance = CompanyPolicy.embedding.cosine_distance(query_embedding)
        similarity = 1 - distance
        statement = (
            select(
                CompanyPolicy.source,
                CompanyPolicy.content,
                similarity.label("score"),
            )
            .where(CompanyPolicy.embedding_model == embedding_model_name)
            .order_by(distance, CompanyPolicy.source)
            .limit(limit)
        )
        if min_score > 0.0:
            statement = statement.where(similarity >= min_score)

        async with self._session_factory() as session:
            rows = (await session.execute(statement)).all()

        return [
            PolicyMatch(source=source, content=content, score=float(score))
            for source, content, score in rows
        ]
