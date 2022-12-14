import logging
import pytest

from dataclasses import dataclass, field
from jwt import PyJWK, PyJWS, PyJWT

from .dpop import canonical, jwk_thumbprint, validate_dpop
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


@dataclass
class MockRequest:
    headers: dict[str, str] = field(default_factory=lambda: {})
    method: str = "get"
    url: str = "http://localhost/"


def test_validate_dpop_no_auth():
    with pytest.raises(UnauthorizedError, match=r".*Missing auth.*"):
        validate_dpop("", MockRequest(), True)


def test_validate_dpop_malformed_auth():
    with pytest.raises(UnauthorizedError, match=r".*Invalid auth.*"):
        validate_dpop("", MockRequest({"authorization": "Barely a.b.c"}))


def test_validate_dpop_malformed_auth_2():
    with pytest.raises(UnauthorizedError, match=r".*Invalid JWT.*"):
        validate_dpop("", MockRequest({"authorization": "Bearer a.b.c"}))


def test_validate_dpop_standard_auth():
    id_jwt = PyJWT().encode(
        {},
        "secret",
        algorithm="HS256",
    )
    validate_dpop("", MockRequest({"authorization": f"Bearer {id_jwt}"}))


def test_validate_dpop_no_cnf_ignored():
    id_jwt = PyJWT().encode(
        {},
        "secret",
        algorithm="HS256",
    )
    dpop = "eyJhbGciOiJSUzI1NiIsInR5cCI6ImRwb3Arand0IiwiandrIjp7Imt0eSI6IlJTQSIsImUiOiJBUUFCIiwibiI6ImpZWUdvcGxoT3ViWnBiQ1ZVa0RDMTJhVUU3MmJKYk9Oa3VoS1g1ZVBMcXhiYV9BYWN5NXpzei04Ykxab2ttY2lKOUtQc2dwMkl3Q050UDBDMTJrX25kRlBGYzhwQ3pjSWp5MUxRZ3JnMEtUdXhac1JLN0k1bnRBOTRVM3IxR0tMcTBjM1J3RGZ2dWZDLUtjb2g5aWNVM0xFOTZGZUlmTFozYzlnMmROai1MWXJ4eFBPSzFuY2dobmZMbHI5QXNiM3UweUt2eFZ6M1FUTVRoVUFmTVY0NmFVdXdKSi1RNXRYLUZKbXdqajZRNVQ0bzgyT2xLcjhzZDZoZGp6NkY2YUlrMDIzcmxXeFRfRmdPLU1MdS0tVkFBblpuXzBaSFhKSGRCUjA2NUpKVi1obE5YdmdtZnJqOTFmckY2djNabDY2QUtJQUZQd29GdHV3ZzR2S0pFaFUzdyJ9fQ.eyJpYXQiOjE2NzA4NjY4MzEsImp0aSI6InBkc2tsX0lKdHJtY2h3NlZ1UjQycEZFZDFoTWxzVmlMNnV4MUcxT0FzRHMiLCJodG0iOiJQT1NUIiwiaHR1IjoiaHR0cDovL2xvY2FsaG9zdDo2NTQzMi9hdXRoL3JlYWxtcy90ZGYvcHJvdG9jb2wvb3BlbmlkLWNvbm5lY3QvdG9rZW4ifQ.WB_43xmaKdr--j7rm4Z1O1OVUXroxA-Pyp2j1qHHz0pwRq4ejHG3ev83edjOQT-sXp5kyySw2o-d5cW33OkGy1ZP2kX_B4TILwvVCIEGtXoz_JfKWchCVdQ49AmaTekWTq66uE8SA-H8NIyTaKIouMmGF4_wRFFH8nv203NVd_V2tSxm7AlrwlD2WdvB6a81tfw2wFBnxivoup0SKdy1UbEZ0usn-IcoVlqI-cy7dw_rdnJ7Gm6AwbJiNgLbcdN_-nzOXmJro7Mn41PMQCT13IZiP17fs1j58dpE11xYyQWWEjgFZG19iflzloKkNeoXy8uPT-iRgnunr-8FUay0sA"
    validate_dpop(
        None, MockRequest({"authorization": f"Bearer {id_jwt}", "dpop": dpop})
    )


def test_validate_dpop_invalid_cnf():
    id_jwt = PyJWT().encode(
        {"cnf": "unknwon"},
        "secret",
        algorithm="HS256",
    )
    dpop = "eyJhbGciOiJSUzI1NiIsInR5cCI6ImRwb3Arand0IiwiandrIjp7Imt0eSI6IlJTQSIsImUiOiJBUUFCIiwibiI6ImpZWUdvcGxoT3ViWnBiQ1ZVa0RDMTJhVUU3MmJKYk9Oa3VoS1g1ZVBMcXhiYV9BYWN5NXpzei04Ykxab2ttY2lKOUtQc2dwMkl3Q050UDBDMTJrX25kRlBGYzhwQ3pjSWp5MUxRZ3JnMEtUdXhac1JLN0k1bnRBOTRVM3IxR0tMcTBjM1J3RGZ2dWZDLUtjb2g5aWNVM0xFOTZGZUlmTFozYzlnMmROai1MWXJ4eFBPSzFuY2dobmZMbHI5QXNiM3UweUt2eFZ6M1FUTVRoVUFmTVY0NmFVdXdKSi1RNXRYLUZKbXdqajZRNVQ0bzgyT2xLcjhzZDZoZGp6NkY2YUlrMDIzcmxXeFRfRmdPLU1MdS0tVkFBblpuXzBaSFhKSGRCUjA2NUpKVi1obE5YdmdtZnJqOTFmckY2djNabDY2QUtJQUZQd29GdHV3ZzR2S0pFaFUzdyJ9fQ.eyJpYXQiOjE2NzA4NjY4MzEsImp0aSI6InBkc2tsX0lKdHJtY2h3NlZ1UjQycEZFZDFoTWxzVmlMNnV4MUcxT0FzRHMiLCJodG0iOiJQT1NUIiwiaHR1IjoiaHR0cDovL2xvY2FsaG9zdDo2NTQzMi9hdXRoL3JlYWxtcy90ZGYvcHJvdG9jb2wvb3BlbmlkLWNvbm5lY3QvdG9rZW4ifQ.WB_43xmaKdr--j7rm4Z1O1OVUXroxA-Pyp2j1qHHz0pwRq4ejHG3ev83edjOQT-sXp5kyySw2o-d5cW33OkGy1ZP2kX_B4TILwvVCIEGtXoz_JfKWchCVdQ49AmaTekWTq66uE8SA-H8NIyTaKIouMmGF4_wRFFH8nv203NVd_V2tSxm7AlrwlD2WdvB6a81tfw2wFBnxivoup0SKdy1UbEZ0usn-IcoVlqI-cy7dw_rdnJ7Gm6AwbJiNgLbcdN_-nzOXmJro7Mn41PMQCT13IZiP17fs1j58dpE11xYyQWWEjgFZG19iflzloKkNeoXy8uPT-iRgnunr-8FUay0sA"
    with pytest.raises(UnauthorizedError, match=r".*Unsupported.*"):
        validate_dpop(
            None, MockRequest({"authorization": f"Bearer {id_jwt}", "dpop": dpop})
        )


def test_validate_dpop_mismatch_cnf():
    id_jwt = PyJWT().encode(
        {"cnf": {"jkt": "incorrect"}},
        "secret",
        algorithm="HS256",
    )
    dpop = "eyJhbGciOiJSUzI1NiIsInR5cCI6ImRwb3Arand0IiwiandrIjp7Imt0eSI6IlJTQSIsImUiOiJBUUFCIiwibiI6ImpZWUdvcGxoT3ViWnBiQ1ZVa0RDMTJhVUU3MmJKYk9Oa3VoS1g1ZVBMcXhiYV9BYWN5NXpzei04Ykxab2ttY2lKOUtQc2dwMkl3Q050UDBDMTJrX25kRlBGYzhwQ3pjSWp5MUxRZ3JnMEtUdXhac1JLN0k1bnRBOTRVM3IxR0tMcTBjM1J3RGZ2dWZDLUtjb2g5aWNVM0xFOTZGZUlmTFozYzlnMmROai1MWXJ4eFBPSzFuY2dobmZMbHI5QXNiM3UweUt2eFZ6M1FUTVRoVUFmTVY0NmFVdXdKSi1RNXRYLUZKbXdqajZRNVQ0bzgyT2xLcjhzZDZoZGp6NkY2YUlrMDIzcmxXeFRfRmdPLU1MdS0tVkFBblpuXzBaSFhKSGRCUjA2NUpKVi1obE5YdmdtZnJqOTFmckY2djNabDY2QUtJQUZQd29GdHV3ZzR2S0pFaFUzdyJ9fQ.eyJpYXQiOjE2NzA4NjY4MzEsImp0aSI6InBkc2tsX0lKdHJtY2h3NlZ1UjQycEZFZDFoTWxzVmlMNnV4MUcxT0FzRHMiLCJodG0iOiJQT1NUIiwiaHR1IjoiaHR0cDovL2xvY2FsaG9zdDo2NTQzMi9hdXRoL3JlYWxtcy90ZGYvcHJvdG9jb2wvb3BlbmlkLWNvbm5lY3QvdG9rZW4ifQ.WB_43xmaKdr--j7rm4Z1O1OVUXroxA-Pyp2j1qHHz0pwRq4ejHG3ev83edjOQT-sXp5kyySw2o-d5cW33OkGy1ZP2kX_B4TILwvVCIEGtXoz_JfKWchCVdQ49AmaTekWTq66uE8SA-H8NIyTaKIouMmGF4_wRFFH8nv203NVd_V2tSxm7AlrwlD2WdvB6a81tfw2wFBnxivoup0SKdy1UbEZ0usn-IcoVlqI-cy7dw_rdnJ7Gm6AwbJiNgLbcdN_-nzOXmJro7Mn41PMQCT13IZiP17fs1j58dpE11xYyQWWEjgFZG19iflzloKkNeoXy8uPT-iRgnunr-8FUay0sA"
    with pytest.raises(UnauthorizedError, match=r".*Invalid DPoP.*"):
        validate_dpop(
            None, MockRequest({"authorization": f"Bearer {id_jwt}", "dpop": dpop})
        )
