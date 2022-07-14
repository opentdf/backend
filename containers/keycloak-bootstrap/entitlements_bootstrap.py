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
kc_internal_url = os.getenv("KEYCLOAK_INTERNAL_URL", "http://keycloak-http").rstrip("/")


def insertAttrsForUsers(keycloak_admin, entitlement_host, user_attr_map, authToken):
    users = keycloak_admin.get_users()
    logger.info(f"Got users: {users}")

    for user in users:
        if user["username"] not in user_attr_map:
            continue
        loc = f"{entitlement_host}/entitlements/{user['id']}"
        attrs = user_attr_map[user["username"]]
        logger.info(
            "Entitling for user: [%s] with [%s] at [%s]", user["username"], attrs, loc
        )
        logger.debug("Using auth JWT: [%s]", authToken)

        for attr in attrs:
            response = requests.post(
                loc,
                json=[attr],
                headers={"Authorization": f"Bearer {authToken}"},
            )
            if response.status_code != 200:
                logger.error(
                    "Unexpected code [%s] from entitlements service when attempting to entitle user! [%s]",
                    response.status_code,
                    response.text,
                    exc_info=True,
                )
                exit(1)


def insertAttrsForClients(keycloak_admin, entitlement_host, client_attr_map, authToken):
    clients = keycloak_admin.get_clients()

    for client in clients:
        if client["clientId"] not in client_attr_map:
            continue
        clientId = client["clientId"]
        loc = f"{entitlement_host}/entitlements/{client['id']}"
        attrs = client_attr_map[clientId]
        logger.info(
            "Entitling for client: [%s] with [%s] at [%s]", clientId, attrs, loc
        )
        logger.debug("Using auth JWT: [%s]", authToken)
        for attr in attrs:
            response = requests.post(
                loc,
                json=[attr],
                headers={"Authorization": f"Bearer {authToken}"},
            )
            if response.status_code != 200:
                logger.error(
                    "Unexpected code [%s] from entitlements service when attempting to entitle client! [%s]",
                    response.status_code,
                    response.text,
                    exc_info=True,
                )
                exit(1)


def insertEntitlementAttrsForRealm(
    keycloak_admin, target_realm, keycloak_auth_url, cliend_id,
    username, password, entity_attrmap
):
    logger.info("Inserting attrs for realm: [%s]", target_realm)
    # entitlement_clientid = os.getenv("ENTITLEMENT_CLIENT_ID")
    # entitlement_username = os.getenv("ENTITLEMENT_USERNAME")
    # entitlement_password = os.getenv("ENTITLEMENT_PASSWORD")
    entitlement_host = os.getenv("ENTITLEMENT_HOST", "http://opentdf-entitlements:4030").rstrip("/")

    keycloak_openid = KeycloakOpenID(
        # NOTE: `realm_name` IS NOT == `target_realm` here
        # Target realm is the realm you're querying users from keycloak for
        # `realm_name` is the realm you're using to get a token to talk to entitlements with
        # They are not the same.
        server_url=keycloak_auth_url,
        client_id=cliend_id,
        realm_name="tdf",
    )  # Entitlements endpoint always uses `tdf` realm client creds
    authToken = keycloak_openid.token(username, password)

    insertAttrsForUsers(
        keycloak_admin, entitlement_host, entity_attrmap, authToken["access_token"]
    )
    insertAttrsForClients(
        keycloak_admin, entitlement_host, entity_attrmap, authToken["access_token"]
    )
    logger.info("Finished inserting attrs for realm: [%s]", target_realm)


def entitlements_bootstrap():
    username = os.getenv("keycloak_admin_username")
    password = os.getenv("keycloak_admin_password")

    keycloak_auth_url = kc_internal_url + "/auth/"

    # Contains a map of `entities` to attributes we want to preload
    # Entities can be clients or users, doesn't matter
    try:
        with open("/etc/virtru-config/entitlements.yaml") as f:
            entitlements = yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning("Not found: /etc/virtru-config/entitlements.yaml", exc_info=1)
        entitlements = {}

    if entitlements:
        for realm in entitlements:
            keycloak_admin_tdf = KeycloakAdmin(
                server_url=keycloak_auth_url,
                username=username,
                password=password,
                realm_name=realm["name"],
                user_realm_name="master",
            )
            insertEntitlementAttrsForRealm(
                keycloak_admin_tdf, realm["name"], keycloak_auth_url, realm["clientId"],
                realm["username"], realm["password"], realm["preloadedClaims"]
            )

    return True
