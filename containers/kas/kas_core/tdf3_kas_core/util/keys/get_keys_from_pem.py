"""Utility functions to get public and private keys from pem strings."""

import logging
from typing import Union

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ec import (
    EllipticCurvePrivateKey,
    EllipticCurvePublicKey,
)
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography import x509

from tdf3_kas_core.errors import KeyNotFoundError

logger = logging.getLogger(__name__)


def get_public_key_from_pem(
    pem: Union[str, x509.Certificate, EllipticCurvePrivateKey, RSAPublicKey],
) -> x509.Certificate | EllipticCurvePrivateKey | RSAPublicKey:
    """Deserialize a public key from a pem string."""
    if (
        isinstance(pem, EllipticCurvePublicKey)
        or isinstance(pem, RSAPublicKey)
        or isinstance(pem, x509.Certificate)
    ):
        return pem
    try:
        try:
            logger.debug("Attempting to return deserialized key")
            return serialization.load_pem_public_key(str.encode(pem), backend=default_backend())
        except Exception:
            logger.debug("Deserialization failed; loading cert")
            cert = x509.load_pem_x509_certificate(str.encode(pem), default_backend())
            logger.debug("Cert check passed, returning cert")
            return cert

    except Exception as err:
        raise KeyNotFoundError(
            "KEY File not found, or exception getting public key from pem."
        ) from err


def get_private_key_from_pem(
    pem: Union[str, EllipticCurvePrivateKey, RSAPrivateKey]
) -> EllipticCurvePrivateKey | RSAPrivateKey:
    """Deserialize a private key from a PEM string."""
    if isinstance(pem, EllipticCurvePrivateKey) or isinstance(pem, RSAPrivateKey):
        return pem
    try:
        logger.debug("Attempting to return deserialized key")
        return serialization.load_pem_private_key(
            str.encode(pem), password=None, backend=default_backend()
        )

    except Exception as e:
        raise KeyNotFoundError(
            "KEY File not found, or exception getting private key from pem."
        ) from e
