import json
import pytest

from .. import main

def test_add_entitlements_to_entity(test_app, monkeypatch):
    test_payload = [
      "https://opentdf.io/attr/IntellectualProperty/value/TradeSecret1",
      "https://opentdf.io/attr/IntellectualProperty/value/TradeSecret2"
    ]

    test_response = [
      "https://opentdf.io/attr/IntellectualProperty/value/TradeSecret1",
      "https://opentdf.io/attr/IntellectualProperty/value/TradeSecret2"
    ]

    async def mock_add_entitlements_to_entity_crud(entityId, request):
        return test_response

    monkeypatch.setattr(main, "add_entitlements_to_entity_crud", mock_add_entitlements_to_entity_crud)

    response = test_app.post("/entitlements/tdf_client", data=json.dumps(test_payload))
    assert response.status_code == 200
    assert response.json() == test_response

def test_remove_entitlement_from_entity(test_app, monkeypatch):
    test_payload = [
        "https://opentdf.io/attr/IntellectualProperty/value/TradeSecret1",
        "https://opentdf.io/attr/IntellectualProperty/value/TradeSecret2"
    ]


    async def mock_remove_entitlement_from_entity_crud(entityId, request):
        return {}

    monkeypatch.setattr(main, "remove_entitlement_from_entity_crud", mock_remove_entitlement_from_entity_crud)

    response = test_app.delete("/entitlements/tdf_client", data=json.dumps(test_payload))
    assert response.status_code == 202
    assert response.json() == {}