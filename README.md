# Order Resolver

Learning scaffold for an AI-assisted e-commerce support service using FastAPI,
LangGraph, PostgreSQL, and pgvector. The project currently provides boundaries
and wiring only; business rules, LLM calls, tools, RAG, and write actions are
intentionally left for you to implement.

## Local setup

```bash
cp .env.example .env
docker compose up -d
uv sync --dev   # Installs dev dependencies as well. 
uv run alembic upgrade head
uv run python scripts/seed_database.py
uv run uvicorn order_resolver.main:app --reload
```

Migrations and seeding are separate on purpose. `docker compose up` starts the
database but does not mutate its schema or insert application data.

Run unit tests with:

```bash
uv run pytest
```

## Layout

- `src/order_resolver/agent`: typed state, placeholder nodes, and graph topology
- `src/order_resolver/api`: FastAPI routers
- `src/order_resolver/db`: SQLAlchemy models and session factory
- `migrations`: Alembic configuration and initial schema (not auto-run)
- `scripts/seed_database.py`: small deterministic local dataset
- `docs`: policy documents to be ingested later

The support endpoints return `501 Not Implemented` until graph execution and
persistence are connected. `/health` is usable now.
