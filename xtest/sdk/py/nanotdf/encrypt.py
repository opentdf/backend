import json
import logging
import os
import sys

from opentdf import TDFClient, NanoTDFClient, OIDCCredentials, LogLevel

logger = logging.getLogger("xtest")
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)


def main():
    stage, source, target, owner = sys.argv[1:5]
    attributes = sys.argv[8] if sys.argv[7] == "--attrs" else ""

    with open("config-oss.json") as config_file:
        config = json.load(config_file)

    tier = config[stage]
    eas = tier.get("entityObjectEndpoint", None) or tier.get("easEndpoint", None)
    logger.info("EAS url is: %s", eas)
    for s in ["/v1/entity_object", "/api/entityobject"]:
        if eas.endswith(s):
            eas = eas[: -len(s)]
            break
    if attributes:
        # based on alice_1234 - assuming she is owner
        iterations = {
            "No Attributes": [],
            "Success Attributes": [
                "http://example.com/attr/language/value/urduTest",
                "http://example.com/attr/language/value/frenchTest",
            ],
            "Failing Attributes": [
                "http://example.com/attr/language/value/urduTest",
                "http://example.com/attr/language/value/germanTest",
            ],
        }
        encrypt_attrs = iterations[attributes]
    else:
        encrypt_attrs = []

    encrypt_file(source, target, owner, eas, encrypt_attrs)


def encrypt_file(source, target, owner, eas, attrs):
    logger.info(
        "Source: %s, Target: %s, owner: %s, eas: %s", source, target, owner, eas
    )
    oidc_creds = OIDCCredentials()
    oidc_creds.set_client_credentials(
        client_id="tdf-client",
        client_secret="123-456",
        organization_name="tdf",
        oidc_endpoint=OIDC_ENDPOINT,
    )

    nano_tdf_client = NanoTDFClient(oidc_credentials=oidc_creds, kas_url=KAS_URL)
    nanotdf_client.enable_console_logging(LogLevel.Info)

    logger.info("Encrypting with data attributes: [%s] as file: [%s]", attrs, target)
    nano_tdf_client.with_data_attributes(attrs)
    nano_tdf_client.encrypt_file(source, target)


if __name__ == "__main__":
    main()
