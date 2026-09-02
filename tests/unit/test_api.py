from fastapi.testclient import TestClient

from order_resolver.main import app, create_app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# End-to-end behaviour of POST /support/requests (graph execution, refund /
# cancellation writes, human-approval interrupts) is covered by the integration
# suite under tests/integration, which runs the app against a real database.


def test_create_app_preserves_injected_dependencies() -> None:
    dependencies = app.state.dependencies

    test_app = create_app(dependencies)

    assert test_app.state.dependencies is dependencies
