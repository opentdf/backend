import pytest
import logging

from .dpop import canonical, jwk_thumbprint

from .errors import UnauthorizedError

logger = logging.getLogger(__name__)


def test_canonical_strips():
    assert {"e": "AQAB", "kty": "RSA", "n": "01234567"} == canonical(
        {"kty": "RSA", "e": "AQAB", "n": "01234567", "asdf": "extra"}
    )


def test_canonical_fails_on_unknown():
    with pytest.raises(UnauthorizedError):
        canonical({"kty": "None"})


def test_jwk_thumbprint():
    assert "bbsSdyA_3m_aig3CvdaLcYWvLRg1Yidpym39xpkODxY" == jwk_thumbprint(
        {
            "kty": "RSA",
            "e": "AQAB",
            "n": "jYYGoplhOubZpbCVUkDC12aUE72bJbONkuhKX5ePLqxba_Aacy5zsz-8bLZokmciJ9KPsgp2IwCNtP0C12k_ndFPFc8pCzcIjy1LQgrg0KTuxZsRK7I5ntA94U3r1GKLq0c3RwDfvufC-Kcoh9icU3LE96FeIfLZ3c9g2dNj-LYrxxPOK1ncghnfLlr9Asb3u0yKvxVz3QTMThUAfMV46aUuwJJ-Q5tX-FJmwjj6Q5T4o82OlKr8sd6hdjz6F6aIk023rlWxT_FgO-MLu--VAAnZn_0ZHXJHdBR065JJV-hlNXvgmfrj91frF6v3Zl66AKIAFPwoFtuwg4vKJEhU3w",
        }
    )
