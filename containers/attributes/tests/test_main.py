from .. import main
from fastapi.testclient import TestClient

client = TestClient(main.app)


def test_read_semver():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "attributes"}


def test_get_retryable_request():
    http = main.get_retryable_request()
    assert http is not None
