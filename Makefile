.PHONY: test test-unit test-integration integration-db-up integration-db-down lint typecheck

# Fast, isolated tests - no database, no network.
test-unit:
	uv run pytest -m unit

# Bring up the throwaway Postgres for the integration suite.
integration-db-up:
	docker compose -f docker-compose.integration.yml up -d --wait

integration-db-down:
	docker compose -f docker-compose.integration.yml down

# End-to-end API tests. Requires the integration database (integration-db-up);
# the suite skips itself if it cannot connect.
test-integration:
	uv run pytest -m integration

# Everything (integration tests skip when their database is unavailable).
test:
	uv run pytest

lint:
	uv run ruff check

typecheck:
	uv run pyright
