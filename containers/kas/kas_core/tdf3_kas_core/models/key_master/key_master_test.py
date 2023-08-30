"""Test the KeyMaster."""

import pytest

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

#
from tdf3_kas_core.errors import KeyNotFoundError

from .key_master import KeyMaster


def test_key_master():
    """Test the KeyMaster constructor."""
    km = KeyMaster()
    assert isinstance(km, KeyMaster)


def test_key_master_set_key_bad_type():
    """Test the KeyMaster set function."""
    km = KeyMaster()
    with pytest.raises(KeyError):
        km.set_key_path("name", "UNKNOWN_TYPE", "some path")


def test_key_master_get_key_public(public_key_path):
    """Get a public key."""
    km = KeyMaster()
    km.set_key_path("PUB", "PUBLIC", public_key_path)
    actual = km.public_key("PUB")
    assert isinstance(actual, RSAPublicKey)


def test_key_master_export_key_private(private_key_path):
    """Get a private key."""
    km = KeyMaster()
    km.set_key_path("PRIV", "PRIVATE", private_key_path)
    with pytest.raises(AttributeError):
        km.get_export_string("PRIV")


def test_key_master_export_public(public_key_path):
    """Get a public key."""
    km = KeyMaster()
    km.set_key_path("PUB", "PUBLIC", public_key_path)
    actual = km.get_export_string("PUB")
    assert isinstance(actual, str)


def test_key_master_get_private(private_key_path):
    """Get a private key."""
    km = KeyMaster()
    km.set_key_path("PRIV", "PRIVATE", private_key_path)
    actual = km.private_key("PRIV")
    assert isinstance(actual, RSAPrivateKey)


def test_key_master_private_key_non_existant():
    """Try to get a non-existant key."""
    km = KeyMaster()
    with pytest.raises(KeyNotFoundError):
        km.private_key("DOES_NOT_EXIST")


def test_key_master_public_key_non_existant():
    """Try to get a non-existant key."""
    km = KeyMaster()
    with pytest.raises(KeyNotFoundError):
        km.public_key("DOES_NOT_EXIST")
