"""Fixtures that produce commonly used models.

Pytest searches for conftest.py files to harvest these fixtures.
"""

import pytest

import json
import base64

from .models import Policy
from .models import EntityAttributes
from .models import KeyAccess
from .models import Context

from .util import get_public_key_from_disk
from .util import get_private_key_from_disk
from .util import generate_hmac_digest
from .util import aes_encrypt_sha1

public_key = get_public_key_from_disk("test")
private_key = get_private_key_from_disk("test")

entity_public_key = get_public_key_from_disk("test_alt")
entity_private_key = get_private_key_from_disk("test_alt")


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
def key_access_wrapped():
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
