import argparse
import requests
from authlib.integrations.requests_client import OAuth2Session, OAuth2Auth


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--attributesEndpoint", help="attributes endpoint")
    parser.add_argument("--oidcEndpoint", help="OIDC endpoint")
    parser.add_argument("--auth", help="ORGANIZATION_NAME:CLIENT_ID:CLIENT_SECRET")

    args = parser.parse_args()

    auth = args.auth.split(":")

    scope = 'openid email profile'
    client = OAuth2Session(auth[1], auth[2], scope=scope)

    token_endpoint = args.oidcEndpoint + '/auth/realms/' + auth[0] + '/protocol/openid-connect/token'
    token = client.fetch_token(token_endpoint, grant_type='client_credentials')
    auth = OAuth2Auth(token)
    response = requests.get(args.attributesEndpoint, auth=auth)
    assert response.ok
    # Authorities
    authorities_endpoint = f'{args.attributesEndpoint}/authorities'
    response = requests.get(authorities_endpoint, auth=auth)
    assert response.ok
    # Authorities Create
    authority = {
        "authority": "https://opentdf.io"
    }
    response = requests.post(authorities_endpoint, json=authority, auth=auth)
    assert response.ok or response.status_code == 400
    # Attributes Definitions
    attributes_definitions_endpoint = f'{args.attributesEndpoint}/definitions/attributes'
    response = requests.get(attributes_definitions_endpoint, auth=auth)
    assert response.ok
    # Attributes Definitions Create
    attribute_ip = {
        "authority": "https://opentdf.io",
        "name": "IntellectualProperty",
        "rule": "hierarchy",
        "state": "published",
        "order": [
            "TradeSecret",
            "Proprietary",
            "BusinessSensitive",
            "Open"
        ]
    }
    response = requests.post(attributes_definitions_endpoint, json=attribute_ip, auth=auth)
    assert response.ok or response.status_code == 400
    attribute_sg = {
        "authority": "https://opentdf.io",
        "name": "SocialGrade",
        "rule": "hierarchy",
        "state": "published",
        "order": [
            "A",
            "B",
            "C",
            "D",
            "F"
        ]
    }
    response = requests.post(attributes_definitions_endpoint, json=attribute_sg, auth=auth)
    assert response.ok or response.status_code == 400
    # Attributes Definitions Update
    attribute_sg = {
        "authority": "https://opentdf.io",
        "name": "SocialGrade",
        "rule": "hierarchy",
        "state": "published",
        "order": [
            "A",
            "B",
            "C1",
            "C2",
            "D",
            "F"
        ]
    }
    response = requests.put(attributes_definitions_endpoint, json=attribute_sg, auth=auth)
    assert response.ok
    # Attributes Definitions Get
    response = requests.get(attributes_definitions_endpoint,
                            params={"authority": "https://opentdf.io","name": "SocialGrade"}, auth=auth)
    assert response.ok
    assert "C1" in response.text
    response = requests.get(attributes_definitions_endpoint,
                            params={"authority": "https://opentdf.io","name": "IntellectualProperty"}, auth=auth)
    assert response.ok
    assert "C1" not in response.text
    # Attribute rule endpoint for KAS
    attributes_names_endpoint = f'{args.attributesEndpoint}/v1/attrName'
    response = requests.post(attributes_names_endpoint)
    assert response.ok
    assert "SocialGrade" in response.text
    assert "IntellectualProperty" in response.text


if __name__ == "__main__":
    main()
