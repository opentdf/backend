import connexion
import json
import logging


from base64 import urlsafe_b64encode
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from jwt import PyJWK, PyJWS, PyJWT

from .authorized import authorized_v2, looks_like_jwt
from .errors import UnauthorizedError
from .keycloak import fetch_realm_key_by_jwt

logger = logging.getLogger(__name__)

ALLOWED_DPOP_ALGORITHMS = ["ES256", "ES384", "ES512", "RS256", "RS384", "RS512"]


def canonical(jwk):
    """Sort and filter the jwk according to the JWK thumbprint rules"""
    try:
        kty = jwk["kty"]
        if "RSA" == kty:
            return {
                "e": jwk["e"],
                "kty": "RSA",
                "n": jwk["n"],
            }
        if "EC" == kty:
            return {
                "crv": jwk["crv"],
                "kty": "EC",
                "x": jwk["x"],
                "y": jwk["y"],
            }
    except Exception as e:
        raise UnauthorizedError(f"Invalid JWK {jwk}") from e
    raise UnauthorizedError(f"Unsupported JWK {jwk}")


def jws_sha(s):
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(bytes(s.encode("utf8")))
    encoded = urlsafe_b64encode(digest.finalize())
    return encoded.decode("utf8").rstrip("=")


def jwk_thumbprint(jwk):
    c = canonical(jwk)
    cs = json.dumps(c, separators=(",", ":"), sort_keys=True)
    return jws_sha(cs)


def validate_dpop(dpop, key_master, request=connexion.request, do_oidc=False):
    """Validate a dpop header, when present."""
    # First, grab Auth JWT
    auth_header = request.headers.get("authorization", None)
    if not auth_header:
        if do_oidc:
            raise UnauthorizedError("Missing auth header")
        logger.debug("Missing auth header")
        return
    bearer, _, id_jwt = auth_header.partition(" ")
    logger.debug("id_jwt: [%s], dpop: [%s]", id_jwt, dpop)
    if bearer != "Bearer" or not looks_like_jwt(id_jwt):
        raise UnauthorizedError("Invalid auth header")
    verifier_key = fetch_realm_key_by_jwt(id_jwt, key_master)
    jwt_decoded = authorized_v2(verifier_key, id_jwt)
    logger.debug("jwt_decoded: [%s]", jwt_decoded)
    cnf = jwt_decoded.get("cnf", None)
    # NOTE: Somehow the dpop field isn't populated yet? What am I doing wrong
    # with connexion?
    if not dpop:
        dpop = request.headers.get("dpop", None)
    if not dpop and not cnf:
        logger.debug("DPoP not required, not found")
        return
    if dpop and not cnf:
        logger.warn(
            "DPoP found but unconfirmed [%s] not referenced from [%s]", dpop, id_jwt
        )
        return
    if not dpop and cnf:
        raise UnauthorizedError("DPoP Required")
    try:
        jkt = cnf["jkt"]
    except:
        raise UnauthorizedError(f"Unsupported JWT confirmation type [{cnf}]")

    # First, validate header and check
    decoded = PyJWS(options={"verify_signature": False}).decode_complete(dpop)
    if decoded["header"]["typ"] != "dpop+jwt":
        raise UnauthorizedError("Invalid JWT")
    if decoded["header"]["alg"] not in ALLOWED_DPOP_ALGORITHMS:
        raise UnauthorizedError("Invalid JWT")
    jwk = decoded["header"]["jwk"]
    key_thumbprint = jwk_thumbprint(jwk)
    if key_thumbprint != jkt:
        raise UnauthorizedError("Invalid DPoP")

    try:
        key = PyJWK.from_dict(jwk).key
        decoded = PyJWT().decode(
            dpop,
            key,
            algorithms=["RS256", "ES256", "ES384", "ES512"],
        )
        # TODO: Validate jti is not 'recently seen'
        ath = decoded["ath"]
        htm = decoded["htm"]
        htu = decoded["htu"]
        m = request.method.lower()
        u = request.url
    except Exception as e:
        raise UnauthorizedError("Invalid JWT") from e

    if m != htm or u != htu:
        logger.warning("Invalid DPoP htm:[%s] htu:[%s] != m:[%s] u[%s]", htm, htu, m, u)
        raise UnauthorizedError("Invalid DPoP")
    access_token_hash = jws_sha(id_jwt)
    if ath != access_token_hash:
        logger.warning(
            "Invalid DPoP ath:[%s] not hash of [%s], should be [%s]",
            ath,
            id_jwt,
            access_token_hash,
        )
        raise UnauthorizedError("Invalid DPoP")
    logger.info("DPoP Validated!")
