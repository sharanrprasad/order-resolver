Build a backend API and AI agent for an **AI E-commerce Customer Support / Order Resolution system**.

The goal of the project is to demonstrate production-style AI agent development using **Python, FastAPI, LangGraph, OpenAI, PostgreSQL, pgvector, and Pydantic**.

Do not build a frontend yet. Do not implement MCP yet. Focus only on the API, LangGraph agent, database, RAG, tests, and local Docker setup.

## Tech Stack

Use:

* Python 3.11+
* FastAPI
* LangGraph
* LangChain OpenAI integration
* OpenAI API
* Pydantic
* PostgreSQL
* SQLAlchemy 2.x
* Alembic
* pgvector
* pytest
* Docker / Docker Compose

Use async Python where appropriate.

Follow clean architecture principles without over-engineering.

## Business Scenario

The application represents an e-commerce company's customer support system.

Customers should be able to send natural-language support requests such as:

* "Where is order 123?"
* "My order hasn't arrived yet."
* "I want to cancel order 456."
* "Can I get a refund for order 789?"
* "The item I received is damaged."
* "I haven't received my order and the expected delivery date was last week."

The AI agent must investigate the request using tools rather than having all business data injected into the prompt.

The agent should gather information, retrieve applicable company policies, determine an appropriate action, and return a structured recommendation.

Sensitive actions such as large refunds should require human approval.

## Database Model

Create PostgreSQL tables/models for:

### Customer

Fields:

* id
* name
* email
* membership_tier
* created_at

### Order

Fields:

* id
* customer_id
* status
* total
* created_at

Possible statuses:

* pending
* paid
* processing
* shipped
* delivered
* cancelled

### OrderItem

Fields:

* id
* order_id
* product_name
* quantity
* unit_price

### Shipment

Fields:

* id
* order_id
* carrier
* tracking_number
* status
* estimated_delivery
* delivered_at

Possible statuses:

* pending
* shipped
* in_transit
* delivered
* lost

### Refund

Fields:

* id
* order_id
* amount
* reason
* status
* created_at

Statuses:

* pending
* approved
* rejected
* completed

Create proper primary keys, foreign keys, constraints, indexes, and relationships.

Use migrations via Alembic.

## Seed Data

Create a seed script that generates realistic test data including:

* customers
* orders
* order items
* shipments
* refunds

Include scenarios useful for testing the agent, such as:

* delivered order
* late shipment
* lost shipment
* order that has not shipped
* already refunded order
* expensive order requiring refund approval
* order outside the return period

Keep the dataset reasonably small for running locally.

## Company Policies / RAG

Create local Markdown documents under:

docs/

Include:

* refund-policy.md
* shipping-policy.md
* cancellation-policy.md
* damaged-items-policy.md
* lost-package-policy.md

Example rules should include things such as:

* Orders can be cancelled before shipment.
* Delivered products can normally be returned within 30 days.
* Lost shipments can be refunded when sufficiently overdue.
* Refunds greater than $100 require human approval.
* Duplicate refunds must never be issued.

Implement document ingestion.

Chunk the documents, generate OpenAI embeddings, and store embeddings in PostgreSQL using pgvector.

Implement semantic policy search.

The agent should retrieve relevant policy sections when deciding what action is allowed.

## LangGraph Agent

Implement the support workflow using LangGraph.

Do NOT make the entire workflow a single LLM call.

Use a combination of:

* LLM-based nodes
* deterministic Python nodes
* conditional graph edges
* tools
* persistent state
* human-in-the-loop interrupts

Define a typed LangGraph state containing approximately:

* messages
* customer_id
* order_id
* intent
* customer
* order
* shipment
* relevant_policies
* proposed_action
* requires_approval
* approval_status
* final_response

Adapt this structure if necessary.

## Suggested Graph

Design something similar to:

START

→ understand_request

→ investigate

→ retrieve_relevant_policy

→ determine_action

→ validate_action

→ check_approval_requirement

If approval is NOT required:

→ execute_action

→ generate_response

→ END

If approval IS required:

→ interrupt and wait for human approval

If approved:

→ execute_action

→ generate_response

→ END

If rejected:

→ generate_response explaining that the action was not approved

→ END

Use LangGraph's persistence/checkpoint functionality so interrupted workflows can resume later.

## Agent Tools

Implement tools approximately like:

### get_customer

Retrieve customer information.

### get_order

Retrieve an order.

The tool must verify that the order belongs to the requested customer when appropriate.

### get_order_items

Retrieve items belonging to an order.

### get_shipment

Retrieve shipment information.

### search_company_policy

Perform semantic search against policy documents using pgvector.

### calculate_refund

Calculate the refundable amount without changing database state.

### create_refund

Create the refund.

This is a WRITE operation.

It must be idempotent.

It must never create a duplicate refund for the same approved request.

### cancel_order

Cancel an order only when business rules allow it.

This is a WRITE operation.

Keep READ tools distinct from WRITE tools.

## Important Agent Behaviour

The agent must not invent information.

For example, it must not claim:

* an order was shipped unless get_shipment shows that
* a refund was issued unless create_refund succeeds
* a policy allows something unless relevant policy information was retrieved

The final answer should clearly distinguish:

* observed facts
* relevant policy
* recommended action
* action actually executed

## Structured Decisions

Use Pydantic structured output for important LLM decisions.

For example, create models similar to:

SupportIntent

* intent
* customer_id
* order_id
* explanation

ProposedAction

* action
* reason
* amount
* confidence
* requires_approval

Do not rely on parsing arbitrary LLM text.

## Human Approval

Refunds greater than $100 must require human approval.

Use LangGraph interrupt/checkpoint functionality.

When approval is required, the graph should stop and persist its state.

Expose an API that allows a human to:

* approve
* reject

After approval or rejection, resume the same LangGraph execution.

The workflow should survive an application restart when using PostgreSQL persistence.

## API Endpoints

Implement endpoints approximately like:

POST /support/requests

Example:

{
"customer_id": 123,
"message": "My order 456 hasn't arrived and I want a refund."
}

The endpoint should start the LangGraph workflow.

Return:

* request/thread ID
* current status
* agent response if completed
* approval request if paused

### GET /support/requests/{thread_id}

Return the current workflow state/status.

### POST /support/requests/{thread_id}/approve

Approve a pending action and resume the LangGraph execution.

### POST /support/requests/{thread_id}/reject

Reject a pending action and resume the workflow.

### GET /orders/{order_id}

Useful for testing/debugging the system.

### GET /customers/{customer_id}

Useful for testing/debugging.

## Safety and Business Validation

Never trust the LLM as the final authority for business-critical rules.

Before executing a refund or cancellation, run deterministic validation.

Examples:

* verify the order exists
* verify ownership
* check that a duplicate refund does not exist
* check whether the order can actually be cancelled
* validate refund amount
* verify approval exists when required

The LLM proposes actions.

Application code decides whether those actions are permitted.

## Failure Handling

Handle failures properly.

Examples:

* customer not found
* order not found
* order belongs to another customer
* shipment data unavailable
* policy retrieval fails
* OpenAI API timeout
* database failure
* duplicate refund
* attempted cancellation of shipped order

Tool errors should be represented clearly so the agent can react appropriately.

Do not expose stack traces to API consumers.

Use appropriate HTTP responses.

## Idempotency

Pay particular attention to write operations.

create_refund must not issue two refunds if:

* the agent retries a tool
* the API request is retried
* the workflow resumes after a crash
* the LLM accidentally requests the tool twice

Enforce this at both application and database levels where appropriate.

## Observability

Add structured logging.

Log:

* thread ID
* graph node
* tool name
* tool execution result/status
* execution duration
* errors

Do not log secrets or full sensitive customer information.

Design the project so LangSmith tracing can easily be enabled through environment variables, but do not make the application depend on LangSmith to run.

## Tests

Write meaningful pytest tests.

Include unit and integration tests covering at least:

1. Tracking an existing shipment.
2. Cancelling an order that has not shipped.
3. Preventing cancellation after shipment.
4. Refunding an eligible low-value order automatically.
5. Requiring approval for a refund greater than $100.
6. Resuming the graph after approval.
7. Rejecting a proposed refund.
8. Preventing duplicate refunds.
9. Handling an unknown customer.
10. Handling an unknown order.
11. Ensuring an order belongs to the specified customer.
12. Retrieving the correct company policy.
13. Handling tool failures.
14. Ensuring write operations cannot bypass deterministic validation.

Mock OpenAI calls in normal unit tests.

Keep a small optional set of integration/evaluation tests that can use a real OpenAI API key.

## Project Structure

Use a clean structure similar to:

app/
main.py

api/
routes/

agent/
graph.py
state.py
nodes.py
prompts.py
schemas.py

tools/
customer_tools.py
order_tools.py
shipment_tools.py
refund_tools.py
policy_tools.py

db/
models/
repositories/
session.py

services/
refund_service.py
order_service.py

retrieval/
embeddings.py
policy_store.py

core/
config.py
logging.py

docs/

migrations/

scripts/
seed_database.py
ingest_policies.py

tests/

docker-compose.yml

pyproject.toml

README.md

This is a suggested structure; improve it if there is a good reason, but keep clear separation between LangGraph orchestration, tools, domain/business logic, and persistence.

## Configuration

Use environment variables for:

* OPENAI_API_KEY
* DATABASE_URL
* OPENAI_MODEL
* EMBEDDING_MODEL
* LANGSMITH configuration if enabled

Provide:

.env.example

Never hardcode secrets.

## Local Development

Provide Docker Compose for PostgreSQL with pgvector enabled.

The intended local workflow should be approximately:

docker compose up -d

alembic upgrade head

python scripts/seed_database.py

python scripts/ingest_policies.py

uvicorn app.main:app --reload

Document everything in README.md.

## Implementation Principles

Follow these principles throughout the project:

1. Use the LLM for interpretation and reasoning, not for deterministic business logic.
2. Give the agent tools instead of placing all database information directly into its prompt.
3. Keep tool interfaces small and strongly typed.
4. Use Pydantic structured outputs.
5. Persist LangGraph state.
6. Make write operations idempotent.
7. Require human approval for sensitive actions.
8. Keep domain logic outside LangGraph nodes where possible.
9. Make the system testable without calling OpenAI for every test.
10. Prefer simple, readable production-style code over unnecessary abstractions.

## Initial Scope

Do not implement:

* frontend/UI
* authentication
* MCP
* multi-agent architecture
* Kubernetes
* cloud deployment
* payment gateway integration
* actual email sending

Build the backend and single LangGraph support agent first.

Once the basic system is complete, ensure that the README explains:

* architecture
* LangGraph flow
* where LLM reasoning is used
* where deterministic validation is used
* how tool calls work
* how RAG works
* how human approval works
* how checkpoint/resume works
* how idempotency is enforced
* how to run and test everything locally
