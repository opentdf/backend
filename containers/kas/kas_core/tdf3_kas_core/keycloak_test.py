"""Test the Keycloak module."""
import os
import pytest
import json

from unittest.mock import patch

from tdf3_kas_core.errors import KeyNotFoundError

import tdf3_kas_core.keycloak as keycloak

KEYCLOAK_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAian19orjts+wol1BxEXo5hx7OsfqKT2soU+3COG6/WSnphqBI2RRRvI07q0+LGGq9wRpDYPRu01RG0JIIqP3VptLOVmzDH8n6ckctvxPuYDlp1NqjAKOSlxhfaAwpCLOllGn+XkpMBUHduaPRb0fl5vaxWleNT11s9FrYTMJEAJcrf56YoWeQUnp5bBSPQcNlz+UjKuppoTeSl8sxtxT5iF3lYfwq3IL5UHrupm19WNOfw+1GdCgX30hppX0TRxDTpOu99kzL4tzbfOSuG+o2IgYe9Or9GKWkP5Fg2kAYyD/bu6IGAbq3O7VOARL0/t0zm8LxS+sYFMSIndFt82X9wIDAQAB
-----END PUBLIC KEY-----"""

fakeDecodedToken = """
{
  "exp": 1623693824,
  "iat": 1623693524,
  "jti": "cb0765ea-80a6-4056-9f55-1a41e644c87a",
  "iss": "http://localhost:8080/auth/realms/tdf",
  "aud": "account",
  "sub": "8e6de020-3617-436e-a497-feded4c64f10",
  "typ": "Bearer",
  "azp": "tdf-client",
  "session_state": "423b06ff-fc8d-4f9f-8266-57b07ce340dd",
  "acr": "1",
  "allowed-origins": [
    "http://keycloak-http"
  ],
  "realm_access": {
    "roles": [
      "default-roles-tdf",
      "offline_access",
      "uma_authorization"
    ]
  },
  "resource_access": {
    "account": {
      "roles": [
        "manage-account",
        "manage-account-links",
        "view-profile"
      ]
    }
  },
  "scope": "profile email",
  "email_verified": false,
  "preferred_username": "user1"
}
"""


class FakeKeyMaster:
    def __init__(self, private_key) -> None:
        self._private_key = private_key

    def set_key_pem(self, key_name, key_type, pem_key):
        """Set a key directly with a PEM encoded string."""

    def private_key(self, name):
        if name == "KAS-PRIVATE":
            return self._private_key
        raise KeyNotFoundError(f"Unknown test key: {name}")

    def public_key(self, name):
        if name == "KEYCLOAK-PUBLIC-tdf":
            return KEYCLOAK_PUBLIC_KEY
        raise KeyNotFoundError(f"Unknown test key: {name}")


@pytest.fixture
def key_master(private_key):
    return FakeKeyMaster(private_key)


class MockResponse:
    def __init__(self, json_data, status_code):
        self.fakejson = json_data
        self.status_code = status_code
        self.ok = status_code < 399

    def json(self):
        return self.fakejson


def mocked_requests_get(*args, **kwargs):
    fakeKeycloakPKResp = json.loads(
        '{"realm":"tdf","public_key":"MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAj/QUmaMS/4ANsz3OKRH8vU8Dw+iyVEnvgkA1Z6a9twaZglQUDegOVZwqSImI6UNsESmJMcU1l0zHNsxM/C9d+ttuZOIdnWDtQL6IrX5FBMXA+AFAIAf/SpCDZEkrjVjfhn5fH76dI7lETZrMtWpS3O0fXId63yKaOe4+HddSZ+l7J2meAuHqpBkTC60MOmFiwgCJ11xFIEKEUne10smBBtsND5uB75oceZSF/gNdEltk2u7AQLzToL50Jcnp9CV1fOQ8bbe0J2NwKyaYUX2/qBKhGOB1k0y/eHFsJ2ceQEfWzLr1z/cuH208/TAxAq2QjggokIRIm2DpnwcntSFpkQIDAQAB","token-service":"http://keycloak-http:80/auth/realms/tdf/protocol/openid-connect","account-service":"http://keycloak-http:80/auth/realms/tdf/account","tokens-not-before":0}'
    )
    if "/auth/realms/" in args[0]:
        return MockResponse(fakeKeycloakPKResp, 200)

    return MockResponse(None, 404)


def mocked_requests_get_fails(*args, **kwargs):
    return MockResponse(None, 500)


@patch("requests.Session.get", side_effect=mocked_requests_get)
def test_get_keycloak_public_key_succeeds_with_required_env(mock_get):
    """Tests that fetching KC pubkey will invoke an http get pubkey."""
    pubkey = keycloak.get_keycloak_public_key("https://mykc.com", "tdf")
    assert mock_get.called == True
    assert pubkey


@patch("requests.Session.get", side_effect=mocked_requests_get)
def test_try_extract_realm_returns_realmkey(mock_get):
    token = json.loads(fakeDecodedToken)
    realmKey = keycloak.try_extract_realm(token)
    assert realmKey == "tdf"


@patch("requests.Session.get", side_effect=mocked_requests_get)
def test_load_realm_key_prefers_cached_key(mock_get, key_master):
    realm = "tdf"
    realmKey = keycloak.load_realm_key("https://mykc.com", realm, key_master)
    assert mock_get.called == False
    assert realmKey


@patch("requests.Session.get", side_effect=mocked_requests_get)
def test_load_realm_key_fetches_uncached_key(mock_get, key_master):
    realm = "someRealm"
    realmKey = keycloak.load_realm_key("https://mykc.com", realm, key_master)
    assert mock_get.called == True
    assert realmKey


@patch("requests.Session.get", side_effect=mocked_requests_get_fails)
def test_uncached_key_fetch_fails_returns_falsy_empty(mock_get, key_master):
    realm = "someRealm"
    realmKey = ""
    realmKey = keycloak.load_realm_key("https://mykc.com", realm, key_master)
    assert mock_get.called == True
    assert not realmKey
