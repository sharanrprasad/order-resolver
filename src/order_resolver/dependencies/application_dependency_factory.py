from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from order_resolver.agent.tools.read_tools import create_read_tools
from order_resolver.db.session import AsyncSessionLocal
from order_resolver.dependencies.application_dependencies import (
    ApplicationDependencies,
)
from order_resolver.dependencies.service_factory import build_services

DEFAULT_POLICY_DOCUMENTS_PATH = Path(__file__).resolve().parents[3] / "docs"


def build_application_dependencies(
    session_factory: async_sessionmaker[AsyncSession] = AsyncSessionLocal,
    documents_path: Path = DEFAULT_POLICY_DOCUMENTS_PATH,
) -> ApplicationDependencies:
    """Build the dependency graph once for use by API and agent adapters."""
    services = build_services(session_factory, documents_path)
    read_tools = tuple(create_read_tools(services))
    return ApplicationDependencies(
        services=services,
        read_tools=read_tools,
    )
