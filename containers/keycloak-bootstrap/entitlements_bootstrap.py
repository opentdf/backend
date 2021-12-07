import os
import json
import logging
import requests
from keycloak import KeycloakAdmin
from keycloak import KeycloakOpenID


logging.basicConfig()
logger = logging.getLogger("keycloak_bootstrap")
logger.setLevel(logging.DEBUG)

# tdf_realm_user_attrmap = {
#     'tdf-user': [
#         "https://example.com/attr/Classification/value/C",
#         "https://example.com/attr/COI/value/PRX"
#     ],
#     'user1': [
#         "https://example.com/attr/Classification/value/S",
#         "https://example.com/attr/COI/value/PRX"
#     ],
#     'bob_1234': [
#         "https://example.com/attr/Classification/value/C",
#         "https://example.com/attr/COI/value/PRC"
#     ],
#     'alice_1234': [
#         "https://example.com/attr/Classification/value/C",
#         "https://example.com/attr/COI/value/PRD"
#     ]
# }

# tdf_realm_client_attrmap = {
#     'tdf-client': [
#         "https://example.com/attr/Classification/value/S",
#         "https://example.com/attr/COI/value/PRX"
#     ],
#     'browsertest': [
#         "https://example.com/attr/Classification/value/C",
#         "https://example.com/attr/COI/value/PRA"
#     ],
#     'service-account-tdf-client': [
#         "https://example.com/attr/Classification/value/C",
#         "https://example.com/attr/COI/value/PRB"
#     ],
#     'client_x509': [
#         "https://example.com/attr/Classification/value/S",
#         "https://example.com/attr/COI/value/PRX"
#     ],
#     'dcr-test': [
#         "https://example.com/attr/Classification/value/C",
#         "https://example.com/attr/COI/value/PRF"
#     ]
# }

def insertAttrsForUsers(keycloak_admin, entitlement_host, user_attr_map, authToken):
    users = keycloak_admin.get_users()
    logger.info(f"Got users: {users}")

    for user in users:
        if user['username'] in user_attr_map:
            logger.info("Inserting attributes for user: " + user['username'])
            logger.debug(f"Using auth JWT: {authToken}")

            for attr in user_attr_map[user['username']]:
                response = requests.put(
                    f"{entitlement_host}/v1/entity/{user['id']}/attribute",
                    json=[attr], headers={'Authorization': f"Bearer {authToken}"})
                if response.status_code != 200:
                    print(response.text)
                    exit(1)


def insertAttrsForClients(keycloak_admin, entitlement_host, client_attr_map, authToken):
    clients = keycloak_admin.get_clients()

    for client in clients:
        if client['clientId'] in client_attr_map:
            logger.info("Inserting attributes for clientId: " + client['clientId'])

            for attr in client_attr_map[client['clientId']]:
                response = requests.put(
                    f"{entitlement_host}/v1/entity/{client['id']}/attribute",
                    json=[attr], headers={'Authorization': f"Bearer {authToken}"})
                if response.status_code != 200:
                    print(response.text)
                    exit(1)

def insertEntitlementAttrsForRealm(keycloak_admin, realm, keycloak_auth_url, entity_attrmap):
    logger.info(f"Inserting attrs for realm: {realm}")
    entitlement_clientid = os.getenv("ENTITLEMENT_CLIENT_ID")
    entitlement_username = os.getenv("ENTITLEMENT_USERNAME")
    entitlement_password = os.getenv("ENTITLEMENT_PASSWORD")
    entitlement_host = os.getenv("ENTITLEMENT_HOST", "http://opentdf-entitlements:4030")

    keycloak_openid = KeycloakOpenID(server_url=keycloak_auth_url,
                    client_id=entitlement_clientid,
                    realm_name="tdf") #Entitlements endpoint always uses `tdf` realm client creds
    authToken = keycloak_openid.token(entitlement_username, entitlement_password)

    insertAttrsForUsers(keycloak_admin, entitlement_host, entity_attrmap, authToken['access_token'])
    insertAttrsForClients(keycloak_admin, entitlement_host, entity_attrmap, authToken['access_token'])
    logger.info(f"Finished inserting attrs for realm: {realm}")

def entitlements_bootstrap():
    username = os.getenv("keycloak_admin_username")
    password = os.getenv("keycloak_admin_password")

    keycloak_hostname = os.getenv("keycloak_hostname", "http://localhost:8080")
    keycloak_auth_url = keycloak_hostname + "/auth/"

    keycloak_admin_tdf = KeycloakAdmin(
        server_url=keycloak_auth_url,
        username=username,
        password=password,
        realm_name="tdf",
        user_realm_name="master",
    )

    keycloak_admin_tdf_pki = KeycloakAdmin(
        server_url=keycloak_auth_url,
        username=username,
        password=password,
        realm_name="tdf-pki",
        user_realm_name="master",
    )

    # Contains a map of `entities` to attributes we want to preload
    # Entities can be clients or users, doesn't matter
    with open('/etc/virtru-config/entitlements.json') as f:
        entity_attrmap = json.load(f)

    insertEntitlementAttrsForRealm(keycloak_admin_tdf, "tdf", keycloak_auth_url, entity_attrmap)
    insertEntitlementAttrsForRealm(keycloak_admin_tdf_pki, "tdf-pki", keycloak_auth_url, entity_attrmap)

    return True
