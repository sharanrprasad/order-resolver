from dataclasses import dataclass

from order_resolver.services.customer_service import CustomerService
from order_resolver.services.order_service import OrderService
from order_resolver.services.policy_service import PolicyService
from order_resolver.services.refund_service import RefundService


@dataclass(frozen=True)
class Services:
    customers: CustomerService
    orders: OrderService
    policies: PolicyService
    refunds: RefundService
