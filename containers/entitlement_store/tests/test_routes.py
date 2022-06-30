import json
import pytest

import main


def test_get_entitlements(client_fixture, monkeypatch):
    test_req = {
                "primary_entity_id": "31c871f2-6d2a-4d27-b727-e619cfaf4e7a",
                "secondary_entity_ids": ["46a871f2-6d2a-4d27-b727-e619cfaf4e7b"],
            }
    test_data = {
                        "entity_identifier": "cliententityid-14443434-1111343434-asdfdffff",
                        "entity_attributes": [
                            {
                                "attribute": "https://example.com/attr/Classification/value/S",
                                "displayName": "classification"
                            },
                            {
                                "attribute": "https://example.com/attr/COI/value/PRX",
                                "displayName": "category of intent"
                            }
                        ]
                    }

    async def mock_get_entitlements_for_entity_id(entityId: str):
        return test_data

    monkeypatch.setattr(main, "get_entitlements_for_entity_id", mock_get_entitlements_for_entity_id)

    response = client_fixture.post("/entitle", data=json.dumps(test_req))
    assert response.status_code == 200
    assert response.json()[0] == test_data
    assert len(response.json()[0]) == 2
