from dataclasses import dataclass

from langchain_core.tools import BaseTool

from order_resolver.services.services import Services


@dataclass(frozen=True)
class ApplicationDependencies:
    """Dependencies shared by the API and agent composition roots."""

    services: Services
    read_tools: tuple[BaseTool, ...]
