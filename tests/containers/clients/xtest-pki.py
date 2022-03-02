import sys
from opentdf import TDFClient, NanoTDFClient, OIDCCredentials, LogLevel

# encrypt the file and apply the policy on tdf file and also decrypt.
OIDC_ENDPOINT = "https://opentdf.local:4566"
KAS_URL = "http://localhost:65432/kas"

try:

    oidc_creds.set_client_credentials_pki(
        client_id="client_x509",
        client_key_file_name="/Users/mustyantsev/temp/cert/john.doe.key",
        client_cert_file_name="/Users/mustyantsev/temp/cert/john.doe.cer",
        certificate_authority="/Users/mustyantsev/temp/cert/ca.crt",
        organization_name="tdf-pki",
        oidc_endpoint=OIDC_ENDPOINT
    )

    client = TDFClient(oidc_credentials=oidc_creds, kas_url=KAS_URL)
    client.enable_console_logging(LogLevel.Debug)

    # Print subject attributes in claims object
    print(f'The attributes in claims object:{client.subject_attributes()}')

    # Plain text
    plain_text = "openTDF - Easily Protect Data Wherever It’s Created or Shared"

    client.encrypt_file("sample.txt", "sample.txt.tdf")
    client.decrypt_file("sample.txt.tdf", "sample_out_tdf.txt")

    #################################################
    # TDF3 ZIP format - Data API
    #################################################

    tdf_data = client.encrypt_string(plain_text)
    decrypted_plain_text = client.decrypt_string(tdf_data)

    if plain_text == decrypted_plain_text:
        print("TDF3 zip format Encrypt/Decrypt is successful!!")
    else:
        print("Error: TDF3 zip format Encrypt/Decrypt failed!!")

    #################################################
    # TDF3 XML format - File API
    ################################################

    # Set XML format
    client.set_xml_format()

    client.encrypt_file("sample.txt", "sample.txt.xml")
    client.decrypt_file("sample.txt.xml", "sample_out_xml.txt")

    #################################################
    # TDF3 XML format - Data API
    #################################################

    tdf_data = client.encrypt_string(plain_text)
    decrypted_plain_text = client.decrypt_string(tdf_data)

    if plain_text == decrypted_plain_text:
        print("TDF3 xml format Encrypt/Decrypt is successful!!")
    else:
        print("Error: TDF3 xml format Encrypt/Decrypt failed!!")

    #################################################
    # Nano TDF - File API
    ################################################

    # create a nano tdf client.
    nano_tdf_client = NanoTDFClient(oidc_credentials=oidc_creds, kas_url=KAS_URL)
    # nano_tdf_client.enable_console_logging(LogLevel.Trace);
    nano_tdf_client.enable_console_logging(LogLevel.Debug)
    # nano_tdf_client.with_data_attributes(
    #     ["https://example.com/attr/Classification/value/S"]
    # )
    nano_tdf_client.encrypt_file("sample.txt", "sample.txt.ntdf")
    nano_tdf_client.decrypt_file("sample.txt.ntdf", "sample_out.txt")

    #################################################
    # Nano TDF - Data API
    #################################################

    nano_tdf_data = nano_tdf_client.encrypt_string(plain_text)
    # print(nano_tdf_data)
    decrypted_plain_text = nano_tdf_client.decrypt_string(nano_tdf_data)

    if plain_text == decrypted_plain_text.decode("utf-8"):
        print("Nano TDF Encrypt/Decrypt is successful!!")
    else:
        print("Error: Nano TDF Encrypt/Decrypt failed!!")

except:
    print("Unexpected error: %s" % sys.exc_info()[0])
    raise

