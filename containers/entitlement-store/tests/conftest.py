import pytest
from fastapi.testclient import TestClient

from ..main import app

@pytest.fixture(scope="module")
def client_fixture():
    client = TestClient(app)
    yield client  # testing happens here
