import logging

logger = logging.getLogger(__name__)

def audit_hook(function_name, data, context, *args, **kwargs):
    logger.audit("------AUDIT_HOOK------")
    logger.audit(data)
    logger.audit(context)
    for arg in args:
        logger.audit(arg)
    for key, value in kwargs.items():
        logger.audit("%s == %s" % (key, value))
    logger.audit("-------------------------")
    # if http_method in [HttpMethod.POST, HttpMethod.PUT, HttpMethod.DELETE]:
    #     _audit_log(CallType.POST, http_method, function_name, *args, **kwargs)
    # pass


def err_audit_hook(http_method, function_name, err, *args, **kwargs):
    logger.audit("ERR_AUDIT_HOOK")
    # if http_method in [HttpMethod.POST, HttpMethod.PUT, HttpMethod.DELETE]:
    #     _audit_log(CallType.ERR, http_method, function_name, *args, **kwargs)
    # pass