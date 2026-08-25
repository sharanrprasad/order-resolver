import pytest
from langchain_core.embeddings import Embeddings

from order_resolver.repositories.policy_repository import PolicyMatch
from order_resolver.services.policy_service import PolicyService


class EmbeddingModelStub(Embeddings):
    def __init__(self) -> None:
        self.queries: list[str] = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise AssertionError("Policy search should not embed documents at runtime")

    def embed_query(self, text: str) -> list[float]:
        raise AssertionError("Policy search should use the async embedding API")

    async def aembed_query(self, text: str) -> list[float]:
        self.queries.append(text)
        return [0.1, 0.2, 0.3]


class PolicyRepositoryStub:
    def __init__(self) -> None:
        self.search_args: tuple[list[float], str, int] | None = None

    async def search(
        self,
        query_embedding: list[float],
        embedding_model_name: str,
        limit: int,
    ) -> list[PolicyMatch]:
        self.search_args = (query_embedding, embedding_model_name, limit)
        return [
            PolicyMatch(
                source="refund-policy.md",
                content="Refund policy",
                score=0.91,
            )
        ]


@pytest.mark.asyncio
async def test_search_embeds_the_normalized_query_and_bounds_the_limit() -> None:
    repository = PolicyRepositoryStub()
    embedding_model = EmbeddingModelStub()
    service = PolicyService(
        repository,  # type: ignore[arg-type]
        embedding_model,
        "test-embedding-model",
    )

    results = await service.search("  refund a delivered order  ", limit=100)

    assert embedding_model.queries == ["refund a delivered order"]
    assert repository.search_args == (
        [0.1, 0.2, 0.3],
        "test-embedding-model",
        5,
    )
    assert results[0].source == "refund-policy.md"
    assert results[0].score == pytest.approx(0.91)


@pytest.mark.asyncio
async def test_search_rejects_an_empty_query_before_embedding() -> None:
    repository = PolicyRepositoryStub()
    embedding_model = EmbeddingModelStub()
    service = PolicyService(
        repository,  # type: ignore[arg-type]
        embedding_model,
        "test-embedding-model",
    )

    with pytest.raises(ValueError, match="cannot be empty"):
        await service.search("   ")

    assert embedding_model.queries == []
    assert repository.search_args is None
