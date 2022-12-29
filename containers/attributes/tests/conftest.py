import pytest
from fastapi.testclient import TestClient

from ..main import app, get_auth


def get_override_token():
    # return sample auth token
    return {
            "exp": 1672299147,
            "iat": 1672298847,
            "jti": "9828fcd9-8214-4c92-99be-6e5e6d3fae68",
            "iss": "http://localhost:65432/auth/realms/tdf",
            "aud": [
                "tdf-entitlement",
                "tdf-attributes",
                "realm-management",
                "account"
            ],
            "sub": "0e56dae3-70bf-4f2a-a919-a58e7807ef53",
            "typ": "Bearer",
            "azp": "tdf-client",
            "session_state": "ea78a1d0-5c04-416f-b842-a69c2f2471cd",
            "acr": "1",
            "allowed-origins": [
                "http://localhost:65432"
            ],
            "realm_access": {
                "roles": [
                "default-roles-tdf",
                "offline_access",
                "uma_authorization"
                ]
            },
            "resource_access": {
                "realm-management": {
                "roles": [
                    "view-users",
                    "view-clients",
                    "query-clients",
                    "query-groups",
                    "query-users"
                ]
                },
                "account": {
                "roles": [
                    "manage-account",
                    "manage-account-links",
                    "view-profile"
                ]
                }
            },
            "scope": "email profile",
            "sid": "110ba3de-eec3-4415-a6cf-0e3b05833ed7",
            "email_verified": False,
            "preferred_username": "user1"
            }


@pytest.fixture(scope="module")
def test_app():
    app.dependency_overrides[get_auth] = get_override_token
    client = TestClient(app)
    yield client  # testing happens here
