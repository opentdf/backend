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
kc_internal_url = os.getenv("KEYCLOAK_INTERNAL_URL", "http://keycloakx-http/auth").rstrip("/")


def createAttributes(attribute_host, preloaded_attributes, authToken):
    loc = f"{attribute_host}/definitions/attributes"
    for definition in preloaded_attributes:
        q_params = {'name': definition['name'], 'authority': definition['authority']}
        # Look up existing attrs by guaranteed-unique NS/authority combo
        # to decide if we should POST (not there) or PUT (already there)
        get_response = requests.get(loc, headers={"Authorization": f"Bearer {authToken}"}, params=q_params)
        # POST - add new
        if get_response.status_code == 404 or (get_response.status_code == 200 and not get_response.json()) :
            logger.info(f"Adding attribute definition {definition}")
            http_call = requests.post
            
        # PUT - update existing
        elif get_response.status_code < 400:
            logger.info(f"Updating attribute definition {definition}")
            http_call = requests.put

        else:
            # catch and weird codes from attribtues service
            logger.error(
                "Unexpected code [%s] from attributes service when attempting to GET attribute definition! [%s]",
                get_response.status_code,
                get_response.text,
                exc_info=True,
            )
            exit(1)

        logger.debug("Using auth JWT: [%s]", authToken)
        response = http_call(
            loc,
            json=definition,
            headers={"Authorization": f"Bearer {authToken}"},
        )
        if response.status_code != 200:
            logger.error(
                "Unexpected code [%s] from attributes service! [%s]",
                response.status_code,
                response.text,
                exc_info=True,
            )
            exit(1)
        else:
            logger.info("Attribute created/updated successfully")


def createAuthorities(attribute_host, preloaded_authorities, authToken):
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


def createPreloaded(keycloak_admin, realm, keycloak_auth_url,
     preloaded_authorities, preloaded_attributes):
    attribute_clientid = os.getenv("ATTRIBUTES_CLIENT_ID")
    attribute_username = os.getenv("ATTRIBUTES_USERNAME")
    attribute_password = os.getenv("ATTRIBUTES_PASSWORD")
    attribute_host = os.getenv("ATTRIBUTE_AUTHORITY_HOST", "http://opentdf-attributes:4020").rstrip("/")

    keycloak_openid = KeycloakOpenID(
        server_url=keycloak_auth_url,
        client_id=attribute_clientid,
        realm_name=realm,
    ) 

    authToken = keycloak_openid.token(attribute_username, attribute_password)

    # Create authorities
    if preloaded_authorities is not None:
        createAuthorities(
            attribute_host, preloaded_authorities, authToken["access_token"]
        )
    # Create attributes
    if preloaded_attributes is not None:
        createAttributes(
            attribute_host, preloaded_attributes, authToken["access_token"]
        )


def attributes_bootstrap():
    username = os.getenv("keycloak_admin_username")
    password = os.getenv("keycloak_admin_password")
    keycloak_auth_url = kc_internal_url + "/"
    attribute_realm = os.getenv("ATTRIBUTES_REALM")

    keycloak_admin = KeycloakAdmin(
        server_url=keycloak_auth_url,
        username=username,
        password=password,
        realm_name=attribute_realm,
        user_realm_name="master",
    )

    # Preloaded authorities
    try:
        with open("/etc/virtru-config/authorities.yaml") as f:
            preloaded_authorities = yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning("Not found: /etc/virtru-config/authorities.yaml", exc_info=1)
        preloaded_authorities = None

    # Preloaded attributes
    try:
        with open("/etc/virtru-config/attributes.yaml") as f:
            preloaded_attributes = yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning("Not found: /etc/virtru-config/attributes.yaml", exc_info=1)
        preloaded_attributes = None

    #TDF
    createPreloaded(
        keycloak_admin, attribute_realm, keycloak_auth_url, preloaded_authorities, preloaded_attributes
    )

    return True
