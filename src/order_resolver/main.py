from fastapi import FastAPI

from order_resolver.api.routes.health import router as health_router
from order_resolver.api.routes.resources import router as resources_router
from order_resolver.api.routes.support import router as support_router

app = FastAPI(title="Order Resolver API", version="0.1.0")
app.include_router(health_router)
app.include_router(support_router)
app.include_router(resources_router)
