import pytest
import json

from tdf3_kas_core.models import Context

from .audit_hooks import (
    extract_policy_data_from_tdf3,
    extract_policy_data_from_nano,
    extract_info_from_auth_token,
)

BASE_AUDIT_LOG = {
    "id": "TEST_UUID",
    "transactionId": "TEST_UUID",
    "transactionTimestamp": "NOW_DATETIME",
    "tdf_id": "",
    "tdfName": None,
    "ownerId": "",
    "ownerOrganizationId": None,
    "transactionType": "testint",
    "eventType": "testint",
    "tdfAttributes": {"dissem": [], "attrs": []},
    "actorAttributes": {"npe": True, "actorId": "", "attrs": []},
}

KEYCLOAK_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJaUEx4SFBLN1RVNnYtNFlzNE9SVlp3c3Y1bTNScEJmSGpOX1luZDVGUmVVIn0.eyJleHAiOjE2NzUxODI0OTcsImlhdCI6MTY3NTE4MjE5NywianRpIjoiZTI5NjYxZjctNzliZS00NmVhLWE0MTQtZmM1NmM1ZDk2YjI1IiwiaXNzIjoiaHR0cDovL2xvY2FsaG9zdDo2NTQzMi9hdXRoL3JlYWxtcy90ZGYiLCJhdWQiOlsidGRmLWF0dHJpYnV0ZXMiLCJhY2NvdW50Il0sInN1YiI6IjNjYmE4ZDg2LTE2NTQtNDE5Zi04ZTY4LTE3ODhlN2Q2OWZhMyIsInR5cCI6IkJlYXJlciIsImF6cCI6InRkZi1jbGllbnQiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHA6Ly9rZXljbG9hay1odHRwIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJkZWZhdWx0LXJvbGVzLXRkZiIsIm9mZmxpbmVfYWNjZXNzIiwidW1hX2F1dGhvcml6YXRpb24iXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6ImVtYWlsIHByb2ZpbGUiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsImNsaWVudElkIjoidGRmLWNsaWVudCIsImNsaWVudEhvc3QiOiIxMjcuMC4wLjEiLCJ0ZGZfY2xhaW1zIjp7ImVudGl0bGVtZW50cyI6W3siZW50aXR5X2lkZW50aWZpZXIiOiJkYjFkZDA1OS00MjEwLTQ5ZWUtOTJkOS0xYjg1Y2Y3NGQzNTAiLCJlbnRpdHlfYXR0cmlidXRlcyI6W3siYXR0cmlidXRlIjoiaHR0cHM6Ly9leGFtcGxlLmNvbS9hdHRyL0NsYXNzaWZpY2F0aW9uL3ZhbHVlL1MiLCJkaXNwbGF5TmFtZSI6IkNsYXNzaWZpY2F0aW9uIn0seyJhdHRyaWJ1dGUiOiJodHRwczovL2V4YW1wbGUuY29tL2F0dHIvQ09JL3ZhbHVlL1BSWCIsImRpc3BsYXlOYW1lIjoiQ09JIn0seyJhdHRyaWJ1dGUiOiJodHRwczovL2V4YW1wbGUuY29tL2F0dHIvRW52L3ZhbHVlL0NsZWFuUm9vbSIsImRpc3BsYXlOYW1lIjoiRW52In1dfV0sImNsaWVudF9wdWJsaWNfc2lnbmluZ19rZXkiOiItLS0tLUJFR0lOIFBVQkxJQyBLRVktLS0tLVxuTUZrd0V3WUhLb1pJemowQ0FRWUlLb1pJemowREFRY0RRZ0FFK3N6QWREYmZYUFh3Y0M2M1NwS1JIUzcwRnpjWVxud0NLUFNKSytLY1NyMDQzek03M3FqRXpPUTFuUjc5aHRBOW5tU3VqMHdoZnpjNituVFJWM2NHSERSQT09XG4tLS0tLUVORCBQVUJMSUMgS0VZLS0tLS1cbiJ9LCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJzZXJ2aWNlLWFjY291bnQtdGRmLWNsaWVudCIsImNsaWVudEFkZHJlc3MiOiIxMjcuMC4wLjEifQ.qUWvcBT27ENkx1MImiC21c9X5hKW5HiGdzQux3TCOaLNLQHlxZJYu4Eov0sBxQv68ocCbsooNZRemw598HMJwkVJQ12nSiODe7bQQZNU-Wa-X8SbaPaDLs5bIb-yKu1CCpnHyj09SCL0NgfqlwgjiWqbTJbuN4nt8AjCAMqrGz9m2OvNESWf_zl0iw8lSkj3i8KTSldWod9IKU4eexxPzIrp5NXu_apRYMb864_SbDtnqGkLXEeOlAGUW_uoK080xQUkH2F84x04YF4H0zMaxLlCnqZMZw0uXfTCnd4Rp0Rl7lyx95OR7SXh9cgF1T6UmdBM3F2-_AK4YsJlSzzpaQ"

TEST_REQUEST_BODY = {
    "policy": "eyJib2R5Ijp7ImRhdGFBdHRyaWJ1dGVzIjpbeyJhdHRyaWJ1dGUiOiJodHRwczovL2V4YW1wbGUuY29tL2F0dHIvQ2xhc3NpZmljYXRpb24vdmFsdWUvVFMiLCJkaXNwbGF5TmFtZSI6IiIsImthc1VybCI6Imh0dHA6Ly9sb2NhbGhvc3Q6NjU0MzIvYXBpL2thcyIsInB1YktleSI6IiJ9XSwiZGlzc2VtIjpbXX0sInV1aWQiOiJhNDZkZDE2My02MDM5LTRlZjMtOWJkMy0wZWJiM2Y0MDM5NTQifQ==",
}


def test_extract_policy_data_from_tdf():
    new_audit_log = extract_policy_data_from_tdf3(BASE_AUDIT_LOG, TEST_REQUEST_BODY)

    assert new_audit_log["tdfId"] == "a46dd163-6039-4ef3-9bd3-0ebb3f403954"
    assert new_audit_log["tdfAttributes"]["dissem"] == []
    assert new_audit_log["tdfAttributes"]["attrs"] == [
            "https://example.com/attr/Classification/value/TS"
        ]


def test_extract_info_from_auth_token():
    context = Context()
    context.add("Authorization", f"Bearer {KEYCLOAK_TOKEN}")
    new_audit_log = extract_info_from_auth_token(BASE_AUDIT_LOG, context)

    assert new_audit_log["ownerId"] == "3cba8d86-1654-419f-8e68-1788e7d69fa3"

    assert new_audit_log["actorAttributes"]["npe"] == True
    assert new_audit_log["actorAttributes"]["actorId"] == "tdf-client"
    assert set(new_audit_log["actorAttributes"]["attrs"]) == set(
        [
            "https://example.com/attr/Env/value/CleanRoom",
            "https://example.com/attr/COI/value/PRX",
            "https://example.com/attr/Classification/value/S",
        ]
    )
