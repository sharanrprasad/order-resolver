from typing import Any, cast

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from order_resolver.agent.graph import SupportGraph
from order_resolver.dependencies import application_dependency_factory
from order_resolver.services import Services


def test_application_dependencies_share_services_with_tools_and_graph(
    monkeypatch,
) -> None:
    session_factory = cast(async_sessionmaker[AsyncSession], object())
    services = cast(Services, object())
    model = cast(BaseChatModel, object())
    embedding_model = cast(Embeddings, object())
    checkpointer = cast(BaseCheckpointSaver, object())
    read_tool = cast(BaseTool, object())
    support_graph = cast(SupportGraph, object())
    calls: list[tuple[str, Any]] = []

    def fake_build_services(
        received_session_factory: async_sessionmaker[AsyncSession],
        received_embedding_model: Embeddings,
        received_embedding_model_name: str,
    ) -> Services:
        calls.append(
            (
                "services",
                (
                    received_session_factory,
                    received_embedding_model,
                    received_embedding_model_name,
                ),
            )
        )
        return services

    def fake_create_read_tools(received_services: Services) -> list[BaseTool]:
        calls.append(("tools", received_services))
        return [read_tool]

    def fake_build_support_graph(*args: Any, **kwargs: Any) -> SupportGraph:
        calls.append(("graph", (args, kwargs)))
        return support_graph

    monkeypatch.setattr(
        application_dependency_factory,
        "build_services",
        fake_build_services,
    )
    monkeypatch.setattr(
        application_dependency_factory,
        "create_read_tools",
        fake_create_read_tools,
    )
    monkeypatch.setattr(
        application_dependency_factory,
        "build_support_graph",
        fake_build_support_graph,
    )

    dependencies = application_dependency_factory.build_application_dependencies(
        session_factory,
        model=model,
        embedding_model=embedding_model,
        embedding_model_name="test-embedding-model",
        checkpointer=checkpointer,
    )

    assert dependencies.services is services
    assert dependencies.support_graph is support_graph
    assert calls == [
        (
            "services",
            (session_factory, embedding_model, "test-embedding-model"),
        ),
        ("tools", services),
        (
            "graph",
            (
                (model, services, (read_tool,)),
                {"checkpointer": checkpointer},
            ),
        ),
    ]
