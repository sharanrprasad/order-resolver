from uuid import UUID

from order_resolver.repositories.customer_repository import CustomerRepository
from order_resolver.services.models import CustomerDetails
from order_resolver.services.resource_not_found_error import ResourceNotFoundError


class CustomerService:
    def __init__(self, repository: CustomerRepository) -> None:
        self._repository = repository

    async def get(self, customer_id: UUID) -> CustomerDetails:
        customer = await self._repository.get(customer_id)
        if customer is None:
            raise ResourceNotFoundError("Customer not found.")
        return CustomerDetails.model_validate(customer)
