"""Test the key production functions."""

import os
import pytest  # noqa: F401

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

from tdf3_kas_core.util import get_public_key_from_pem
from tdf3_kas_core.util import get_private_key_from_pem


# //////// Public Key //////////


def test_get_public_key_from_pem(public_key):
    """Test the ability to parse a public key in PEM encoding."""
    actual_public_key = get_public_key_from_pem(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    assert isinstance(actual_public_key, RSAPublicKey)
    assert actual_public_key == public_key


def test_get_public_key_from_pem_cert():
    """Test the get_public_key_from_disk function as pem bytes."""
    curr_dir = os.path.dirname(__file__)
    path = os.path.join(curr_dir, "keys_for_tests/x509_cert.pem")
    with open(path, "rb") as test_file:
        public_key_cert = test_file.read()
        public_key = get_public_key_from_pem(public_key_cert)
        assert isinstance(public_key, x509.Certificate)


# //////// Private Key //////////


def test_get_private_key_from_pem(private_key):
    """Test the ability to parse a private key in PEM encoding."""
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    actual_private_key = get_private_key_from_pem(private_key_pem)
    assert isinstance(actual_private_key, RSAPrivateKey)
    assert actual_private_key.private_numbers() == private_key.private_numbers()
