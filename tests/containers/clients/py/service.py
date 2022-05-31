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

    authorization_endpoint = args.oidcEndpoint + '/auth/realms/' + auth[0] + '/protocol/openid-connect/auth'
    print(authorization_endpoint)
    uri, state = client.create_authorization_url(authorization_endpoint, response_type='token')
    print(uri)

    token_endpoint = args.oidcEndpoint + '/auth/realms/' + auth[0] + '/protocol/openid-connect/token'
    print(token_endpoint)
    token = client.fetch_token(token_endpoint, grant_type='client_credentials')
    print(token)
    auth = OAuth2Auth(token)
    response = requests.get(args.attributesEndpoint, auth=auth)
    print(response.text)
    assert response.ok
    # Authorities
    authorities_endpoint = f'{args.attributesEndpoint}/authorities'
    print(authorities_endpoint)
    response = requests.get(authorities_endpoint, auth=auth)
    print(response.text)
    assert response.ok
    # Authorities Create
    authority = {
        "authority": "https://opentdf.io"
    }
    response = requests.post(authorities_endpoint, json=authority, auth=auth)
    print(response.status_code)
    assert response.ok or response.status_code == 400
    # Attributes Definitions
    attributes_definitions_endpoint = f'{args.attributesEndpoint}/definitions/attributes'
    print(attributes_definitions_endpoint)
    response = requests.get(attributes_definitions_endpoint, auth=auth)
    print(response.text)
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
    print(response.status_code)
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
    print(response.status_code)
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
    print(response.status_code)
    assert response.ok
    # Attributes Definitions Get
    response = requests.get(attributes_definitions_endpoint,
                            params={"authority": "https://opentdf.io","name": "SocialGrade"}, auth=auth)
    print(response.text)
    assert response.ok
    assert "C1" in response.text
    response = requests.get(attributes_definitions_endpoint,
                            params={"authority": "https://opentdf.io","name": "IntellectualProperty"}, auth=auth)
    print(response.text)
    assert response.ok
    assert "C1" not in response.text


if __name__ == "__main__":
    main()
