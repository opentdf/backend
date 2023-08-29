"""Test the claims object."""

import pytest
from cryptography.hazmat.primitives import serialization

from tdf3_kas_core.errors import ClaimsError
from tdf3_kas_core.models import ClaimsAttributes

from .claims import Claims


def test_claims_constructor(public_key):
    """Test the basic constructor."""
    user_id = "Hey It's Me"
    attributes = {}
    attributes[user_id] = ClaimsAttributes()
    actual = Claims(user_id, public_key, attributes)
    assert actual.user_id == user_id
    assert actual.client_public_signing_key == public_key
    assert actual.entity_attributes == attributes


def test_claims_constructor_bad_id(public_key):
    """Test the basic constructor."""
    user_id = {}
    attributes = ClaimsAttributes()
    with pytest.raises(ClaimsError):
        Claims(user_id, public_key, attributes)


def test_claims_constructor_bad_key(public_key):
    """Test the basic constructor."""
    user_id = "Hey It's Me"
    public_key = "Public key String"
    attributes = ClaimsAttributes()
    with pytest.raises(ClaimsError):
        Claims(user_id, public_key, attributes)


def test_claims_no_attributes(public_key):
    """Test the basic constructor."""
    user_id = "Hey It's Me"
    attributes = ["one", "two"]
    with pytest.raises(ClaimsError):
        Claims(user_id, public_key, attributes)


def test_claims_constructor_with_attributes(public_key):
    """Test the basic constructor."""
    user_id = "Hey It's Me"
    attribute1 = (
        "https://aa.virtru.com/attr/unique-identifier"
        "/value/7b738968-131a-4de9-b4a1-c922f60583e3"
    )
    attribute2 = (
        "https://aa.virtru.com/attr/primary-organization"
        "/value/7b738968-131a-4de9-b4a1-c922f60583e3"
    )
    attributes = ClaimsAttributes.create_from_list(
        user_id,
        [
            {
                "attribute": attribute1,
                "displayName": "7b738968-131a-4de9-b4a1-c922f60583e3",
            },
            {
                "attribute": attribute2,
                "displayName": "7b738968-131a-4de9-b4a1-c922f60583e3",
            },
        ],
    )

    actual = Claims(user_id, public_key, attributes)

    assert actual.user_id == user_id
    assert actual.client_public_signing_key == public_key
    attr1 = actual.entity_attributes[user_id].get(attribute1)
    assert attr1.namespace == "https://aa.virtru.com/attr/unique-identifier"
    assert attr1.value == "7b738968-131a-4de9-b4a1-c922f60583e3"
    attr2 = actual.entity_attributes[user_id].get(attribute2)
    assert attr2.namespace == "https://aa.virtru.com/attr/primary-organization"
    assert attr2.value == "7b738968-131a-4de9-b4a1-c922f60583e3"


def make_claims_object(public_key):
    data = {
        "sub": "user@virtru.com",
        "tdf_claims": {
            "client_public_signing_key": public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode("ascii"),
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
        },
        "tdf_spec_version": "4.0.0",
    }
    return data


def test_load_from_raw_data_as_dict(public_key):
    """Test load_from_raw_data.  Raw data as a dict."""
    data = make_claims_object(public_key)
    actual = Claims.load_from_raw_data(data)
    assert actual.user_id == "user@virtru.com"
