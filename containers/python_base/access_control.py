import logging
import os
from keycloak import KeycloakOpenID

logger = logging.getLogger(__package__)
def add_filter_by_access_control(request):
    authority = get_authority(request)
    return authority

def get_authority(request):
    token = request.headers.get('Authorization').replace('Bearer ', '')
    keycloak_openid = KeycloakOpenID(
        # trailing / is required
        server_url=os.getenv("OIDC_SERVER_URL"),
        client_id=os.getenv("OIDC_CLIENT_ID"),
        realm_name=os.getenv("OIDC_REALM"),
        client_secret_key=os.getenv("OIDC_CLIENT_SECRET"),
        verify=True,
    )

    decoded = keycloak_openid.decode_token(
        token,
        key="",
        options={"verify_signature": False, "verify_aud": False, "exp": True},
    )

    if "orgs_domain" in decoded:
        authority = "https://" + decoded["orgs_domain"]
    else:
        authority = None

    return authority
