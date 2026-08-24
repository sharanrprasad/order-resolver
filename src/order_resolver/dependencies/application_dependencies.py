from dataclasses import dataclass

from order_resolver.agent.graph import SupportGraph
from order_resolver.services.services import Services


@dataclass(frozen=True)
class ApplicationDependencies:
    """Application services and the compiled support workflow."""

    services: Services
    support_graph: SupportGraph
