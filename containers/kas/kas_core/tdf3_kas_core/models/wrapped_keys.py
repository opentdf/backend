"""WrappedKey class."""

import base64
import logging

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.backends.openssl.rsa import _RSAPrivateKey, _RSAPublicKey
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

from tdf3_kas_core.errors import CryptoError
from tdf3_kas_core.util import aes_gcm_decrypt, validate_hmac


logger = logging.getLogger(__name__)


def assure_public_key(public_key):
    """Assure that the public key is an _RSAPublicKey."""
    if isinstance(public_key, _RSAPublicKey):
        return public_key
    elif isinstance(public_key, _RSAPrivateKey):
        raise CryptoError("Public key expected in assure_public_key")
    try:
        # Assume the public key is a PEM encoded bytes. Try to construct
        # a public key. If it fails error will be caught.
        return serialization.load_pem_public_key(public_key, backend=default_backend())
    except Exception as e:
        raise CryptoError("Key error") from e


def assure_private_key(private_key):
    """Assure that the private key is an _RSAPrivateKey."""
    if isinstance(private_key, _RSAPrivateKey):
        return private_key
    elif isinstance(private_key, _RSAPublicKey):
        raise CryptoError("Private key expected in assure_private_key")
    else:
        try:
            # Assume the private key is a PEM encoded bytes. Try to construct
            # a private key. If it isn't PEM then this will raise an error.
            return serialization.load_pem_private_key(
                private_key, backend=default_backend(), password=None
            )
        except Exception as e:
            raise CryptoError("Key Error") from e


def aes_decrypt_sha1(cipher, private_key):
    """Decrypt AES, given OAEP padding with SHA1 hash."""
    try:
        key = assure_private_key(private_key)
        return key.decrypt(
            cipher,
            padding.OAEP(
                # TODO: https://virtru.atlassian.net/browse/PLAT-230
                # The following is not used in any security context.
                mgf=padding.MGF1(algorithm=hashes.SHA1()),  # nosec (B303)
                algorithm=hashes.SHA1(),  # nosec (B303)
                label=None,
            ),
        )
    except Exception as e:
        raise CryptoError("Decrypt failed") from e


decrypt_algs = {"RSA-OAEP": aes_decrypt_sha1}


def aes_encrypt_sha1(binary, public_key):
    """Encrypt AES using OAEP padding with SHA1 hash."""
    try:
        key = assure_public_key(public_key)
        return key.encrypt(
            binary,
            padding.OAEP(
                # TODO: https://virtru.atlassian.net/browse/PLAT-230
                # The following is not used in any security context.
                mgf=padding.MGF1(algorithm=hashes.SHA1()),  # nosec (B303)
                algorithm=hashes.SHA1(),  # nosec (B303)
                label=None,
            ),
        )
    except Exception as e:
        raise CryptoError("Encrypt failed") from e


encrypt_algs = {"RSA-OAEP": aes_encrypt_sha1}


class WrappedKey(object):
    """This class holds the wrapped key split.

    It also owns the key split rewrapping process.
    """

    @classmethod
    def from_raw(cls, raw_wrapped_key, private_unwrap_key, algorithm="RSA-OAEP"):
        """Create a WrappedKey from raw data."""
        logger.debug("------ Unpacking Wrapped Key")
        wrapped_key = base64.b64decode(raw_wrapped_key)
        plain_key = decrypt_algs[algorithm](wrapped_key, private_unwrap_key)
        wk = cls(plain_key)
        logger.debug("------ Wrapped Key construction complete")
        return wk

    @classmethod
    def from_plain(cls, plain_key):
        """Create a WrappedKey from a plain key."""
        return cls(plain_key)

    def __init__(self, plain_key):
        """Construct a WrappedKey instance if trusted.

        The risk of having the clear text key in memory (as self.__wrapped_key)
        is a trade against the extra work of repeated unwrapping operations.
        This decision should be revisited if there are security issues.
        """
        # If here then the key can be trusted. Pack and ship the instance.
        self.__unwrapped_key = plain_key

    def perform_hmac_check(self, binding, message, method="HS256"):
        """Perform a HMAC check on the message string.

        Throws an error if the HMAC does not pass.  Method is currently
        ignored.
        """
        logger.debug(message)
        logger.debug(binding)
        validate_hmac(message, self.__unwrapped_key, binding)

    def rewrap_key(self, entity_public_key, algorithm="RSA-OAEP"):
        """Rewrap the held key with another key."""
        entity_wrapped_key = encrypt_algs[algorithm](
            self.__unwrapped_key, entity_public_key
        )
        return bytes.decode(base64.b64encode(entity_wrapped_key))

    def decrypt(self, ciphertext, iv):
        return aes_gcm_decrypt(ciphertext, self.__unwrapped_key, iv)
