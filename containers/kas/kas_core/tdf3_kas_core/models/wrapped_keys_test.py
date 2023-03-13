"""Test the wrapped key."""

import base64
import pytest

from cryptography.hazmat.backends.openssl.rsa import _RSAPrivateKey, _RSAPublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from tdf3_kas_core.errors import CryptoError
from tdf3_kas_core.util import get_public_key_from_disk
from tdf3_kas_core.util import get_private_key_from_disk
from tdf3_kas_core.util import generate_hmac_digest
from tdf3_kas_core.util.cipher.aes_gcm import aes_gcm_decrypt, aes_gcm_encrypt


from .wrapped_keys import (
    aes_decrypt_sha1,
    aes_encrypt_sha1,
    WrappedKey,
    assure_private_key,
    assure_public_key,
)

kas_public_key = get_public_key_from_disk("test")
kas_private_key = get_private_key_from_disk("test")
entity_public_key = get_public_key_from_disk("test_alt")
entity_private_key = get_private_key_from_disk("test_alt")


plain_key = b"This-is-the-good-key"
wrapped_key = aes_encrypt_sha1(plain_key, kas_public_key)
good_msg = b"This message is valid"
good_binding = str.encode(generate_hmac_digest(good_msg, plain_key))

# /////// Constructor tests ///////////


def test_wrapped_key_constructor_success():
    """Test to see if it constructs under ideal conditions."""
    test_item = WrappedKey(plain_key)
    assert isinstance(test_item, WrappedKey)


# /////// Factory test(s) ///////////


def test_wrapped_key_from_plain():
    """Test the plain key getter."""
    test_item = WrappedKey.from_plain(plain_key)
    assert test_item._WrappedKey__unwrapped_key == plain_key


def test_wrapped_key_from_raw():
    """Test the from raw factory function."""
    raw_wrapped_key = bytes.decode(base64.b64encode(wrapped_key))
    test_item = WrappedKey.from_raw(raw_wrapped_key, kas_private_key)
    assert isinstance(test_item, WrappedKey)
    assert test_item._WrappedKey__unwrapped_key == plain_key


def test_rsa_sha1_keys():
    """Test asymmetric RSA SHA1 encrypt/decrypt."""
    expected = b"Cozy sphinx waves quart jug of bad milk"
    wrapped = aes_encrypt_sha1(expected, public_key)
    actual = aes_decrypt_sha1(wrapped, private_key)
    assert actual == expected


def test_wrapped_key_rewrap_key():
    """Test the rewrap method."""
    test_item = WrappedKey(plain_key)
    rewrapped_b64str = test_item.rewrap_key(entity_public_key)
    rewrapped = base64.b64decode(str.encode(rewrapped_b64str))
    actual = aes_decrypt_sha1(rewrapped, entity_private_key)
    print(actual)
    assert actual == plain_key


def test_wrapped_key_decrypt():
    """Test the decrypt method."""
    test_item = WrappedKey(plain_key)
    rewrapped_b64str = test_item.rewrap_key(entity_public_key)
    rewrapped = base64.b64decode(str.encode(rewrapped_b64str))
    actual = aes_decrypt_sha1(rewrapped, entity_private_key)
    print(actual)
    assert actual == plain_key


def test_aes_gcm_mode():
    """Test encrypt/decrypt."""
    expected = b"This message is the expected message."
    key = AESGCM.generate_key(bit_length=128)
    (ciphertext, iv) = aes_gcm_encrypt(expected, key)
    actual = WrappedKey(key).decrypt(ciphertext, iv)
    assert actual == expected


public_key = get_public_key_from_disk("test")
private_key = get_private_key_from_disk("test")

public_key_pem = get_public_key_from_disk("test", as_pem=True)
private_key_pem = get_private_key_from_disk("test", as_pem=True)


def test_assure_public_key_key():
    """Test assure_public_key passes through RSAPublicKeys."""
    actual = assure_public_key(public_key)
    assert actual == public_key


def test_assure_public_key_pem():
    """Test assure_public_key converts PEM encoded bytes."""
    actual = assure_public_key(public_key_pem)
    assert isinstance(actual, _RSAPublicKey)


def test_assure_public_key_fail_str():
    """Test assure_public_key raises error on bad input."""
    with pytest.raises(CryptoError):
        assure_public_key("bad input")


def test_assure_public_key_fail_private():
    """Test assure_public_key raises error with private key."""
    with pytest.raises(CryptoError):
        assure_public_key(private_key)


def test_assure_public_key_fail_private_pem():
    """Test assure_public_key raises error with private pem."""
    with pytest.raises(CryptoError):
        assure_public_key(private_key_pem)


def test_assure_private_key_key():
    """Test assure_private_key passes through RSAPrivateKeys."""
    actual = assure_private_key(private_key)
    assert actual == private_key


def test_assure_private_key_pem():
    """Test assure_private_key converts PEM encoded bytes."""
    actual = assure_private_key(private_key_pem)
    assert isinstance(actual, _RSAPrivateKey)


def test_assure_private_key_fail_bad_input():
    """Test assure_private_key raises error on bad input."""
    with pytest.raises(CryptoError):
        assure_private_key("bad input")


def test_assure_private_key_fail_public():
    """Test assure_private_key raises error on public key."""
    with pytest.raises(CryptoError):
        assure_private_key(public_key)


def test_assure_private_key_fail_public_pem():
    """Test assure_private_key raises error on bad input."""
    with pytest.raises(CryptoError):
        assure_private_key(public_key_pem)
