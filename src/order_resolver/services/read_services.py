from dataclasses import dataclass

from order_resolver.services.customer_read_service import CustomerReadService
from order_resolver.services.order_read_service import OrderReadService
from order_resolver.services.policy_read_service import PolicyReadService
from order_resolver.services.refund_read_service import RefundReadService


@dataclass(frozen=True)
class ReadServices:
    customers: CustomerReadService
    orders: OrderReadService
    policies: PolicyReadService
    refunds: RefundReadService
