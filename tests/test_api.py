from fastapi.testclient import TestClient

from order_resolver.main import app

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
