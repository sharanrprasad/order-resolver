from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from order_resolver.agent.graph import build_support_graph
from order_resolver.agent.tools.read_tools import create_read_tools
from order_resolver.core.config import settings
from order_resolver.db.session import AsyncSessionLocal
from order_resolver.dependencies.application_dependencies import (
    ApplicationDependencies,
)
from order_resolver.dependencies.model_factory import (
    build_chat_model,
    build_embedding_model,
)
from order_resolver.dependencies.service_factory import build_services


def build_application_dependencies(
    session_factory: async_sessionmaker[AsyncSession] = AsyncSessionLocal,
    *,
    model: BaseChatModel,
    embedding_model: Embeddings,
    embedding_model_name: str = settings.embedding_model,
    checkpointer: BaseCheckpointSaver,
) -> ApplicationDependencies:
    """Build the dependency graph once for use by API and agent adapters."""
    services = build_services(
        session_factory,
        embedding_model,
        embedding_model_name,
    )
    read_tools = tuple(create_read_tools(services))
    support_graph = build_support_graph(
        model,
        services,
        read_tools,
        checkpointer=checkpointer,
    )
    return ApplicationDependencies(
        services=services,
        support_graph=support_graph,
    )


@asynccontextmanager
async def application_dependencies_context(
    session_factory: async_sessionmaker[AsyncSession] = AsyncSessionLocal,
    checkpoint_database_url: str = settings.checkpoint_database_url,
) -> AsyncIterator[ApplicationDependencies]:
    """Own application dependencies that require asynchronous cleanup."""
    model = build_chat_model()
    embedding_model = build_embedding_model()

    # TODO - Move this to a script so multiple instances won't try to create the same tables in Postgres.
    async with AsyncPostgresSaver.from_conn_string(
        checkpoint_database_url
    ) as checkpointer:
        await checkpointer.setup()
        yield build_application_dependencies(
            session_factory,
            model=model,
            embedding_model=embedding_model,
            embedding_model_name=settings.embedding_model,
            checkpointer=checkpointer,
        )
