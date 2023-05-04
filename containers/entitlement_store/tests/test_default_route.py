from fastapi.testclient import TestClient
from ..main import app


def test_default_route(client_fixture):
    response = client_fixture.get("/")
    assert response.status_code == 200
