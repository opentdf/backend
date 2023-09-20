import uuid
import json
import datetime
import os
import logging
import sys
import socket
from python_base import HttpMethod
from enum import Enum


##### Set up logger ########

AUDIT_LEVEL_NUM = os.getenv("AUDIT_LEVEL_NUM", 45)
AUDIT_ENABLED = os.getenv("AUDIT_ENABLED", "false").lower() in ("yes", "true", "t", "1")

ORG_ID = os.getenv("CONFIG_ORG_ID", str(uuid.uuid4()))


logging.basicConfig(
    stream=sys.stdout, level=os.getenv("SERVER_LOG_LEVEL", "CRITICAL").upper()
)

logging.addLevelName(AUDIT_LEVEL_NUM, "AUDIT")


def audit(self, message, *args, **kws):
    if self.isEnabledFor(AUDIT_LEVEL_NUM) and AUDIT_ENABLED:
        self._log(AUDIT_LEVEL_NUM, message, args, **kws)


logging.Logger.audit = audit
logger = logging.getLogger(__package__)

##### Enums #########


class CallType(Enum):
    PRE = 1
    POST = 2
    ERR = 3


###### HOOKS ##########


def audit_hook(http_method, function_name, *args, **kwargs):
    if http_method in [HttpMethod.POST, HttpMethod.PUT, HttpMethod.DELETE]:
        _audit_log(CallType.POST, http_method, function_name, *args, **kwargs)
    pass


def err_audit_hook(http_method, function_name, err, *args, **kwargs):
    if http_method in [HttpMethod.POST, HttpMethod.PUT, HttpMethod.DELETE]:
        _audit_log(CallType.ERR, http_method, function_name, *args, **kwargs)
    pass


##### Custom Log ######


def _audit_log(
    call_type, http_method, function_name, request, auth_token, *args, **kwargs
):
    # not currently configured for attribute audit logging
    if http_method == HttpMethod.POST:
        transaction_type = "create"
    elif http_method == HttpMethod.DELETE:
        transaction_type = "delete"
    else:
        transaction_type = "update"

    if call_type == CallType.ERR:
        transaction_result = "error"
    else:
        transaction_result = "success"
    # audit_log = {
    #     "id": str(uuid.uuid4()),
    #     "transaction_timestamp": str(datetime.datetime.now()),
    #     "tdf_id": None,
    #     "tdf_name": None,
    #     # this will be the clientid or user
    #     "owner_id": auth_token.get("azp") if type(auth_token) is dict else None,
    #     # who created the token: http://localhost:65432/auth/realms/tdf
    #     "owner_org_id": auth_token.get("iss") if type(auth_token) is dict else None,
    #     "transaction_type": transaction_type,
    #     "action_type": "access_modified",
    #     "actor_attributes": request,
    # }
    audit_log = {
        "id": str(uuid.uuid4()),
        "object": {
            "type": "entity_object",
            "id": str(uuid.uuid4()),
            "attributes": {
                "attrs": request,
                "dissem": [],
                "permissions": [] #only for user_objects
            }
        },
        "action": {
            "type": transaction_type,
            "result": transaction_result,
        },
        "owner": {
            "id": auth_token.get("sub") if type(auth_token) is dict else None,
            "orgId": ORG_ID
        },
        "actor": {
            "id": auth_token.get("azp") if type(auth_token) is dict else None,
            "attributes": {
                "attrs": [],
                "permissions": [] #only for user_objects
            }
        },
        "eventMetaData": {},
        "clientInfo": {
            "userAgent": None,
            "platform": "entitlements",
            "requestIp": str(socket.gethostbyname(socket.gethostname())),
        },
        "diff": {},
        "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    if auth_token.get("tdf_claims") and auth_token.get("tdf_claims").get("entitlements"):
        attributes = set()
        # just put all entitlements into one list, dont seperate by entity for now
        for item in auth_token.get("tdf_claims").get("entitlements"):
            for attribute in item.get("entity_attributes"):
                attributes.add(attribute.get("attribute"))
        audit_log["actor"]["attributes"]["attrs"] = list(attributes)

    logger.audit(json.dumps(audit_log))
