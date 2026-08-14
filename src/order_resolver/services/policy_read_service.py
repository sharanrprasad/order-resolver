from order_resolver.repositories.policy_repository import LocalPolicyRepository
from order_resolver.services.read_models import PolicyDetails


class PolicyReadService:
    def __init__(self, repository: LocalPolicyRepository) -> None:
        self._repository = repository

    async def search(self, query: str, limit: int = 3) -> list[PolicyDetails]:
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("Policy search query cannot be empty.")
        bounded_limit = min(max(limit, 1), 5)
        matches = await self._repository.search(normalized_query, bounded_limit)
        return [PolicyDetails.model_validate(match) for match in matches]
