import logging
import json
import uuid
import datetime
import base64
import jwt
import os

from cryptography.hazmat.primitives import serialization
from pkg_resources import packaging

from tdf3_kas_core.models import Policy
from tdf3_kas_core.models.nanotdf import Policy as PolicyInfo
from tdf3_kas_core.models.nanotdf import ResourceLocator
from tdf3_kas_core.models.nanotdf import ECCMode
from tdf3_kas_core.models.nanotdf import SymmetricAndPayloadConfig

from tdf3_kas_core.errors import AuthorizationError

logger = logging.getLogger(__name__)

ORG_ID = os.getenv("CONFIG_ORG_ID", str(uuid.uuid4()))


def audit_hook(function_name, return_value, data, context, *args, **kwargs):

    res, policy, claims = return_value

    # wrap in try except to prevent unnecessary 500s
    try:
        audit_log = {
            "id": str(uuid.uuid4()),
            "transactionId": str(uuid.uuid4()), ##TODO
            "transactionTimestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tdfId": "",
            "tdfName": None,
            "ownerId": "",
            "ownerOrganizationId": ORG_ID,
            "transactionType": "create",
            "eventType": "decrypt",
            "tdfAttributes": {"dissem": [], "attrs": []},
            "actorAttributes": {"npe": True, "actorId": "", "attrs": []},
        }

        audit_log["tdfId"] = policy.uuid
        audit_log["tdfAttributes"]["attrs"] = policy.data_attributes.export_raw()
        audit_log["tdfAttributes"]["dissem"] = policy.dissem.list

        audit_log = extract_info_from_auth_token(audit_log, context)

        logger.audit(json.dumps(audit_log))

    except Exception as e:
        logger.error(f"Error on err_audit_hook - unable to log audit: {str(e)}")

    return res


def err_audit_hook(
    function_name, err, data, context, plugin_runner, key_master, *args, **kwargs
):
    # wrap in try except to prevent unnecessary 500s
    try:
        # not yet auditing other errors, only access denied
        if not (type(err) is AuthorizationError) and ("Access Denied" in str(err)):
            return

        audit_log = {
            "id": str(uuid.uuid4()),
            "transactionId": str(uuid.uuid4()),
            "transactionTimestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tdfId": "",
            "tdfName": None,
            "ownerId": "",
            "ownerOrganizationId": ORG_ID,
            "transactionType": "create_error",
            "eventType": "access_denied",
            "tdfAttributes": {"dissem": [], "attrs": []},
            "actorAttributes": {"npe": True, "actorId": "", "attrs": []},
        }

        audit_log = extract_info_from_auth_token(audit_log, context)

        # wrap in try except -- should not fail since succeeded before
        if "signedRequestToken" not in data:
            logger.error(
                "Rewrap success without signedRequestToken - should never get here"
            )
        else:
            decoded_request = jwt.decode(
                data["signedRequestToken"],
                options={"verify_signature": False},
                algorithms=["RS256", "ES256", "ES384", "ES512"],
                leeway=30,
            )
            requestBody = decoded_request["requestBody"]
            json_string = requestBody.replace("'", '"')
            dataJson = json.loads(json_string)
            if dataJson.get("algorithm", "rsa:2048") == "ec:secp256r1":
                # nano
                audit_log = extract_policy_data_from_nano(
                    audit_log, dataJson, context, key_master
                )
            else:
                # tdf3
                audit_log = extract_policy_data_from_tdf3(audit_log, dataJson)

        logger.audit(json.dumps(audit_log))

    except Exception as e:
        logger.error(f"Error on err_audit_hook - unable to log audit: {str(e)}")


def extract_policy_data_from_tdf3(audit_log, dataJson):
    canonical_policy = dataJson["policy"]
    original_policy = Policy.construct_from_raw_canonical(canonical_policy)
    audit_log["tdfId"] = original_policy.uuid
    audit_log["tdfAttributes"]["attrs"] = original_policy.data_attributes.export_raw()
    audit_log["tdfAttributes"]["dissem"] = original_policy.dissem.list

    return audit_log


def extract_policy_data_from_nano(audit_log, dataJson, context, key_master):
    header = base64.b64decode(dataJson["keyAccess"]["header"])
    legacy_wrapping = (
        os.environ.get("LEGACY_NANOTDF_IV") == "1"
    ) and packaging.version.parse(
        context.get("virtru-ntdf-version") or "0.0.0"
    ) < packaging.version.parse(
        "0.0.1"
    )

    (ecc_mode, header) = ECCMode.parse(ResourceLocator.parse(header[3:])[1])
    # extract payload config from header.
    (payload_config, header) = SymmetricAndPayloadConfig.parse(header)
    # extract policy from header.
    (policy_info, header) = PolicyInfo.parse(ecc_mode, payload_config, header)

    private_key_bytes = key_master.get_key("KAS-EC-SECP256R1-PRIVATE").private_bytes(
        serialization.Encoding.DER,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    decryptor = ecc_mode.curve.create_decryptor(
        header[0 : ecc_mode.curve.public_key_byte_length], private_key_bytes
    )

    symmetric_cipher = payload_config.symmetric_cipher(
        decryptor.symmetric_key, b"\0" * (3 if legacy_wrapping else 12)
    )
    policy_data = policy_info.body.data

    policy_data_as_byte = base64.b64encode(
        symmetric_cipher.decrypt(
            policy_data[0 : len(policy_data) - payload_config.symmetric_tag_length],
            policy_data[-payload_config.symmetric_tag_length :],
        )
    )
    original_policy = Policy.construct_from_raw_canonical(
        policy_data_as_byte.decode("utf-8")
    )

    audit_log["tdfId"] = original_policy.uuid
    audit_log["tdfAttributes"]["attrs"] = original_policy.data_attributes.export_raw()
    audit_log["tdfAttributes"]["dissem"] = original_policy.dissem.list

    return audit_log


def extract_info_from_auth_token(audit_log, context):
    try:
        authToken = context.data["Authorization"]
        bearer, _, idpJWT = authToken.partition(" ")
    except KeyError as e:
        logger.error("Rewrap success without auth header - should never get here")
    else:
        if bearer != "Bearer":
            logger.error(
                "Rewrap success without valid auth header - should never get here"
            )
        else:
            decoded_auth = jwt.decode(
                idpJWT,
                options={"verify_signature": False, "verify_aud": False},
                algorithms=["RS256", "ES256", "ES384", "ES512"],
            )
            if decoded_auth.get("sub"):
                audit_log["ownerId"] = decoded_auth.get("sub")
            if decoded_auth.get("tdf_claims").get("entitlements"):
                attributes = set()
                # just put all entitlements into one list, dont seperate by entity for now
                for item in decoded_auth.get("tdf_claims").get("entitlements"):
                    for attribute in item.get("entity_attributes"):
                        attributes.add(attribute.get("attribute"))
                audit_log["actorAttributes"]["attrs"] = list(attributes)
            if decoded_auth.get("azp"):
                audit_log["actorAttributes"]["actorId"] = decoded_auth.get("azp")

    return audit_log
