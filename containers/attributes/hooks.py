import os
import logging
import sys
from enum import Enum
from python_base import HttpMethod

##### Set Up Logger ########

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

##### Custom Enums #########


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
    call_type, http_method, function_name, request, decoded_token, *args, **kwargs
):
    # not currently configured for attribute audit logging
    pass