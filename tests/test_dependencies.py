from pathlib import Path
from typing import Any, cast

from langchain_core.tools import BaseTool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from order_resolver.dependencies import application_dependency_factory
from order_resolver.services import ReadServices


def test_application_dependencies_build_services_and_tools_once(
    monkeypatch,
    tmp_path: Path,
) -> None:
    session_factory = cast(async_sessionmaker[AsyncSession], object())
    read_services = cast(ReadServices, object())
    read_tool = cast(BaseTool, object())
    calls: list[tuple[str, Any]] = []

    def fake_build_read_services(
        received_session_factory: async_sessionmaker[AsyncSession],
        received_documents_path: Path,
    ) -> ReadServices:
        calls.append(
            (
                "services",
                (received_session_factory, received_documents_path),
            )
        )
        return read_services

    def fake_create_read_tools(received_services: ReadServices) -> list[BaseTool]:
        calls.append(("tools", received_services))
        return [read_tool]

    monkeypatch.setattr(
        application_dependency_factory,
        "build_read_services",
        fake_build_read_services,
    )
    monkeypatch.setattr(
        application_dependency_factory,
        "create_read_tools",
        fake_create_read_tools,
    )

    dependencies = application_dependency_factory.build_application_dependencies(
        session_factory,
        tmp_path,
    )

    assert dependencies.read_services is read_services
    assert dependencies.read_tools == (read_tool,)
    assert calls == [
        ("services", (session_factory, tmp_path)),
        ("tools", read_services),
    ]
