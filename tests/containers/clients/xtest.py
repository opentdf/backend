#!/usr/bin/env python3

# Evaluate several

import argparse
import filecmp
import logging
import os
import random
import shutil
import string
import subprocess

logger = logging.getLogger("xtest")
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

tmp_dir = "tmp/"

FILE_PATHS = {
    "service": "integration-tests/service.py",
    "other": "integration-tests/other.py",
    "py_encrypt": "py/encrypt.py",
    "py_decrypt": "py/decrypt.py",
}

KAS_ENDPOINT = os.getenv("KAS_ENDPOINT", "http://host.docker.internal:65432/kas")
ATTRIBUTES_ENDPOINT = os.getenv("ATTRIBUTES_ENDPOINT", "http://attributes:4020")
OIDC_ENDPOINT = os.getenv("OIDC_ENDPOINT", "http://host.docker.internal:65432/keycloak")
ORGANIZATION_NAME = "tdf"
CLIENT_ID = "tdf-client"
TEST_CLIENT_1 = "test-client-1"
TEST_CLIENT_2 = "test-client-2"
TEST_CLIENT_3 = "test-client-3" # no mappers
ATTRIBUTES_CLIENT_ID = "tdf-client"
ATTRIBUTES_CLIENT_SECRET = "123-456"
CLIENTS = {
    CLIENT_ID: "123-456",
    TEST_CLIENT_1: "123-456-789",
    TEST_CLIENT_2: "123-456-789",
    TEST_CLIENT_3: "123-456-789",
}
ALL_OF_SUCCESS = ["http://testing123.fun/attr/Language/value/spanish"]
ALL_OF_FAILURE = [
    "http://testing123.fun/attr/Language/value/spanish",
    "http://testing123.fun/attr/Language/value/french",
]
ANY_OF_SUCCESS = [
    "http://testing123.fun/attr/Color/value/green",
    "http://testing123.fun/attr/Color/value/blue",
]
ANY_OF_FAILURE = ["http://testing123.fun/attr/Color/value/blue"]
HIERARCHY_SUCCESS = ["https://example.com/attr/Classification/value/U"]
HIERARCHY_FAILURE = ["https://example.com/attr/Classification/value/TS"]
ATTR_TESTS = {
    "allOf": ALL_OF_SUCCESS,
    "allOf fail": ALL_OF_FAILURE,
    "anyOf": ANY_OF_SUCCESS,
    "anyOf fail": ANY_OF_FAILURE,
    "hierarchy": HIERARCHY_SUCCESS,
    "hierarchy fail": HIERARCHY_FAILURE,
}


def encrypt_web(ct_file, rt_file, attributes=None, client_id=CLIENT_ID, container="tdf3"):
    c = [
        "npx",
        "@opentdf/cli",
        "--log-level",
        "DEBUG",
        "--kasEndpoint",
        KAS_ENDPOINT,
        "--oidcEndpoint",
        f"{OIDC_ENDPOINT}/auth/realms/{ORGANIZATION_NAME}",
        "--auth",
        f"{client_id}:{CLIENTS[client_id]}",
        "--output",
        rt_file,
    ]
    if attributes:
        c += ["--attributes", ",".join(attributes)]
    c += ["encrypt", ct_file]
    logger.info("Invoking subprocess: %s", " ".join(c))
    subprocess.check_call(c)


def decrypt_web(ct_file, rt_file, client_id=CLIENT_ID, container="tdf3"):
    c = [
        "npx",
        "@opentdf/cli",
        "--container",
        container,
        "--log-level",
        "DEBUG",
        "--kasEndpoint",
        KAS_ENDPOINT,
        "--oidcEndpoint",
        f"{OIDC_ENDPOINT}/auth/realms/{ORGANIZATION_NAME}",
        "--auth",
        f"{client_id}:{CLIENTS[client_id]}",
        "--output",
        rt_file,
        "decrypt",
        ct_file,
    ]
    logger.info("Invoking subprocess: %s", " ".join(c))
    subprocess.check_call(c)

def encrypt_web_nano(ct_file, rt_file, client_id=CLIENT_ID):
    encrypt_web_nano(ct_file, rt_file, client_id=client_id, container="nano")

def decrypt_web_nano(ct_file, rt_file, client_id=CLIENT_ID):
    decrypt_web_nano(ct_file, rt_file, client_id=client_id, container="nano")

def encrypt_py_nano(ct_file, rt_file, attributes=None, client_id=CLIENT_ID):
    encrypt_py(ct_file, rt_file, attributes=attributes, nano=True, client_id=client_id)


def decrypt_py_nano(ct_file, rt_file, client_id=CLIENT_ID):
    decrypt_py(ct_file, rt_file, nano=True, client_id=client_id)


def service():
    c = [
        "python3",
        FILE_PATHS["service"],
        "--attributesEndpoint",
        ATTRIBUTES_ENDPOINT,
        "--oidcEndpoint",
        OIDC_ENDPOINT,
        "--auth",
        f"{ORGANIZATION_NAME}:{ATTRIBUTES_CLIENT_ID}:{ATTRIBUTES_CLIENT_SECRET}",
    ]
    logger.info("Invoking subprocess: %s", " ".join(c))
    subprocess.check_call(c)

def other_integration_tests():
    c = [
        "python3",
        FILE_PATHS["other"],
        "--kasEndpoint",
        KAS_ENDPOINT,
        "--oidcEndpoint",
        OIDC_ENDPOINT,
        "--auth",
        f"{ORGANIZATION_NAME}:{TEST_CLIENT_3}:{CLIENTS[TEST_CLIENT_3]}",
    ]
    logger.info("Invoking subprocess: %s", " ".join(c))
    subprocess.check_call(c)

def encrypt_py(pt_file, ct_file, nano=False, attributes=None, client_id=CLIENT_ID):
    c = [
        "python3",
        FILE_PATHS["py_encrypt"],
        "--kasEndpoint",
        KAS_ENDPOINT,
        "--oidcEndpoint",
        OIDC_ENDPOINT,
        "--auth",
        f"{ORGANIZATION_NAME}:{client_id}:{CLIENTS[client_id]}",
        "--ctfile",
        ct_file,
        "--ptfile",
        pt_file,
    ]
    if attributes:
        c += ["--attributes", ",".join(attributes)]
    if nano:
        c.append("--nano")
    logger.info("Invoking subprocess: %s", " ".join(c))
    subprocess.check_call(c)


def decrypt_py(ct_file, rt_file, nano=False, client_id=CLIENT_ID):
    c = [
        "python3",
        FILE_PATHS["py_decrypt"],
        "--kasEndpoint",
        KAS_ENDPOINT,
        "--oidcEndpoint",
        OIDC_ENDPOINT,
        "--auth",
        f"{ORGANIZATION_NAME}:{client_id}:{CLIENTS[client_id]}",
        "--rtfile",
        rt_file,
        "--ctfile",
        ct_file,
    ]
    if nano:
        c.append("--nano")
    logger.info("Invoking subprocess: %s", " ".join(c))
    subprocess.check_call(c)


def setup():
    teardown()
    os.makedirs(tmp_dir)


def teardown():
    dirs = [tmp_dir]
    for thedir in dirs:
        if os.path.isdir(thedir):
            shutil.rmtree(thedir)


def main():
    parser = argparse.ArgumentParser(
        description="Cross-test various TDF libraries and services."
    )
    parser.add_argument(
        "--large",
        help="Use a 5 GiB File; doesn't work with nano sdks",
        action="store_true",
    )
    parser.add_argument(
        "--no-teardown", action="store_true", help="don't delete temp files"
    )
    parser.add_argument(
        "--attrtest", action="store_true", help="Include attribute tests"
    )
    args = parser.parse_args()

    service_test = set([service])

    other_integration = set([other_integration_tests])

    tdf3_sdks_to_encrypt = set([encrypt_web, encrypt_py])
    tdf3_sdks_to_decrypt = set([decrypt_web, decrypt_py])

    nano_sdks_to_encrypt = set([encrypt_web_nano, encrypt_py_nano])
    nano_sdks_to_decrypt = set([decrypt_web_nano, decrypt_py_nano])

    logger.info("--- main")
    setup()

    pt_file = gen_pt(large=args.large)
    nano_pt_file = pt_file if not args.large else gen_pt(large=False)
    failed = []
    try:
        logger.info("SERVICES TESTS:")
        failed += run_service_tests(service_test)
        logger.info("OTHER INTEGRATION TESTS:")
        failed += run_other_tests(other_integration)
        logger.info("TDF3 TESTS:")
        failed += run_cli_tests(tdf3_sdks_to_encrypt, tdf3_sdks_to_decrypt, pt_file)
        logger.info("NANO TESTS:")
        failed += run_cli_tests(
            nano_sdks_to_encrypt, nano_sdks_to_decrypt, nano_pt_file
        )
        if args.attrtest:
            logger.info("TDF3 ATTRIBUTE TESTS:")
            failed += run_attribute_tests(
                tdf3_sdks_to_encrypt, tdf3_sdks_to_decrypt, pt_file
            )
            logger.info("NANO ATTRIBUTE TESTS:")
            failed += run_attribute_tests(
                nano_sdks_to_encrypt, nano_sdks_to_decrypt, nano_pt_file
            )
    finally:
        if not args.no_teardown:
            teardown()
    if failed:
        raise Exception(f"tests {failed} FAILED. See output for details.")


def run_service_tests(service_test):
    logger.info("--- run_service_tests %s", service_test)
    failed = []
    for x in service_test:
        try:
            x()
        except Exception as e:
            logger.error("Exception with pass %s", x, exc_info=True)
            failed += [f"{x}"]
    return failed

def run_other_tests(other_tests):
    logger.info("--- run_other_tests %s", other_tests)
    failed = []
    for x in other_tests:
        try:
            x()
        except Exception as e:
            logger.error("Exception with pass %s", x, exc_info=True)
            failed += [f"{x}"]
    return failed

def run_attribute_tests(sdks_encrypt, sdks_decrypt, pt_file):
    logger.info("--- run_attribute_tests %s => %s", sdks_encrypt, sdks_decrypt)

    failed = []

    serial = 0
    for x in sdks_encrypt:
        for y in sdks_decrypt:
            serial_attr = 1
            for name, attrs in ATTR_TESTS.items():
                rt_func = (
                    test_cross_roundtrip_failure
                    if "fail" in name
                    else test_cross_roundtrip
                )
                logger.info(f"Test #{serial}.{serial_attr}: {name}")
                try:
                    rt_func(
                        x,
                        y,
                        f"{serial}.{serial_attr}",
                        pt_file,
                        attributes=attrs,
                        encrypt_client=TEST_CLIENT_1,
                        decrypt_client=TEST_CLIENT_2,
                    )
                except Exception as e:
                    logger.error(
                        "Exception with pass (%s => %s) %s", x, y, name, exc_info=True
                    )
                    failed += [f"{name} {x}=>{y}"]
                finally:
                    serial_attr += 1
            serial += 1
    return failed


def run_cli_tests(sdks_encrypt, sdks_decrypt, pt_file, attributes=None):
    logger.info("--- run_cli_tests %s => %s", sdks_encrypt, sdks_decrypt)
    failed = []

    serial = 0
    for x in sdks_encrypt:
        for y in sdks_decrypt:
            try:
                test_cross_roundtrip(x, y, serial, pt_file, attributes)
            except Exception as e:
                logger.error("Exception with pass %s => %s", x, y, exc_info=True)
                failed += [f"{x}=>{y}"]
            serial += 1
    return failed


# Test a roundtrip across the two referenced sdks.
# Returns True if test succeeded, false otherwise.
def test_cross_roundtrip(
    encrypt_sdk,
    decrypt_sdk,
    serial,
    pt_file,
    attributes=None,
    encrypt_client=CLIENT_ID,
    decrypt_client=CLIENT_ID,
):
    logger.info(
        "--- Begin Test #%s: Roundtrip encrypt(%s) --> decrypt(%s)",
        serial,
        encrypt_sdk,
        decrypt_sdk,
    )

    # Generate plaintext and files
    ct_file, rt_file = gen_files(serial)

    # Do the roundtrip.
    logger.info("Encrypt %s", encrypt_sdk)
    encrypt_sdk(pt_file, ct_file, attributes=attributes, client_id=encrypt_client)
    logger.info("Decrypt %s", decrypt_sdk)
    decrypt_sdk(ct_file, rt_file, client_id=decrypt_client)

    # Verify the roundtripped result is the same as our initial plantext.
    if not filecmp.cmp(pt_file, rt_file):
        raise Exception(
            "Test #%s: FAILED due to rt mismatch\n\texpected: %s\n\tactual: %s)"
            % (serial, pt_file, rt_file)
        )
    logger.info("Test #%s, (%s->%s): Succeeded!", serial, encrypt_sdk, decrypt_sdk)


def test_cross_roundtrip_failure(
    encrypt_sdk,
    decrypt_sdk,
    serial,
    pt_file,
    attributes=None,
    encrypt_client=CLIENT_ID,
    decrypt_client=CLIENT_ID,
):
    logger.info(
        "--- Begin Test #%s: Roundtrip encrypt(%s) --> decrypt(%s)",
        serial,
        encrypt_sdk,
        decrypt_sdk,
    )

    # Generate plaintext and files
    ct_file, rt_file = gen_files(serial)

    # Do the roundtrip.
    logger.info("Encrypt %s", encrypt_sdk)
    encrypt_sdk(pt_file, ct_file, attributes=attributes, client_id=encrypt_client)
    logger.info("Decrypt %s", decrypt_sdk)
    try:
        decrypt_sdk(ct_file, rt_file, client_id=decrypt_client)
    except:
        logger.info("Test #%s, (%s->%s): Succeeded!", serial, encrypt_sdk, decrypt_sdk)
    else:
        raise Exception(
            "Test #%s: (%s --> %s) FAIL -- decrypt should fail but succeeded)"
            % (serial, encrypt_sdk, decrypt_sdk)
        )


def gen_pt(*, large):
    pt_file = "%stest-plain-%s.txt" % (tmp_dir, "large" if large else "small")
    length = (5 * 2**30) if large else 128
    with open(pt_file, "w") as f:
        for i in range(0, length, 16):
            f.write("{:15,d}\n".format(i))
    return pt_file


def gen_files(serial):
    ct_file = "%stest-%s.tdf" % (tmp_dir, serial)  # ciphertext (TDF)
    rt_file = "%stest-%s.untdf" % (tmp_dir, serial)  # roundtrip (plaintext)

    return ct_file, rt_file


def random_string():
    return "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(128)
    )


if __name__ == "__main__":
    main()
