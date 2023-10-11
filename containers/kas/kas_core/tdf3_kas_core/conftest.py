"""Fixtures that produce commonly used models.

Pytest searches for conftest.py files to harvest these fixtures.
"""

import os
import pytest

import json
import base64

from .models import Policy
from .models import Entity
from .models import EntityAttributes
from .models import KeyAccess
from .models import Context
from .models.wrapped_keys import aes_encrypt_sha1

from .util import get_public_key_from_pem
from .util import get_private_key_from_pem
from .util import generate_hmac_digest


def test_path(fname):
    return os.path.join(os.path.dirname(__file__), f"util/keys/keys_for_tests/{fname}")


def test_key_path(type):
    return test_path(f"rsa_{type}.pem")


@pytest.fixture
def public_key_path():
    return test_key_path("public")


@pytest.fixture
def private_key_path():
    return test_key_path("private")


@pytest.fixture
def ec_cert_path():
    return test_path("ec_cert.crt")


@pytest.fixture
def ec_private_key_path():
    return test_path("ec_private.key")


@pytest.fixture
def entity_public_key_path():
    return test_key_path("public_alt")


@pytest.fixture
def entity_private_path():
    return test_key_path("private_alt")


def read_test_file(path):
    with open(path, "rb") as test_file:
        return test_file.read()


__public_key = get_public_key_from_pem(read_test_file(test_key_path("public")))
__private_key = get_private_key_from_pem(read_test_file(test_key_path("private")))

__ec_cert = get_public_key_from_pem(read_test_file(test_path("ec_cert.crt")))
__ec_private_key = get_private_key_from_pem(read_test_file(test_path("ec_private.key")))

__entity_public_key = get_public_key_from_pem(
    read_test_file(test_key_path("public_alt"))
)
__entity_private_key = get_private_key_from_pem(
    read_test_file(test_key_path("private_alt"))
)


@pytest.fixture
def public_key():
    return __public_key


@pytest.fixture
def private_key():
    return __private_key


@pytest.fixture
def entity_public_key():
    return __entity_public_key


@pytest.fixture
def entity_private_key():
    return __entity_private_key


@pytest.fixture
def ec_cert():
    return __ec_cert


@pytest.fixture
def ec_private_key():
    return __ec_private_key


@pytest.fixture
def policy():
    """Construct a policy object."""
    data_attributes = [
        {"attribute": "https://example.com/attr/Classification/value/S"},
        {"attribute": "https://example.com/attr/COI/value/PRX"},
    ]
    raw_dict = {
        "uuid": "1111-2222-33333-44444-abddef-timestamp",
        "body": {"dataAttributes": data_attributes, "dissem": ["user-id@domain.com"]},
    }
    raw_can = bytes.decode(base64.b64encode(str.encode(json.dumps(raw_dict))))
    yield Policy.construct_from_raw_canonical(raw_can)


@pytest.fixture
def entity(public_key):
    """Construct an entity object."""
    user_id = "coyote@acme.com"
    attribute1 = (
        "https://aa.virtru.com/attr/unique-identifier"
        "/value/7b738968-131a-4de9-b4a1-c922f60583e3"
    )
    attribute2 = (
        "https://aa.virtru.com/attr/primary-organization"
        "/value/7b738968-131a-4de9-b4a1-c922f60583e3"
    )

    attributes = EntityAttributes.create_from_list(
        [{"attribute": attribute1}, {"attribute": attribute2}]
    )
    yield Entity(user_id, public_key, attributes)


@pytest.fixture
def key_access_remote():
    """Generate an access key for a remote type."""
    raw = {
        "type": "remote",
        "url": "http://127.0.0.1:4000",
        "protocol": "kas",
        "policySyncOptions": {"url": "http://localhost:3000/api/policies"},
    }
    yield KeyAccess.from_raw(raw)


@pytest.fixture
def key_access_wrapped(public_key, private_key):
    """Generate an access key for a wrapped type."""
    plain_key = b"This-is-the-good-key"
    wrapped_key = aes_encrypt_sha1(plain_key, public_key)
    msg = b"This message is valid"
    binding = str.encode(generate_hmac_digest(msg, plain_key))

    raw_wrapped_key = bytes.decode(base64.b64encode(wrapped_key))
    raw_binding = bytes.decode(base64.b64encode(binding))
    canonical_policy = bytes.decode(msg)
    raw = {
        "type": "wrapped",
        "url": "http://127.0.0.1:4000",
        "protocol": "kas",
        "wrappedKey": raw_wrapped_key,
        "policyBinding": raw_binding,
    }
    yield KeyAccess.from_raw(raw, private_key, canonical_policy)


@pytest.fixture
def context():
    """Generate an empty context object."""
    yield Context()
