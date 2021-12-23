import json
import pytest

from .. import main

#Test Authorities
def test_read_authority_namespace(test_app, monkeypatch):
    test_data = [
        "https://opentdf1.io",
        "https://opentdf2.io"
    ]

    async def mock_read_authorities_crud():
        return test_data

    monkeypatch.setattr(main, "read_authorities_crud", mock_read_authorities_crud)

    response = test_app.get("/authorities")
    assert response.status_code == 200
    assert response.json() == test_data

