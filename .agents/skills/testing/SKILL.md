---
name: testing
description: >-
  How this repo's tests are organised and run. Use when adding or changing tests,
  when a test run needs the integration database, or when deciding whether a new
  test belongs in the unit or integration suite.
---

# Testing

Two suites, selected by marker. Markers are applied automatically from the
directory a test lives in (`../../../tests/conftest.py`), so no per-test decorator is
needed.

| Suite | Location | Command | Talks to |
|-------|----------|---------|----------|
| unit | `../../../tests/unit` | `uv run pytest -m unit` | nothing - no DB, no network |
| integration | `../../../tests/integration` | `uv run pytest -m integration` | real Postgres, deterministic (mocked) LLM |

`uv run pytest` runs both. `make test-unit` / `make test-integration` wrap the
commands.

## Unit suite

Fast, isolated. The LLM is a `RunnableLambda` / `MagicMock`; the database is a
hand-written session fake. Node factories take their model and services as
constructor arguments (`create_*_node(...)`), so inject fakes directly. See
`../../../tests/unit/test_nodes.py` and `../../../tests/unit/test_read_tools.py` for the patterns.

Add a unit test here when it checks one function, node, edge, or SQL statement in
isolation.

## Integration suite

Scope: **`POST /support/requests` only** - the full LangGraph workflow, the
deterministic validation, and the refund / cancellation writes, running against a
real database. Each test asserts on the HTTP response *and* the resulting rows.

### Running it

```bash
docker compose -f docker-compose.integration.yml up -d   # Postgres on port 5433
uv run pytest -m integration
docker compose -f docker-compose.integration.yml down
```

If the database is not reachable the suite **skips** (never fails). Override the
connection with `INTEGRATION_DATABASE_URL`.

### How it is wired (`../../../tests/integration/conftest.py`)

- `_migrated_database` (session): runs `alembic upgrade head` once.
- `session_factory` (function): `TRUNCATE`s the commerce tables, re-seeds via
  `../../../tests/integration/seed.py`, hands back an `async_sessionmaker`.
- `support_client` (function): a factory `(*LLMScript*) -> httpx.AsyncClient`.
  It builds real `Services` on the test database, a support graph whose model is
  a `DeterministicChatModel`, and an app via `create_app(...)`.
- `db_session` (function): a session for reading rows back in assertions.

### The deterministic LLM (`../../../tests/integration/fake_llm.py`)

`build_support_graph` uses the model in three shapes: `with_structured_output`
(intent + proposed action), `bind_tools` (investigator loop), and raw `ainvoke`
(reply text). `LLMScript` captures one decision for each shape;
`DeterministicChatModel` serves them back with no network call. The scripted
investigator message carries no `tool_calls`, so the read-only tool loop is
skipped.

### Adding an integration test

1. Pick or add a seed row in `../../../tests/integration/seed.py` (fixed IDs).
2. Build an `LLMScript` with the intent, `order_id`, and `ProposedAction` the LLM
   would produce for that request (`scripted_action(...)` helper).
3. `client = support_client(script)`, then `await client.post("/support/requests", ...)`.
4. Assert on the response body **and** query `db_session` for the row effects.

Keep the deterministic-validation rules (`validate_action.py`) as the oracle:
the script proposes an action, the graph's own Python decides if it is allowed.
