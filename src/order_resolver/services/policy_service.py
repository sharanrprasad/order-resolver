from langchain_core.embeddings import Embeddings

from order_resolver.repositories.policy_repository import PolicyRepository
from order_resolver.services.models import PolicyDetails

# Minimum cosine similarity (1 - cosine_distance) a policy chunk must reach to be
# treated as relevant. Below this, retrieval returns nothing rather than the
# closest-but-unrelated policy. Tuned for OpenAI text-embedding-3-small.
DEFAULT_MIN_SCORE = 0.3


class PolicyService:
    def __init__(
        self,
        repository: PolicyRepository,
        embedding_model: Embeddings,
        embedding_model_name: str,
    ) -> None:
        self._repository = repository
        self._embedding_model = embedding_model
        self._embedding_model_name = embedding_model_name

    async def search(
        self,
        query: str,
        limit: int = 3,
        min_score: float = DEFAULT_MIN_SCORE,
    ) -> list[PolicyDetails]:
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("Policy search query cannot be empty.")

        bounded_limit = min(max(limit, 1), 5) # Max number of documents to retrieve.
        query_embedding = await self._embedding_model.aembed_query(normalized_query)
        matches = await self._repository.search(
            query_embedding,
            self._embedding_model_name,
            bounded_limit,
            min_score,
        )
        return [PolicyDetails.model_validate(match) for match in matches]
