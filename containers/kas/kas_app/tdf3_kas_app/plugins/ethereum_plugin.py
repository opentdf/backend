import jwt as jwt

from tdf3_kas_core.abstractions import AbstractRewrapPlugin
from tdf3_kas_core.authorized import looks_like_jwt
from tdf3_kas_core.errors import UnauthorizedError

from containers.kas.kas_core.tdf3_kas_core import Policy


def get_entity_pubkey(access_jwt):
    # grab information out of the token without verifying it.
    decoded_jwt = jwt.decode(
        access_jwt,
        options={"verify_signature": False, "verify_aud": False},
        algorithms=["RS256", "ES256", "ES384", "ES512"],
    )
    print(decoded_jwt)
    return decoded_jwt["entity-pubkey"]


class EthereumPlugin(AbstractRewrapPlugin):
    def update(self, req, res):
        print(req)
        # entity_pubkey from bearer token
        try:
            auth_token = req.context.data["Authorization"]
            bearer, _, idp_jwt = auth_token.partition(" ")
        except KeyError as e:
            raise UnauthorizedError("Missing auth header") from e
        else:
            if bearer != "Bearer" or not looks_like_jwt(idp_jwt):
                raise UnauthorizedError("Invalid auth header")
        entity_pubkey = get_entity_pubkey(idp_jwt)
        print("~~~~~~~~~")
        print(entity_pubkey)
        print("~~~~~~~~~")
        # attributes from policy
        data = req.json()
        decoded_tdf_request = jwt.decode(
            data["signedRequestToken"],
            options={"verify_signature": False, "verify_aud": False},
            algorithms=["RS256", "ES256", "ES384", "ES512"],
        )
        print(decoded_tdf_request)
        canonical_policy = data["policy"]
        original_policy = Policy.construct_from_raw_canonical(canonical_policy)
        print("^^^^^^^^")
        print(original_policy.data_attributes)
        print("^^^^^^^^")
        return req, res
