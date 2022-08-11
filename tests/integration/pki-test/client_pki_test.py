import os
import sys
from opentdf import TDFClient, NanoTDFClient, OIDCCredentials, LogLevel

# encrypt the file and apply the policy on tdf file and also decrypt.
OIDC_ENDPOINT = "https://keycloak-http:65432"
KAS_URL = "http://localhost:65432/api/kas"

try:
    curr_dir = os.path.dirname(__file__)

    oidc_creds = OIDCCredentials()
    oidc_creds.set_client_credentials_pki(
        client_id="client_x509",
        client_key_file_name=os.path.abspath(os.path.join(curr_dir, "../../../certs/john.doe.key")),
        client_cert_file_name=os.path.abspath(os.path.join(curr_dir, "../../../certs/john.doe.cer")),
        certificate_authority=os.path.abspath(os.path.join(curr_dir, "../../../certs/rootca_kc.crt")),
        organization_name="tdf-pki",
        oidc_endpoint=OIDC_ENDPOINT
    )

    client = TDFClient(oidc_credentials=oidc_creds, kas_url=KAS_URL)
    client.enable_console_logging(LogLevel.Debug)

    # Plain text
    plain_text = "openTDF - Easily Protect Data Wherever It’s Created or Shared"

    tdf_data = client.encrypt_string(plain_text)
    decrypted_plain_text = client.decrypt_string(tdf_data)

    if plain_text == decrypted_plain_text:
        print("TDF3 zip format Encrypt/Decrypt is successful!!")
    else:
        print("Error: TDF3 zip format Encrypt/Decrypt failed!!")

except:
    print("Unexpected error: %s" % sys.exc_info()[0])
    raise

