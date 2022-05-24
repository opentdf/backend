import os
import logging
import requests
import yaml
from keycloak import KeycloakAdmin, KeycloakOpenID


logging.basicConfig()
logger = logging.getLogger("keycloak_bootstrap")
logger.setLevel(logging.DEBUG)

# This is the only URL this file should ever need -
# The URL stuff inside the cluster (aka this bootstrap job) will use to resolve keycloak (private, non-browser clients)
kc_internal_url = os.getenv("KEYCLOAK_INTERNAL_URL", "http://keycloak-http")


def createAttributes(keycloak_admin, attribute_host, preloaded_attributes, authToken):
    loc = f"{attribute_host}/definitions/attributes"
    get_response = requests.get(loc, headers={"Authorization": f"Bearer {authToken}"})
    for definition in preloaded_attributes:
        if definition not in get_response.json():
            logger.info(f"Adding attribute definition {definition}")
            logger.debug("Using auth JWT: [%s]", authToken)

            response = requests.post(
                loc,
                json=definition,
                headers={"Authorization": f"Bearer {authToken}"},
            )
            if response.status_code != 200:
                logger.error(
                    "Unexpected code [%s] from attributes service when attempting to create attribute definition! [%s]",
                    response.status_code,
                    response.text,
                    exc_info=True,
                )
                exit(1)


def createAuthorities(keycloak_admin, attribute_host, preloaded_authorities, authToken):
   loc = f"{attribute_host}/authorities"
   get_response = requests.get(loc, headers={"Authorization": f"Bearer {authToken}"})
   for authority in preloaded_authorities:
        if authority not in get_response.json():
            logger.info(f"Adding authority {authority}")
            logger.debug("Using auth JWT: [%s]", authToken)

            response = requests.post(
                loc,
                json={"authority": authority},
                headers={"Authorization": f"Bearer {authToken}"},
            )
            if response.status_code != 200:
                logger.error(
                    "Unexpected code [%s] from attributes service when attempting to create authority! [%s]",
                    response.status_code,
                    response.text,
                    exc_info=True,
                )
                exit(1)


def createPreloadedForRealm(keycloak_admin, target_realm, keycloak_auth_url, preloaded_authorities, preloaded_attributes):
    logger.info("Creating authorities and attrs for realm: [%s]", target_realm)

    #just using the entitlement creds for now
    attribute_clientid = os.getenv("ENTITLEMENT_CLIENT_ID")
    attribute_username = os.getenv("ENTITLEMENT_USERNAME")
    attribute_password = os.getenv("ENTITLEMENT_PASSWORD")
    attribute_host = os.getenv("ATTRIBUTE_AUTHORITY_HOST", "http://opentdf-attributes:4020")

    keycloak_openid = KeycloakOpenID(
        # NOTE: `realm_name` IS NOT == `target_realm` here
        # Target realm is the realm you're querying users from keycloak for
        # `realm_name` is the realm you're using to get a token to talk to entitlements with
        # They are not the same.
        server_url=keycloak_auth_url,
        client_id=attribute_clientid,
        realm_name="tdf",
    )  # Attributes endpoint always uses `tdf` realm client creds
    authToken = keycloak_openid.token(attribute_username, attribute_password)

    # Create authorities
    if preloaded_authorities is not None:
        createAuthorities(
            keycloak_admin, attribute_host, preloaded_authorities, authToken["access_token"]
        )
    # Create attributes
    if preloaded_attributes is not None:
        createAttributes(
            keycloak_admin, attribute_host, preloaded_attributes, authToken["access_token"]
        )


def attributes_bootstrap():
    username = os.getenv("keycloak_admin_username")
    password = os.getenv("keycloak_admin_password")
    keycloak_auth_url = kc_internal_url + "/auth/"

    keycloak_admin_tdf = KeycloakAdmin(
        server_url=keycloak_auth_url,
        username=username,
        password=password,
        realm_name="tdf",
        user_realm_name="master",
    )

    # Preloaded authorities
    try:
        with open("/etc/virtru-config/authorities.yaml") as f:
            preloaded_authorities = yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning("Not found: /etc/virtru-config/authorities.yaml", exc_info=1)

    # Preloaded attributes
    try:
        with open("/etc/virtru-config/attributes.yaml") as f:
            preloaded_attributes = yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning("Not found: /etc/virtru-config/attributes.yaml", exc_info=1)

    #TDF
    createPreloadedForRealm(
        keycloak_admin_tdf, "tdf", keycloak_auth_url, preloaded_authorities, preloaded_attributes
    )

    keycloak_admin_tdf_pki = KeycloakAdmin(
        server_url=keycloak_auth_url,
        username=username,
        password=password,
        realm_name="tdf-pki",
        user_realm_name="master",
    )

    #PKI
    createPreloadedForRealm(
        keycloak_admin_tdf_pki, "tdf-pki", keycloak_auth_url, preloaded_authorities, preloaded_attributes
    )

    return True