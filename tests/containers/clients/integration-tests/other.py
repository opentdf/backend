import argparse
import json
import logging
import os
import sys

from opentdf import TDFClient, NanoTDFClient, OIDCCredentials, LogLevel, TDFStorageType

logger = logging.getLogger("xtest")
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)


def no_tdf_claims(client_id, client_secret, org_name, oidc_endpoint, kas_endpoint):
    oidc_creds = OIDCCredentials()
    oidc_creds.set_client_credentials_client_secret(
        client_id=client_id,
        client_secret=client_secret,
        organization_name=org_name,
        oidc_endpoint=oidc_endpoint,
    )

    client = NanoTDFClient(oidc_credentials=oidc_creds, kas_url=kas_endpoint)

    plain_text = "testing123"
    sampleStringStorageNano = TDFStorageType()
    sampleStringStorageNano.set_tdf_storage_string_type(plain_text)
    nan_tdf_data = client.encrypt_data(sampleStringStorageNano)

    sampleEncryptedStringStorageNano = TDFStorageType()
    sampleEncryptedStringStorageNano.set_tdf_storage_string_type(nan_tdf_data)

    try:
        decrypted_plain_text = client.decrypt_data(sampleEncryptedStringStorageNano)
    except Exception as e:
        if "Claims absent" not in str(e) or "401" not in str(e):
            raise Exception("Test without tdf_claims failed with wrong error")
        else:
            logger.info("Test without tdf_claims PASSED")
    else:
        raise Exception("Test without tdf_claims succeeded but should have failed")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--kasEndpoint", help="KAS endpoint")
    parser.add_argument("--oidcEndpoint", help="OIDC endpoint")
    parser.add_argument("--auth", help="ORGANIZATION_NAME:CLIENT_ID:CLIENT_SECRET")

    args = parser.parse_args()

    auth = args.auth.split(":")

    no_tdf_claims(auth[1], auth[2], auth[0], args.oidcEndpoint, args.kasEndpoint)


if __name__ == "__main__":
    main()
