"""Authorized function."""

import jwt
import logging
import os
import re
import requests

from cryptography.hazmat.primitives.asymmetric.types import PublicKeyTypes
from datetime import datetime, timedelta

from tdf3_kas_core.errors import AuthorizationError
from tdf3_kas_core.errors import JWTError
from tdf3_kas_core.errors import UnauthorizedError
from tdf3_kas_core.keycloak import fetch_realm_key_by_jwt
from tdf3_kas_core.models.key_master.key_master import KeyMaster


logger = logging.getLogger(__name__)

JWT_EXCEPTIONS = (
    jwt.exceptions.InvalidTokenError,
    jwt.exceptions.DecodeError,
    jwt.exceptions.InvalidSignatureError,
    jwt.exceptions.ExpiredSignatureError,
    jwt.exceptions.InvalidAudienceError,
    jwt.exceptions.InvalidIssuerError,
    jwt.exceptions.InvalidIssuedAtError,
    jwt.exceptions.ImmatureSignatureError,
    jwt.exceptions.InvalidKeyError,
    jwt.exceptions.InvalidAlgorithmError,
    jwt.exceptions.MissingRequiredClaimError,
)

# Number of seconds of leeway for expiry in token validation
# If you need more than 2 mins of leeway, you have a server config problem that you need to fix.
# NOTE: When we drop support <3.8, add `: typing.Final` below
max_leeway = 120
default_leeway = 30
assert 0 <= default_leeway <= max_leeway
leeway = default_leeway


try:
    suggested_leeway = int(os.environ["KAS_JWT_LEEWAY"])
    if 0 <= suggested_leeway <= max_leeway:
        leeway = suggested_leeway
        logger.info("KAS_JWT_LEEWAY set to [%s]", suggested_leeway)
    else:
        logger.error(
            "KAS_JWT_LEEWAY out of bounds [%s] [%s]", suggested_leeway, max_leeway
        )
except KeyError:
    pass
except TypeError:
    logger.error("Invalid KAS_JWT_LEEWAY", exc_info=True)


def unpack_rs256_jwt(jwt_string, public_key):
    """Unpack asymmetric JWT using RSA 256 public key."""
    try:
        return jwt.decode(jwt_string, public_key, algorithms=["RS256"], leeway=leeway)
    except JWT_EXCEPTIONS as err:
        raise JWTError("Error decoding rs256 JWT") from err


def pack_rs256_jwt(payload, private_key, *, exp_hrs=None, exp_sec=None):
    """Create asymmetric JWT with RSA 256 private key."""
    try:
        if exp_hrs:
            now = datetime.now()
            delta = timedelta(hours=exp_hrs)
            payload["exp"] = (now + delta).timestamp()
        elif exp_sec:
            now = datetime.now()
            delta = timedelta(seconds=exp_sec)
            payload["exp"] = (now + delta).timestamp()
        return jwt.encode(payload, private_key, algorithm="RS256")
    except JWT_EXCEPTIONS as err:
        raise JWTError("Error encoding rs256 JWT") from err


JWT_RE = re.compile(r"^[a-zA-Z0-9\-_]+?\.[a-zA-Z0-9\-_]+?\.([a-zA-Z0-9\-_]+)?$")


def looks_like_jwt(jwt):
    match = JWT_RE.match(jwt)
    return bool(match)


def authorized(public_key, auth_token) -> bool:
    """Raise error if the public key does not validate the JWT auth_token."""
    try:
        unpack_rs256_jwt(auth_token, public_key)
        return True
    except Exception as e:
        raise AuthorizationError("Not authorized") from e


def oidc_discovery(server: str) -> dict:
    """Looks up the OIDC Discovery information for the given OpenId provider"""
    # https://openid.net/specs/openid-connect-discovery-1_0.html
    cfg_url = f'{server.removesuffix("/")}/.well-known/openid-configuration'
    r = requests.get(cfg_url, headers={"content-type": "application/json"})
    if r.status_code == 200:
        if "application/json" in r.headers["content-type"]:
            values = r.json()
        else:
            logger.warning(
                "oidc discovery: unrecognized content type [%s] from [%s]",
                r.headers["content-type"],
                cfg_url,
            )
            raise UnauthorizedError("oidc discovery: unrecognized content type")
    elif r.status_code >= 400:
        logger.warning("oidc discovery: [%s] from [%s]", r.status_code, server)
        raise UnauthorizedError(f"oidc discovery: {r.status_code} from backend")
    else:
        raise UnauthorizedError("oidc discovery: network failure")
    return values


def jwt_verifier_key(
    issuer: str, discovery_base: str | None, idpJWT: str | bytes
) -> PublicKeyTypes:
    # We must extract `iss` without validating the JWT,
    # because we need `iss` to know which specific realm endpoint to hit
    # to get the public key we would verify it with
    unverified = jwt.PyJWT().decode_complete(
        idpJWT, options={"verify_signature": False}
    )
    unverified_jwt = unverified["payload"]
    issuer_url = unverified_jwt["iss"]
    if issuer != issuer_url:
        # Fail fast; don't bother with other work if from invalid issuer
        logger.warning("Issuer mismatch: [%s] should be [%s]", issuer_url, issuer)
        raise UnauthorizedError("Invalid auth header")
    oidc_config = oidc_discovery(discovery_base or issuer)
    # TODO Cache jwks_client by uri
    jwks_client = jwt.PyJWKClient(oidc_config["jwks_uri"])
    jwk = jwks_client.get_signing_key_from_jwt(jwt)
    return jwk.key


def _get_keycloak_host():
    return os.environ.get("OIDC_SERVER_URL")


def _get_single_auth_host():
    return os.environ.get("OIDC_ISSUER_URL")


# For compatibility, this can look up a key from the OIDC_ISSUER_URL
# (single oauth2 host) or via the OIDC_SERVER_URL (multiple 'realms' for keycloak)
def issuer_verifier_key(id_jwt: str | bytes, key_master: KeyMaster):
    oidc_host = _get_single_auth_host()
    if oidc_host:
        discovery_base = os.environ.get("OIDC_DISCOVERY_BASE_URL")
        return jwt_verifier_key(oidc_host, discovery_base, id_jwt)
    keycloak_host = _get_keycloak_host()
    if keycloak_host:
        return fetch_realm_key_by_jwt(keycloak_host, id_jwt, key_master)
    raise UnauthorizedError("Issuer Invalid")


def authorized_v2(public_key: PublicKeyTypes, auth_token: str | bytes) -> dict:
    try:
        decoded = jwt.decode(
            auth_token,
            public_key,
            algorithms=["RS256", "ES256", "ES384", "ES512"],
            leeway=leeway,
            options={"verify_aud": False},
        )
    except jwt.exceptions.PyJWTError as e:
        decoded = jwt.decode(
            # This could be an access_token or refresh_token
            auth_token,
            options={"verify_signature": False, "verify_aud": False},
            algorithms=["RS256", "ES256", "ES384", "ES512"],
        )
        logger.warning(
            "Unverifiable claims [%s] found in [%s], public_key=[%s]",
            decoded,
            auth_token,
            public_key,
        )
        raise UnauthorizedError("Not authorized") from e
    return decoded
