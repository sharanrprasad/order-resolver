"""Fixtures for the integration suite.

These tests exercise ``POST /support/requests`` against a real Postgres database
(``docker-compose.integration.yml``) with a deterministic, offline LLM. If the
database is not reachable the whole suite is skipped rather than failed.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Callable, Iterator
from pathlib import Path
from typing import cast

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.memory import InMemorySaver
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from order_resolver.agent.graph import build_support_graph
from order_resolver.agent.tools.read_tools import create_read_tools
from order_resolver.dependencies.application_dependencies import ApplicationDependencies
from order_resolver.dependencies.service_factory import build_services
from order_resolver.main import create_app
from tests.integration.fake_llm import DeterministicChatModel, LLMScript
from tests.integration.seed import seed_commerce_data

_REPO_ROOT = Path(__file__).resolve().parents[2]

INTEGRATION_DATABASE_URL = os.getenv(
    "INTEGRATION_DATABASE_URL",
    "postgresql+psycopg://order_resolver:order_resolver"
    "@localhost:5433/order_resolver_integration",
)

_MANAGED_TABLES = "customers, orders, order_items, shipments, refunds"


def _psycopg_dsn(url: str) -> str:
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


@pytest.fixture(scope="session")
def _database_url() -> str:
    """Skip the whole suite unless the integration database is reachable."""
    try:
        with psycopg.connect(_psycopg_dsn(INTEGRATION_DATABASE_URL), connect_timeout=2):
            pass
    except psycopg.OperationalError as exc:  # pragma: no cover - env dependent
        pytest.skip(
            "integration database not reachable at "
            f"{INTEGRATION_DATABASE_URL}. Start it with: "
            "docker compose -f docker-compose.integration.yml up -d\n"
            f"({exc})"
        )
    return INTEGRATION_DATABASE_URL


@pytest.fixture(scope="session")
def _migrated_database(_database_url: str) -> Iterator[None]:
    """Run Alembic migrations once against the integration database."""
    config = Config(str(_REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(_REPO_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", _database_url)
    # Match alembic.ini's space-separated prepend_sys_path and silence the
    # "no path_separator" deprecation warning when invoked programmatically.
    config.set_main_option("path_separator", "space")

    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = _database_url
    try:
        command.upgrade(config, "head")
        yield
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous


@pytest.fixture
async def session_factory(
    _migrated_database: None,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """A clean, freshly seeded database for one test."""
    engine = create_async_engine(INTEGRATION_DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.execute(
            text(f"TRUNCATE {_MANAGED_TABLES} RESTART IDENTITY CASCADE")
        )
    async with factory() as session:
        await seed_commerce_data(session)
        await session.commit()

    try:
        yield factory
    finally:
        await engine.dispose()


@pytest.fixture
async def db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """A session for reading rows back in assertions."""
    async with session_factory() as session:
        yield session


class _StubEmbeddings(Embeddings):
    """Never called by these tests (the fake model requests no tools); required
    only to construct the policy service."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 8 for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [0.0] * 8


@pytest.fixture
async def support_client(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[Callable[[LLMScript], AsyncClient]]:
    """Return a factory that builds an HTTP client wired to a scripted LLM."""
    clients: list[AsyncClient] = []

    def _make(script: LLMScript) -> AsyncClient:
        services = build_services(session_factory, _StubEmbeddings(), "stub-embeddings")
        graph = build_support_graph(
            cast(BaseChatModel, cast(object, DeterministicChatModel(script))),
            services,
            list(create_read_tools(services)),
            checkpointer=InMemorySaver(),
        )
        # create_app sets app.state.dependencies directly, and the request
        # dependency reads it from there - ASGITransport never runs lifespan.
        app = create_app(
            ApplicationDependencies(services=services, support_graph=graph)
        )
        client = AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        )
        clients.append(client)
        return client

    try:
        yield _make
    finally:
        for client in clients:
            await client.aclose()
