from typing import cast

from fastapi import Request

from order_resolver.dependencies import ApplicationDependencies


def get_application_dependencies(request: Request) -> ApplicationDependencies:
    """Return the dependency graph owned by the current FastAPI application."""
    return cast(ApplicationDependencies, request.app.state.dependencies)
