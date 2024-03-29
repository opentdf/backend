import argparse
import json
import logging
import os
import sys

from opentdf import TDFClient, NanoTDFClient, OIDCCredentials, LogLevel, TDFStorageType

logger = logging.getLogger("xtest")
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)


def decrypt_file(
    client,
    oidc_endpoint,
    kas,
    client_id,
    client_secret,
    org_name,
    nano,
    ct_file,
    rt_file,
):
    logger.info(
        "KAS: %s, OIDC: %s, Client id: %s, Client secret: %s, Org Name: %s, Nano: %s",
        oidc_endpoint,
        kas,
        client_id,
        client_secret,
        org_name,
        str(nano),
    )
    client.enable_console_logging(LogLevel.Info)

    tdfStorage = TDFStorageType()
    tdfStorage.set_tdf_storage_file_type(ct_file)
    client.decrypt_file(tdfStorage, rt_file)

    logger.info("Decrypting file ")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--kasEndpoint", help="KAS endpoint")
    parser.add_argument("--oidcEndpoint", help="OIDC endpoint")
    parser.add_argument("--auth", help="ORGANIZATION_NAME:CLIENT_ID:CLIENT_SECRET")
    parser.add_argument("--rtfile", help="output file name")
    parser.add_argument("--ctfile", help="input file name")
    parser.add_argument("--nano", help="use nano tdf", action="store_true")

    args = parser.parse_args()
    auth = args.auth.split(":")

    oidc_creds = OIDCCredentials()
    oidc_creds.set_client_credentials_client_secret(
        client_id=auth[1],
        client_secret=auth[2],
        organization_name=auth[0],
        oidc_endpoint=args.oidcEndpoint,
    )

    client = (
        NanoTDFClient(oidc_credentials=oidc_creds, kas_url=args.kasEndpoint)
        if args.nano
        else TDFClient(oidc_credentials=oidc_creds, kas_url=args.kasEndpoint)
    )

    decrypt_file(
        client,
        args.kasEndpoint,
        args.oidcEndpoint,
        auth[1],
        auth[2],
        auth[0],
        args.nano,
        args.ctfile,
        args.rtfile,
    )


if __name__ == "__main__":
    main()
