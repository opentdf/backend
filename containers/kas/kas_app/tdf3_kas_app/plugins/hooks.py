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

# temporarily use constant owner org id
OWNER_ORG_ID = str(uuid.uuid4())

def audit_hook(function_name, return_value, data, context, *args, **kwargs):
    # wrap in try except to prevent unnecessary 500s
    try:
        audit_log = {
            "id": str(uuid.uuid4()),
            "transaction_timestamp": str(datetime.datetime.now()),
            "tdf_id": "",
            "tdf_name": None,
            # this will be the clientid or user
            "owner_id": "",
            "owner_org_id": OWNER_ORG_ID,
            "transaction_type": "create",
            "action_type": "decrypt",
            "tdf_attributes": {"dissem":[], "attrs":[]},
            "actor_attributes": {"npe":True, "actor_id":"", "attrs":[]},
        }

        res, policy, claims = return_value

        audit_log["tdf_attributes"]["attrs"] = policy.data_attributes.export_raw()
        audit_log["tdf_attributes"]["dissem"] = policy.dissem.list
            
        audit_log = extract_info_from_auth_token(audit_log, context)

        logger.audit(json.dumps(audit_log))
    except:
        logger.error("Error on audit_hook - unable to log audit")

    return res

def err_audit_hook(function_name, err, data, context, plugin_runner, key_master, *args, **kwargs):
    # wrap in try except to prevent unnecessary 500s
    try:
        # not yet auditing other errors, only access denied
        if not (type(err) is AuthorizationError) and ("Access Denied" in str(err)):
            return

        audit_log = {
            "id": str(uuid.uuid4()),
            "transaction_timestamp": str(datetime.datetime.now()),
            "tdf_id": "",
            "tdf_name": None,
            # this will be the clientid or user
            "owner_id": "",
            "owner_org_id": OWNER_ORG_ID,
            "transaction_type": "create_error",
            "action_type": "access_denied",
            "tdf_attributes": {"dissem":[], "attrs":[]},
            "actor_attributes": {"npe":True, "actor_id":"", "attrs":[]},
        }
        
        audit_log = extract_info_from_auth_token(audit_log, context)

        # wrap in try except -- should not fail since succeeded before
        if "signedRequestToken" not in data:
            logger.error("Rewrap success without signedRequestToken - should never get here")
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
            algorithm = dataJson.get("algorithm", "rsa:2048")
            if algorithm == "ec:secp256r1":
                # nano tdf
                key_access = dataJson["keyAccess"]
                header = base64.b64decode(key_access["header"])
                client_version = packaging.version.parse(
                    context.get("virtru-ntdf-version") or "0.0.0"
                )
                legacy_wrapping = (os.environ.get("LEGACY_NANOTDF_IV") == "1") and client_version < packaging.version.parse("0.0.1")
                (_, header) = ResourceLocator.parse(header[3:])
                (ecc_mode, header) = ECCMode.parse(header)
                # extract payload config from header.
                (payload_config, header) = SymmetricAndPayloadConfig.parse(header)
                # extract policy from header.
                (policy_info, header) = PolicyInfo.parse(ecc_mode, payload_config, header)
                # extract ephemeral key from the header.
                ephemeral_key = header[0 : ecc_mode.curve.public_key_byte_length]

                kas_private = key_master.get_key("KAS-EC-SECP256R1-PRIVATE")
                private_key_bytes = kas_private.private_bytes(
                    serialization.Encoding.DER,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                )
                decryptor = ecc_mode.curve.create_decryptor(ephemeral_key, private_key_bytes)

                zero_iv = b"\0" * (3 if legacy_wrapping else 12)
                symmetric_cipher = payload_config.symmetric_cipher(decryptor.symmetric_key, zero_iv)
                policy_data = policy_info.body.data
                policy_data_len = len(policy_data) - payload_config.symmetric_tag_length
                auth_tag = policy_data[-payload_config.symmetric_tag_length :]

                policy_data_as_byte = base64.b64encode(
                    symmetric_cipher.decrypt(policy_data[0:policy_data_len], auth_tag)
                )
                original_policy = Policy.construct_from_raw_canonical(
                    policy_data_as_byte.decode("utf-8")
                )

                audit_log["tdf_attributes"]["attrs"] = original_policy.data_attributes.export_raw()
                audit_log["tdf_attributes"]["dissem"] = original_policy.dissem.list

            else:
                # tdf3
                canonical_policy = dataJson["policy"]
                original_policy = Policy.construct_from_raw_canonical(canonical_policy)
                audit_log["tdf_attributes"]["attrs"] = original_policy.data_attributes.export_raw()
                audit_log["tdf_attributes"]["dissem"] = original_policy.dissem.list
    
    
        logger.audit(json.dumps(audit_log))

    except:
        logger.error("Error on err_audit_hook - unable to log audit")



def extract_info_from_auth_token(audit_log, context):
    try:
        authToken = context.data["Authorization"]
        bearer, _, idpJWT = authToken.partition(" ")
    except KeyError as e:
        logger.error("Rewrap success without auth header - should never get here")
    else:
        if bearer != "Bearer":
            logger.error("Rewrap success without valid auth header - should never get here")
        else:
            decoded_auth = jwt.decode(
                    idpJWT,
                    options={"verify_signature": False, "verify_aud": False},
                    algorithms=["RS256", "ES256", "ES384", "ES512"],
                )
            if decoded_auth.get("sub"):
                audit_log["owner_id"] = decoded_auth.get("sub")
            if decoded_auth.get("tdf_claims").get("entitlements"):
                attributes = set()
                # assuming items formatted correctly
                # just put all entitlements into one list, dont seperate by entity for now
                for item in decoded_auth.get("tdf_claims").get("entitlements"):
                    for attribute in item.get("entity_attributes"):
                        attributes.add(attribute.get("attribute"))
                audit_log["actor_attributes"]["attrs"] = list(attributes)
            if decoded_auth.get("azp"):
                audit_log["actor_attributes"]["actor_id"] = decoded_auth.get("azp")
    
    return audit_log
