import json
import pytest

from .. import main


def test_get_entitlements(client_fixture, monkeypatch):
    test_req = {
                "algorithm": "ec:secp256r1",
                "clientPublicSigningKey": "-----BEGIN PUBLIC KEY-----\n" +
                             "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2Q9axUqaxEfhOO2+0Xw+\n" +
                             "swa5Rb2RV0xeTX3GC9DeORv9Ip49oNy+RXvaMsdNKspPWYZZEswrz2+ftwcQOSU+\n" +
                             "efRCbGIwbSl8QBfKV9nGLlVmpDydcAIajc7YvWjQnDTEpHcJdo9y7/oogG7YcEmq\n" +
                             "S3NtVJXCmbc4DyrZpc2BmZD4y9417fSiNjTTYY3Fc19lQz07hxDQLgMT21N4N0Fz\n" +
                             "mD6EkiEpG5sdpDT/NIuGjFnJEPfqIs6TnPaX2y1OZ2/JzC+mldJFZuEqJZ/6qq/e\n" +
                             "Ylp04nWrSnXhPpTuxNZ5J0GcPbpcFgdT8173qmm5m5jAjiFCr735lH7USl15H2fW\n" +
                             "TwIDAQAB\n" +
                             "-----END PUBLIC KEY-----\n",
                "primaryEntityId": "31c871f2-6d2a-4d27-b727-e619cfaf4e7a",
                "secondaryEntityIds": ["46a871f2-6d2a-4d27-b727-e619cfaf4e7b"],
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
    assert response.json()['entitlements'][0] == test_data
    assert len(response.json()['entitlements']) == 2
