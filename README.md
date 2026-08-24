# Order Resolver

A learning project to figure out end to end development of an AI agent that processes the cancellation or refund requests of a customer.


## Local setup

```bash
cp .env.example .env
docker compose up -d
uv sync --dev   # Installs dev dependencies as well. 
uv run alembic upgrade head
uv run python scripts/seed_database.py
uv run uvicorn order_resolver.main:app --reload
```

Application migrations and seeding are separate on purpose. `docker compose up`
starts the database but does not mutate its schema or insert application data.
FastAPI startup initializes LangGraph's checkpoint tables and applies
LangGraph-managed checkpoint migrations.

Run unit tests with:

```bash
uv run pytest
```

Run static type checker 

```bash
uv run pyright
```

## Layout

- `src/order_resolver/agent`: typed state, placeholder nodes, and graph topology
- `src/order_resolver/api`: FastAPI routers
- `src/order_resolver/db`: SQLAlchemy models and session factory
- `migrations`: Alembic configuration and initial schema (not auto-run)
- `scripts/seed_database.py`: small deterministic local dataset
- `docs`: policy documents to be ingested later

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
