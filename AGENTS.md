# AGENTS.md

## Purpose

This file contains repository-wide instructions for coding agents working on this project.

For detailed product requirements and workflow behaviour, use `spec.md` as the source of truth. For customer-facing business policy text used by RAG, use the Markdown files under `docs/`.

Keep changes focused on the requested task. Prefer simple, readable production-style code over unnecessary abstractions or unrelated refactors.

## Project Context

This repository implements a backend AI e-commerce customer-support / order-resolution system using Python, FastAPI, LangGraph, OpenAI, PostgreSQL, SQLAlchemy, Pydantic, pgvector, Alembic, and pytest.

The LLM is used for interpretation, investigation, policy retrieval, and proposing actions. Deterministic application code remains authoritative for business validation and writes.

## Architecture Invariants

Preserve these boundaries:

- LLM-callable tools are read-only.
- LangGraph orchestrates workflow and tool loops.
- Business-critical validation is deterministic Python.
- Refund and cancellation writes go through trusted application services, not the LLM.
- `execute_action` is the final trusted write boundary.
- Write operations must be idempotent.
- Policy documents inform the LLM but do not replace deterministic validation.

Do not expose refund creation or order cancellation as LLM-callable tools unless the architecture is explicitly changed.

## Core Business Rules

### Cancellation

- Cancellation is for stopping an order before shipment.
- Cancellable order statuses are `pending`, `paid`, and `processing`.
- Do not cancel orders that are `shipped`, `delivered`, or already `cancelled`.
- If shipment state is `shipped`, `in_transit`, `delivered`, or `lost`, cancellation is not allowed.
- If a paid order is cancelled, any required payment reversal/refund is handled as part of cancellation. Do not propose a separate refund for the same cancellation.

### Refunds

Standalone refunds are supported only when:

- the shipment is confirmed `lost`, or
- a delivered item is reported damaged.

Do not treat a late or `in_transit` shipment as lost. Generic post-delivery return windows are outside the current scope.

Refunds must not exceed the remaining refundable amount and must not create duplicates.

### Human Approval

Human approval is required when:

- the refund amount is greater than `$100`, or
- the refund is for a damaged-item claim, regardless of amount.

If approval is required, `execute_action` must independently verify that `approval_status == APPROVED` before performing the write. Do not rely only on graph routing.

## LangGraph Conventions

Use `TypedDict` for graph state unless there is a strong reason to change it.

Use Pydantic models for structured domain values and structured LLM outputs such as `ParsedRequest`, `ProposedAction`, `ValidationResult`, and `ExecutedAction`.

Use LangGraph's `add_messages` reducer for message history.

Read-tool results may remain in `ToolMessage` entries unless deterministic workflow code needs the data as an explicit state field.

The investigation model may call read tools and propose a `ProposedAction`, but it must never perform writes.

`validate_action` must re-check business-critical facts using trusted services rather than trusting LLM reasoning or prior tool output alone.

Use LangGraph `interrupt()` for human approval. Do not place non-idempotent side effects before `interrupt()` because the node may execute again when resumed.

Human notification belongs in the application/service layer observing the interrupt, not inside the approval node.

## Tool Conventions

Expected LLM-callable tools are read-only operations such as:

- `get_customer`
- `get_order`
- `get_order_items`
- `get_shipment`
- `search_company_policy`
- `calculate_refund`

Use LangGraph `ToolNode` to execute model-requested tools.

Trusted `customer_id` must come from application/graph runtime state, not from an LLM-controlled argument.

Order-related service/repository calls must enforce customer ownership.

Tool failures should return stable, LLM-readable results without exposing internal exceptions.

## Python Conventions

- Use modern Python typing.
- Prefer domain types such as `UUID`, `Decimal`, `StrEnum`, `Literal`, and `TypedDict` over loosely typed strings/dicts where appropriate.
- Use `Decimal` for money; never use `float` for monetary calculations.
- Use `UUID` internally for identifiers.
- Use async code for I/O-bound database, LLM, tool, and external-service operations.
- Prefer dependency injection through factory functions for graph nodes and tools when it improves testability.
- Avoid creating expensive or environment-dependent dependencies at import time when injection is practical.
- Use Pydantic validation for structured LLM outputs.
- Use timezone-aware datetimes for persisted timestamps.
- Use SQLAlchemy 2.x APIs and Alembic for schema changes.

Follow existing naming, module layout, and typing patterns in nearby code before introducing new abstractions.

## Safety and Write Boundaries

Before performing a refund or cancellation write:

- deterministic validation must have succeeded;
- customer ownership must have been verified;
- the action must still satisfy current business rules;
- any required human approval must be present;
- the operation must be safe to retry.

Do not trust an LLM-generated value as authoritative for approval, ownership, refund eligibility, or write success.

## Testing

Use pytest and keep normal unit tests independent of live OpenAI calls.

When changing business logic, add or update tests covering the changed rule. In particular, preserve coverage for:

- cancellation before vs. after shipment;
- lost-shipment refunds;
- damaged-item approval;
- refunds over `$100` requiring approval;
- duplicate-refund prevention;
- ownership checks;
- write operations not bypassing validation or approval.

Run the relevant test suite and any configured formatter/linter before considering a change complete.

## Scope

Do not add major out-of-scope capabilities such as frontend/UI, MCP, multi-agent orchestration, real payment-gateway integration, fraud scoring, or damaged-item evidence verification unless explicitly requested.

Do not duplicate the full product specification in this file. Keep detailed workflows, API contracts, seed scenarios, and exhaustive test cases in `spec.md` or other project documentation.
