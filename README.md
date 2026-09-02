# Order Resolver

A learning project to figure out end to end development of an AI agent that processes the cancellation or refund requests of a customer.


## Local setup

```bash
cp .env.example .env
docker compose up -d
uv sync --dev   # Installs dev dependencies as well. 
uv run alembic upgrade head
uv run python scripts/seed_database.py
uv run python scripts/seed_policy_documents.py
uv run uvicorn order_resolver.main:app --reload
```

The first policy seed run uses `OPENAI_API_KEY` and `EMBEDDING_MODEL` to embed the
Markdown files under `docs/`. Later runs skip unchanged policies, re-embed
changed policies, and remove records for deleted files.

Application migrations and seeding are separate on purpose. `docker compose up`
starts the database but does not mutate its schema or insert application data.
FastAPI startup initializes LangGraph's checkpoint tables and applies
LangGraph-managed checkpoint migrations.

### Tests

Two suites, run independently:

```bash
# Unit - fast, no I/O, no external services
uv run pytest -m unit

# Integration - drives the FastAPI app (POST /support/requests) against a real
# Postgres database with a deterministic, offline LLM
docker compose -f docker-compose.integration.yml up -d
uv run pytest -m integration
docker compose -f docker-compose.integration.yml down
```

`uv run pytest` runs both; the integration suite skips itself when its database
(port 5433) is not reachable. `make test-unit` / `make test-integration` wrap the
same commands. See `.agents/skills/testing/SKILL.md` for how to add tests to each
suite.

Run static type checker 

```bash
uv run pyright
```

## Layout

- `src/order_resolver/agent`: typed state, placeholder nodes, and graph topology
- `src/order_resolver/api`: FastAPI routers
- `src/order_resolver/db`: SQLAlchemy models and session factory
- `migrations`: Alembic configuration and initial schema (not auto-run)
- `scripts/seed_database.py`: deterministic commerce demo data
- `scripts/seed_policy_documents.py`: idempotent policy embedding ingestion
- `docs`: source Markdown documents mirrored into `company_policies` by the seed script

The support endpoints return `501 Not Implemented` until graph execution is
connected. Postgres checkpoint storage is initialized during application
startup, and `/health` is usable now.

### LangGraph checkpoints

Checkpoints use `DATABASE_URL` by default. Set `CHECKPOINT_DATABASE_URL` to a
plain Psycopg URL such as `postgresql://user:password@host:5432/database` when
checkpoint data should use a different database.

Every graph invocation, resume, and state lookup must use the same thread ID:

```python
config = {"configurable": {"thread_id": thread_id}}
```

Alembic owns the application schema. The LangGraph Postgres saver owns its
checkpoint tables and internal checkpoint migrations.


## LangGraph graph 

```text
START
  ↓
understand_request
  ↓
investigate  ←──────────────┐
  │                         │
  ├─ tool call → read_only_tools
  │                         │
  └─────────────────────────┘
  │
  └─ investigation complete
          ↓
    validate_action
          │
     ┌────┴─────────────────────┐
     │                          │
 invalid                  valid + approval required
     │                          │
failure_response          human_approval
                                │
                           interrupt/persist
                                │
                         approved or rejected
                           /             \
                    approved             rejected
                       ↓                    ↓
                 execute_action      failure_response

valid + no approval
        ↓
execute_action
        │
    execution success?
       /          \
     yes           no
      ↓             ↓
success_response  failure_response
      ↓             ↓
     END           END
```
