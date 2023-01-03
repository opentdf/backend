import uuid
import json
import datetime
import os
import logging
import sys
import functools
from enum import Enum


##### Set up logger ########

AUDIT_LEVEL_NUM = os.getenv("AUDIT_LEVEL_NUM", 45)
AUDIT_ENABLED = os.getenv("AUDIT_ENABLED", "false").lower() in ("yes", "true", "t", "1")


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

class HttpMethod(Enum):
    GET = 4
    POST = 5
    PUT = 6
    PATCH = 7
    DELETE = 8

##### Hook decorator #########

def hook_into(http_method):
    def hooks_decorator(func):
        @functools.wraps(func)
        async def hooks_wrapper(*args, **kwargs):
            # Do something before
            run_pre_command_hooks(http_method, func.__name__, *args, **kwargs)
            # try to execute function
            try:
                value = await func(*args, **kwargs)
                # Do something after
                run_post_command_hooks(http_method, func.__name__, *args, **kwargs)
                # return the result
                return value
            # in case of errors
            except Exception as e:
                # run the error hooks
                run_err_hooks(http_method, func.__name__, e, *args, **kwargs)
                raise e
        return hooks_wrapper
    return hooks_decorator

###### HOOKS ##########

def run_pre_command_hooks(http_method, function_name, *args, **kwargs):
    # STUB
    pass

def run_post_command_hooks(http_method, function_name, *args, **kwargs):
    if http_method in [HttpMethod.POST, HttpMethod.PUT, HttpMethod.DELETE]:
        _audit_log(CallType.POST, http_method, function_name, *args, **kwargs)
    pass

def run_err_hooks(http_method, function_name, err, *args, **kwargs):
    if http_method in [HttpMethod.POST, HttpMethod.PUT, HttpMethod.DELETE]:
        _audit_log(CallType.ERR, http_method, function_name, *args, **kwargs)
    pass


##### Custom Log ######

def _audit_log(call_type, http_method, function_name,
                 request, auth_token, *args, **kwargs):
    if call_type == CallType.ERR:
        if http_method == HttpMethod.POST:
            transaction_type = "create-error"
        else:
            transaction_type = "update-error"
    else:
        if http_method == HttpMethod.POST:
            transaction_type = "create"
        else:
            transaction_type = "update"
    audit_log = {
                "id": str(uuid.uuid4()), 
                "transaction_timestamp": str(datetime.datetime.now()), 
                "tdf_id": None,
                "tdf_name": None,
                "owner_id": auth_token["azp"], #this will be the clientid or user
                "owner_org_id": auth_token["iss"], # who created the token: http://localhost:65432/auth/realms/tdf
                "transaction_type": transaction_type, 
                "action_type": "access_modified",
                "actor_attributes": request
                }
    logger.audit(json.dumps(audit_log))
