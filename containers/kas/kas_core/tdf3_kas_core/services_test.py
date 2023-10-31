import pytest  # noqa: F401

import datetime
import os
import json
import jwt

import tdf3_kas_core
from tdf3_kas_core.abstractions import AbstractRewrapPlugin

from tdf3_kas_core.models import Context
from tdf3_kas_core.models import KeyMaster

from tdf3_kas_core.services import *
from tdf3_kas_core import services


@pytest.fixture
def with_idp():
    old_value = flags["idp"]
    flags["idp"] = True
    yield
    flags["idp"] = old_value


@pytest.fixture
def without_idp():
    old_value = flags["idp"]
    flags["idp"] = False
    yield
    flags["idp"] = old_value


@pytest.fixture
def client_public_key(entity_public_key):
    return entity_public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")


@pytest.fixture
def tdf_claims(client_public_key):
    return {
        "tdf_claims": {
            "client_public_signing_key": client_public_key,
            "entitlements": [
                {
                    "entity_identifier": "clientsubjectId1-14443434-1111343434-asdfdffff",
                    "entity_attributes": [
                        {
                            "attribute": "https://example.com/attr/Classification/value/S",
                            "displayName": "classification",
                        },
                        {
                            "attribute": "https://example.com/attr/COI/value/PRX",
                            "displayName": "category of intent",
                        },
                    ],
                },
                {
                    "entity_identifier": "user@virtru.com",
                    "entity_attributes": [
                        {
                            "attribute": "https://example.com/attr/Classification/value/S",
                            "displayName": "classification",
                        },
                        {
                            "attribute": "https://example.com/attr/COI/value/PRX",
                            "displayName": "category of intent",
                        },
                    ],
                },
            ],
        }
    }


@pytest.fixture
def jwt_claims(tdf_claims):
    return {
        "iss": "https://localhost/tdf",
        "sub": "user@virtru.com",
        "tdf_claims": tdf_claims["tdf_claims"],
        "tdf_spec_version": "4.0.0",
    }


@pytest.fixture
def jwt_with_distributed_claims(private_key):
    claims = {
        "iss": "https://localhost/tdf",
        "sub": "user@virtru.com",
        "_claim_names": {
            "tdf_spec_version": "a",
            "tdf_claims": "a",
        },
        "_claim_sources": {
            "a": {
                "endpoint": "https://nowhere.invalid/claims_here",
                "access_token": "ksj3n283dke",
            },
        },
    }
    return jwt.encode(
        claims,
        private_key,
        algorithm="RS256",
    )


@pytest.fixture
def jwt_expired(jwt_claims, private_key):
    now = datetime.datetime.now()
    delta = datetime.timedelta(seconds=60)
    jwt_claims["exp"] = (now - delta).timestamp()
    return jwt.encode(
        jwt_claims,
        private_key,
        algorithm="RS256",
    )


@pytest.fixture
def jwt_standard(jwt_claims, private_key):
    return jwt.encode(
        jwt_claims,
        private_key,
        algorithm="RS256",
    )


class MockAuthPlugin(AbstractRewrapPlugin):
    def fetch_attributes(self, namespaces):
        return [
            {
                "authority": "https://example.com",
                "name": "Classification",
                "rule": "hierarchy",
                "state": "published",
                "order": [
                    "TS",
                    "S",
                    "FOUO",
                    "OS",
                ],
            },
            {
                "authority": "https://example.com",
                "name": "COI",
                "rule": "allOf",
                "order": [
                    "PRA",
                    "PRB",
                    "PRC",
                    "PRD",
                    "PRF",
                    "PRX",
                ],
            },
        ]


@pytest.fixture
def rewrap_plugins():
    return (
        tdf3_kas_core.models.plugin_runner.rewrap_plugin_runner_v2.RewrapPluginRunnerV2(
            [MockAuthPlugin()]
        )
    )


@pytest.fixture
def upsert_plugins():
    return (
        tdf3_kas_core.models.plugin_runner.upsert_plugin_runner_v2.UpsertPluginRunnerV2()
    )


class FakeKeyMaster:
    def __init__(self, public_key, private_key) -> None:
        self._private_key = private_key
        self._public_key = public_key

    def private_key(self, name):
        if name == "KAS-PRIVATE":
            return self._private_key
        raise KeyNotFoundError(f"Unknown test key: {name}")

    def public_key(self, name):
        if name == "KEYCLOAK-PUBLIC-tdf":
            return self._public_key
        raise KeyNotFoundError(f"Unknown test key: {name}")


@pytest.fixture
def key_master(public_key, private_key):
    return FakeKeyMaster(public_key, private_key)


def test_kas_public_rsa_key(public_key_path):
    """Test the getter for the KAS public key."""
    km = KeyMaster()
    km.set_key_path("KAS-PUBLIC", "PUBLIC", public_key_path)
    expected = km.get_export_string("KAS-PUBLIC")
    actual = kas_public_key(km, "rsa:2048")
    assert actual == expected


def test_kas_ec_cert(ec_cert):
    """Test the getter for the KAS public key."""
    km = KeyMaster()
    km.set_key_pem("KAS-EC-SECP256R1-PUBLIC", "PUBLIC", ec_cert)
    expected = km.get_export_string("KAS-EC-SECP256R1-PUBLIC")
    actual = kas_public_key(km, "ec:secp256r1")
    assert actual == expected


def test_kas_public_key_v2_rsa(public_key):
    """Test the getter for the KAS public key."""
    km = KeyMaster()
    km.set_key_pem("KAS-PUBLIC", "PUBLIC", public_key)
    expected = {
        "kid": "nxO623BNDCXfI+t/OGwCTcZ70vwJcuyYyniKQxmrbEQ=",
        "publicKey": km.get_export_string("KAS-PUBLIC"),
    }
    actual = kas_public_key(km, algorithm="rsa:2048", fmt="pkcs8", version="2")
    assert actual == expected


def test_kas_public_key_v2_ec(ec_cert):
    """Test the getter for the KAS public key."""
    km = KeyMaster()
    km.set_key_pem("KAS-EC-SECP256R1-PUBLIC", "PUBLIC", ec_cert)
    expected = {
        "kid": "NQWzlLx8oNFRTxkkvKAXDiEwHtDlRmhQE2AMC7xa7i0=",
        "publicKey": km.get_export_string("KAS-EC-SECP256R1-PUBLIC"),
    }
    actual = kas_public_key(km, algorithm="ec:secp256r1", fmt="pkcs8", version="2")
    assert actual == expected


def test_ping():
    """Test the health ping."""
    expected = {"version": "1.2.3"}
    actual = ping("1.2.3")
    assert actual == expected


def test_rewrap_v2(
    with_idp,
    key_access_wrapped_raw,
    rewrap_plugins,
    faux_policy_bytes,
    key_master,
    entity_private_key,
    client_public_key,
    jwt_standard,
):
    """Test the rewrap_v2 service."""
    os.environ["OIDC_SERVER_URL"] = "https://keycloak.dev"
    data = {
        "requestBody": json.dumps(
            {
                "keyAccess": key_access_wrapped_raw,
                "policy": bytes.decode(faux_policy_bytes),
                "clientPublicKey": client_public_key,
                "algorithm": None,
            }
        )
    }
    signedToken = jwt.encode(data, entity_private_key, "RS256")
    request_data = {"signedRequestToken": signedToken}

    context = Context()
    context.add("Authorization", f"Bearer {jwt_standard}")
    rewrap_v2(request_data, context, rewrap_plugins, key_master)
    assert True


def test_rewrap_distributed_claims(
    with_idp,
    key_access_wrapped_raw,
    rewrap_plugins,
    faux_policy_bytes,
    key_master,
    entity_private_key,
    client_public_key,
    jwt_with_distributed_claims,
    mock_response,
    tdf_claims,
):
    mock_response(v=tdf_claims)
    """Test the rewrap_v2 service."""
    os.environ["OIDC_SERVER_URL"] = "https://keycloak.dev"
    data = {
        "requestBody": json.dumps(
            {
                "keyAccess": key_access_wrapped_raw,
                "policy": bytes.decode(faux_policy_bytes),
                "clientPublicKey": client_public_key,
                "algorithm": None,
            }
        )
    }
    signedToken = jwt.encode(data, entity_private_key, "RS256")
    request_data = {"signedRequestToken": signedToken}

    context = Context()
    context.add("Authorization", f"Bearer {jwt_with_distributed_claims}")
    rewrap_v2(
        request_data,
        context,
        rewrap_plugins,
        key_master,
        ["https://nowhere.invalid/claims_here"],
    )
    assert True


def test_rewrap_v2_expired_token(
    with_idp,
    faux_policy_bytes,
    key_master,
    client_public_key,
    entity_private_key,
    jwt_expired,
    rewrap_plugins,
):
    key_access = {"type": "remote", "url": "http://127.0.0.1:4000", "protocol": "kas"}
    data = {
        "requestBody": json.dumps(
            {
                "keyAccess": key_access,
                "policy": bytes.decode(faux_policy_bytes),
                "clientPublicKey": client_public_key,
                "algorithm": None,
            }
        )
    }
    context = Context()
    context.add("Authorization", f"Bearer {jwt_expired}")

    signedToken = jwt.encode(data, entity_private_key, "RS256")
    request_data = {"signedRequestToken": signedToken}

    # This token is expired, should fail.
    # Actual exception is:  jwt.exceptions.ExpiredSignatureError
    with pytest.raises(tdf3_kas_core.errors.UnauthorizedError):
        rewrap_v2(request_data, context, rewrap_plugins, key_master)
    assert True


def test_rewrap_v2_no_auth_header(
    with_idp,
    faux_policy_bytes,
    key_master,
    client_public_key,
    entity_private_key,
    rewrap_plugins,
):
    key_access = {"type": "remote", "url": "http://127.0.0.1:4000", "protocol": "kas"}
    data = {
        "requestBody": json.dumps(
            {
                "keyAccess": key_access,
                "policy": bytes.decode(faux_policy_bytes),
                "clientPublicKey": client_public_key,
                "algorithm": "rsa:2048",
            }
        )
    }
    signedToken = jwt.encode(data, entity_private_key, "RS256")
    request_data = {"signedRequestToken": signedToken}

    context = Context()
    # Skip context.add("Authorization", ...)
    # This token is expired, should fail.
    # Actual exception is:  jwt.exceptions.ExpiredSignatureError
    with pytest.raises(tdf3_kas_core.errors.UnauthorizedError):
        rewrap_v2(request_data, context, rewrap_plugins, key_master)
    assert True


def test_rewrap_v2_invalid_auth_header(
    with_idp,
    faux_policy_bytes,
    key_master,
    client_public_key,
    entity_private_key,
    jwt_standard,
    rewrap_plugins,
):
    key_access = {"type": "remote", "url": "http://127.0.0.1:4000", "protocol": "kas"}

    data = {
        "requestBody": json.dumps(
            {
                "keyAccess": key_access,
                "policy": bytes.decode(faux_policy_bytes),
                "clientPublicKey": client_public_key,
                "algorithm": "rsa:2048",
            }
        )
    }
    signedToken = jwt.encode(data, entity_private_key, "RS256")
    request_data = {"signedRequestToken": signedToken}

    context = Context()
    context.add("Authorization", f"Chair-er Token:{jwt_standard}")
    # This token is expired, should fail.
    # Actual exception is:  jwt.exceptions.ExpiredSignatureError
    with pytest.raises(tdf3_kas_core.errors.UnauthorizedError):
        rewrap_v2(request_data, context, rewrap_plugins, key_master)
    assert True


def test_rewrap_v2_invalid_auth_jwt(
    with_idp,
    faux_policy_bytes,
    key_master,
    client_public_key,
    entity_private_key,
    rewrap_plugins,
):
    key_access = {"type": "remote", "url": "http://127.0.0.1:4000", "protocol": "kas"}
    data = {
        "requestBody": json.dumps(
            {
                "keyAccess": key_access,
                "policy": bytes.decode(faux_policy_bytes),
                "clientPublicKey": client_public_key,
                "algorithm": None,
            }
        )
    }

    context = Context()
    context.add("Authorization", "Bearer DO I LOOK LIKE A JWT TO YOU?")

    signedToken = jwt.encode(data, entity_private_key, "RS256")
    request_data = {"signedRequestToken": signedToken}

    # This token is expired, should fail.
    # Actual exception is:  jwt.exceptions.ExpiredSignatureError
    with pytest.raises(tdf3_kas_core.errors.UnauthorizedError):
        rewrap_v2(request_data, context, rewrap_plugins, key_master)
    assert True


def test_upsert_v2(
    key_access_wrapped_raw,
    faux_policy_bytes,
    key_master,
    client_public_key,
    entity_private_key,
    jwt_standard,
    upsert_plugins,
):
    """Test the upsert_v2 service."""
    data = {
        "requestBody": json.dumps(
            {
                "keyAccess": key_access_wrapped_raw,
                "policy": bytes.decode(faux_policy_bytes),
                "clientPublicKey": client_public_key,
                "algorithm": None,
            }
        )
    }

    signedToken = jwt.encode(data, entity_private_key, "RS256")
    request_data = {"signedRequestToken": signedToken}

    context = Context()
    context.add("Authorization", f"Bearer {jwt_standard}")
    upsert_v2(request_data, context, upsert_plugins, key_master, [])
    assert True


def test_upsert_v2_no_auth_header(
    key_access_wrapped_raw,
    faux_policy_bytes,
    with_idp,
    key_master,
    client_public_key,
    entity_private_key,
    upsert_plugins,
):
    """Test the upsert_v2 service."""

    data = {
        "requestBody": json.dumps(
            {
                "keyAccess": key_access_wrapped_raw,
                "policy": bytes.decode(faux_policy_bytes),
                "clientPublicKey": client_public_key,
                "algorithm": None,
            }
        )
    }

    signedToken = jwt.encode(data, entity_private_key, "RS256")
    request_data = {"signedRequestToken": signedToken}

    context = Context()
    # context.add("Authorization", "Bearer {0}".format(KEYCLOAK_ACCESS_TOKEN))
    with pytest.raises(tdf3_kas_core.errors.UnauthorizedError):
        upsert_v2(request_data, context, upsert_plugins, key_master, [])
    assert True


def test_upsert_v2_invalid_auth_header(
    with_idp,
    faux_policy_bytes,
    key_access_wrapped_raw,
    key_master,
    client_public_key,
    entity_private_key,
    jwt_standard,
    upsert_plugins,
):
    """Test the upsert_v2 service."""
    data = {
        "requestBody": json.dumps(
            {
                "keyAccess": key_access_wrapped_raw,
                "policy": bytes.decode(faux_policy_bytes),
                "clientPublicKey": client_public_key,
                "algorithm": None,
            }
        )
    }

    signedToken = jwt.encode(data, entity_private_key, "RS256")
    request_data = {"signedRequestToken": signedToken}

    context = Context()
    context.add("Authorization", f"Terr-or Token {jwt_standard}")
    with pytest.raises(tdf3_kas_core.errors.UnauthorizedError):
        upsert_v2(request_data, context, upsert_plugins, key_master, [])
    assert True


def test_upsert_v2_invalid_auth_jwt(
    with_idp,
    faux_policy_bytes,
    key_access_wrapped_raw,
    key_master,
    client_public_key,
    entity_private_key,
    upsert_plugins,
):
    """Test the upsert_v2 service."""
    data = {
        "requestBody": json.dumps(
            {
                "keyAccess": key_access_wrapped_raw,
                "policy": bytes.decode(faux_policy_bytes),
                "clientPublicKey": client_public_key,
                "algorithm": None,
            }
        )
    }

    signedToken = jwt.encode(data, entity_private_key, "RS256")
    request_data = {"signedRequestToken": signedToken}

    context = Context()
    context.add("Authorization", "Bearer DO I LOOK LIKE A JWT TO YOU?")
    with pytest.raises(tdf3_kas_core.errors.UnauthorizedError):
        upsert_v2(request_data, context, upsert_plugins, key_master, [])
    assert True


class MockResponse:
    def __init__(self, status_code=200, type="application/json", v=None):
        self.status_code = status_code
        self.headers = {"content-type": type}
        self.v = v
        if isinstance(v, str):
            self.text = v

    def json(self):
        return self.v


@pytest.fixture
def mock_response(monkeypatch):
    def with_value(**kwargs):
        response = MockResponse(**kwargs)

        def mock_get(*args, **kwargs):
            return response

        monkeypatch.setattr(requests, "get", mock_get)

    return with_value


def test_fetch_distributed_claims_valid_json(mock_response, tdf_claims):
    mock_response(v=tdf_claims)
    actual = services._fetch_distributed_claims(
        {"tdf_claims": "a"},
        {"a": {"endpoint": "https://b/"}},
        "tdf_claims",
        ["https://b/"],
    )
    assert "client_public_signing_key" in actual


def test_fetch_distributed_claims_valid_jwt(mock_response, jwt_standard):
    logger.warning(jwt_standard)
    mock_response(v=jwt_standard, type="application/jwt")
    with pytest.raises(tdf3_kas_core.errors.UnauthorizedError) as e:
        services._fetch_distributed_claims(
            {"tdf_claims": "a"},
            {"a": {"endpoint": "https://b/"}},
            "tdf_claims",
            ["https://b/"],
        )
    assert "not yet implemented" in e.value.message


def test_fetch_distributed_claims_404(mock_response):
    mock_response(status_code=404)
    with pytest.raises(tdf3_kas_core.errors.UnauthorizedError) as e:
        services._fetch_distributed_claims(
            {"a": "a"}, {"a": {"endpoint": "https://b/"}}, "a", ["https://b/"]
        )
    assert "404" in e.value.message


def test_fetch_distributed_claims_500(mock_response):
    mock_response(status_code=500)
    with pytest.raises(tdf3_kas_core.errors.UnauthorizedError) as e:
        services._fetch_distributed_claims(
            {"a": "a"}, {"a": {"endpoint": "https://b/"}}, "a", ["https://b/"]
        )
    assert "500" in e.value.message


def test_fetch_distributed_claims_invalid(mock_response):
    mock_response()
    with pytest.raises(tdf3_kas_core.errors.UnauthorizedError) as e:
        services._fetch_distributed_claims(
            {"a": "a"}, {"a": {"endpoint": "https://b/"}}, "a", ["https://b/"]
        )
    assert "remote claim not returned" in e.value.message
