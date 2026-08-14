from dataclasses import dataclass

from langchain_core.tools import BaseTool

from order_resolver.services.read_services import ReadServices


@dataclass(frozen=True)
class ApplicationDependencies:
    """Dependencies shared by the API and agent composition roots."""

    read_services: ReadServices
    read_tools: tuple[BaseTool, ...]
