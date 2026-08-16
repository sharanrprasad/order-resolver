from fastapi.testclient import TestClient

from order_resolver.main import app, create_app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_support_endpoint_is_scaffolded() -> None:
    response = client.post(
        "/support/requests",
        json={
            "customer_id": "00000000-0000-0000-0000-000000000001",
            "message": "Where is my order?",
        },
    )
    assert response.status_code == 501


def test_create_app_preserves_injected_dependencies() -> None:
    dependencies = app.state.dependencies

    test_app = create_app(dependencies)

    assert test_app.state.dependencies is dependencies
