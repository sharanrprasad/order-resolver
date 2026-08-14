from fastapi import FastAPI

from order_resolver.api.routes.health import router as health_router
from order_resolver.api.routes.resources import router as resources_router
from order_resolver.api.routes.support import router as support_router
from order_resolver.dependencies import (
    ApplicationDependencies,
    build_application_dependencies,
)


def create_app(
    dependencies: ApplicationDependencies | None = None,
) -> FastAPI:
    """Create the API with a single application dependency graph."""
    application = FastAPI(title="Order Resolver API", version="0.1.0")
    application.state.dependencies = dependencies or build_application_dependencies()
    application.include_router(health_router)
    application.include_router(support_router)
    application.include_router(resources_router)
    return application


app = create_app()
