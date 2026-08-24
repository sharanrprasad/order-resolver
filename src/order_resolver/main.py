from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from order_resolver.api.routes.health import router as health_router
from order_resolver.api.routes.resources import router as resources_router
from order_resolver.api.routes.support import router as support_router
from order_resolver.dependencies import (
    ApplicationDependencies,
    application_dependencies_context,
)


def create_app(
    dependencies: ApplicationDependencies | None = None,
) -> FastAPI:
    """Create the API with a single application dependency graph."""

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        if dependencies is not None:
            yield
            return

        async with application_dependencies_context() as managed_dependencies:
            application.state.dependencies = managed_dependencies
            yield

    application = FastAPI(
        title="Order Resolver API",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.state.dependencies = dependencies
    application.include_router(health_router)
    application.include_router(support_router)
    application.include_router(resources_router)
    return application


app = create_app()
