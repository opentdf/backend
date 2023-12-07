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
    """Validate a dpop header, when present.

    Returns True if the dpop was present and validated. Throws UnauthorizedError
    if DPoP or OIDC are required and fail, or if DPoP is present but invalid.
    Returns False if either DPoP is ignored or no auth is requested.
    """
    auth_header = request.headers.get("authorization", None)
    
    if not auth_header:
        if do_oidc:
            raise UnauthorizedError("Missing auth header")
        logger.debug("Missing auth header")
        return False
    bearer, _, id_jwt = auth_header.partition(" ")
    logger.info("id_jwt: [%s], dpop: [%s]", id_jwt, dpop)
    if bearer != "Bearer" or not looks_like_jwt(id_jwt):
        if do_oidc:
            raise UnauthorizedError("Invalid auth header")
        return False
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
        return False
    if dpop and not cnf:
        logger.warning(
            "DPoP found but unconfirmed [%s] not referenced from [%s]", dpop, id_jwt
        )
        return False
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
        m = request.method
        u = request.url
    except Exception as e:
        raise UnauthorizedError("Invalid JWT") from e

    # workaround for starlette request.url not including ingress path
    htu_no_ingress = htu.replace("/api/kas", "")
    if m != htm or u != htu_no_ingress:
        logger.warning("Invalid DPoP htm:[%s] htu:[%s] != m:[%s]", htm, htu_no_ingress, m, u)
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
    logger.debug("DPoP Validated!")
    return True

{"asctime": "2023-12-05 21:58:30,432", "levelname": "WARNING", "module": "dpop", "lineno": 63, "message": "scope: {
 'wsgi_environ': {'wsgi.errors': <gunicorn.http.wsgi.WSGIErrorsWrapper object at 0x7f3b29988a90>, 'wsgi.version': (1, 0), 'wsgi.multithread': False, 'wsgi.multiprocess': False, 'wsgi.run_once': False, 
                  wsgi.file_wrapper': <class 'gunicorn.http.wsgi.FileWrapper'>, 'wsgi.input_terminated': True, 'SERVER_SOFTWARE': 'gunicorn/20.1.0', 'wsgi.input': <gunicorn.http.body.Body object at 0x7f3b29988700>, 
                  'gunicorn.socket': <socket.socket fd=12, family=AddressFamily.AF_INET, type=SocketKind.SOCK_STREAM, proto=0, laddr=('172.17.0.10', 8000), raddr=('172.17.0.2', 49150)>, 
                  'REQUEST_METHOD': 'POST', 'QUERY_STRING': '', 'RAW_URI': '/v2/rewrap', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'ingress-nginx-controller', 'HTTP_X_REQUEST_ID': '173802d325e785a285e824dc864dae7b', 
                  'HTTP_X_REAL_IP': '172.17.0.1', 'HTTP_X_FORWARDED_FOR': '172.17.0.1', 'HTTP_X_FORWARDED_HOST': 'ingress-nginx-controller', 'HTTP_X_FORWARDED_PORT': '80', 'HTTP_X_FORWARDED_PROTO': 'http', 'HTTP_X_FORWARDED_SCHEME': 'http', 
                  'HTTP_X_SCHEME': 'http', 'CONTENT_LENGTH': '975', 'CONTENT_TYPE': 'application/json', 'HTTP_VIRTRU_NTDF_VERSION': '0.0.1', 'HTTP_AUTHORIZATION': '***', 'HTTP_DPOP': '***', 'HTTP_ACCEPT': '*/*', 'HTTP_ACCEPT_LANGUAGE': '*', 'HTTP_SEC_FETCH_MODE': 'cors', 'HTTP_USER_AGENT': 'node', 'HTTP_CACHE_CONTROL': 'max-age=0', 'HTTP_ACCEPT_ENCODING': 'gzip, deflate', 'wsgi.url_scheme': 'http', 'REMOTE_ADDR': '172.17.0.2', 'REMOTE_PORT': '49150', 'SERVER_NAME': '0.0.0.0', 'SERVER_PORT': '8000', 
                  'PATH_INFO': '/v2/rewrap', 'SCRIPT_NAME': ''}, 'type': 'http', 'asgi': {'version': '3.0', 'spec_version': '3.0'}, 'http_version': '1.1', 'method': 'POST', 'scheme': 'http', 'path': '/v2/rewrap', 'query_string': b'', 'root_path': '', 'client': ('172.17.0.2', 49150), 'server': ('0.0.0.0', 8000), 'headers': [(b'host', b'ingress-nginx-controller'), (b'x-request-id', b'173802d325e785a285e824dc864dae7b'), (b'x-real-ip', b'172.17.0.1'), (b'x-forwarded-for', b'172.17.0.1'), (b'x-forwarded-host', b'ingress-nginx-controller'), (b'x-forwarded-port', b'80'), (b'x-forwarded-proto', b'http'), (b'x-forwarded-scheme', b'http'), (b'x-scheme', b'http'), (b'virtru-ntdf-version', b'0.0.1'), (b'authorization', b'***'), (b'dpop', b'***'), (b'accept', b'*/*'), (b'accept-language', b'*'), (b'sec-fetch-mode', b'cors'), (b'user-agent', b'node'), (b'cache-control', b'max-age=0'), (b'accept-encoding', b'gzip, deflate'), (b'content-length', b'975'), (b'content-type', b'application/json')], 'app': <connexion.middleware.main.ConnexionMiddleware object at 0x7f3b29ec0b50>, 
                  'starlette.exception_handlers': ({<class 'starlette.exceptions.HTTPException'>: <function ExceptionMiddleware.http_exception at 0x7f3b29aad2d0>, <class 'starlette.exceptions.WebSocketException'>: <bound method ExceptionMiddleware.websocket_exception of <connexion.middleware.exceptions.ExceptionMiddleware object at 0x7f3b2a2cf0a0>>, <class 'connexion.exceptions.ProblemException'>: <function ExceptionMiddleware.problem_handler at 0x7f3b2ca97b50>, <class 'Exception'>: <function ExceptionMiddleware.common_error_handler at 0x7f3b298c3910>}, {}), 'path_params': {}, 'extensions': {'connexion_routing': {'api_base_path': '', 'operation_id': 'tdf3_kas_core.web.rewrap.rewrap_v2'}}}"}