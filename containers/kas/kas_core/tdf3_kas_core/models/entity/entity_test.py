"""Test the entity object."""

import jwt
import pytest
from cryptography.hazmat.primitives import serialization

import tdf3_kas_core

from tdf3_kas_core.errors import EntityError
from tdf3_kas_core.models import EntityAttributes

from .entity import Entity


def test_entity_constructor(public_key):
    """Test the basic constructor."""
    user_id = "Hey It's Me"
    attributes = EntityAttributes()
    actual = Entity(user_id, public_key, attributes)
    assert actual.user_id == user_id
    assert actual.public_key == public_key
    assert actual.attributes == attributes


def test_entity_constructor_bad_id(public_key):
    """Test the basic constructor."""
    user_id = {}
    attributes = EntityAttributes()
    with pytest.raises(EntityError):
        Entity(user_id, public_key, attributes)


def test_entity_constructor_bad_key():
    """Test the basic constructor."""
    user_id = "Hey It's Me"
    public_key = "Public key String"
    attributes = EntityAttributes()
    with pytest.raises(EntityError):
        Entity(user_id, public_key, attributes)


def test_entity_no_attributes(public_key):
    """Test the basic constructor."""
    user_id = "Hey It's Me"
    attributes = ["one", "two"]
    with pytest.raises(EntityError):
        Entity(user_id, public_key, attributes)


def test_entity_constructor_with_attributes(public_key):
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
    attributes = EntityAttributes.create_from_list(
        [
            {
                "attribute": attribute1,
                "displayName": "7b738968-131a-4de9-b4a1-c922f60583e3",
            },
            {
                "attribute": attribute2,
                "displayName": "7b738968-131a-4de9-b4a1-c922f60583e3",
            },
        ]
    )

    actual = Entity(user_id, public_key, attributes)

    assert actual.user_id == user_id
    assert actual.public_key == public_key
    attr1 = actual.attributes.get(attribute1)
    assert attr1.namespace == "https://aa.virtru.com/attr/unique-identifier"
    assert attr1.value == "7b738968-131a-4de9-b4a1-c922f60583e3"
    attr2 = actual.attributes.get(attribute2)
    assert attr2.namespace == "https://aa.virtru.com/attr/primary-organization"
    assert attr2.value == "7b738968-131a-4de9-b4a1-c922f60583e3"


def make_eo(public_key, private_key):
    data = {
        "userId": "user@virtru.com",
        "aliases": [],
        "attributes": [
            {
                "jwt": jwt.encode(
                    {"attribute": "https://example.com/attr/Classification/value/S"},
                    private_key,
                    algorithm="RS256",
                )
            },
            {
                "jwt": jwt.encode(
                    {"attribute": "https://example.com/attr/COI/value/PRX"},
                    private_key,
                    algorithm="RS256",
                )
            },
        ],
        "publicKey": public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("ascii"),
    }
    data["cert"] = jwt.encode(data, private_key, algorithm="RS256")
    return data


def test_load_from_raw_data_as_dict(public_key, private_key):
    """Test load_from_raw_data.  Raw data as a dict."""
    data = make_eo(public_key, private_key)
    actual = Entity.load_from_raw_data(data, public_key)


def test_load_from_raw_data_raises_on_invalid_jwt(public_key, private_key):
    """Test load_from_raw_data.  Raw data as a dict encoded as a jwt."""
    data = make_eo(public_key, private_key)
    # invalidate the jwt in the 'cert' field.
    data["cert"] = data["cert"] + "aaaaaaa"
    with pytest.raises(tdf3_kas_core.errors.AuthorizationError):
        Entity.load_from_raw_data(data, public_key)
