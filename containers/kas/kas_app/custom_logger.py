import logging
import os
from gunicorn import glogging

AUDIT_LEVEL_NUM = os.getenv("AUDIT_LEVEL_NUM", 45)

class CustomLogger(glogging.Logger):
    """Custom logger for Gunicorn log messages."""

    LOG_LEVELS = {
        "critical": logging.CRITICAL,
        "error": logging.ERROR,
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG
    }

    LOG_LEVELS["audit"] = AUDIT_LEVEL_NUM
    logging.addLevelName(AUDIT_LEVEL_NUM, "AUDIT")
    def audit(self, message, *args, **kws):
        if self.isEnabledFor(AUDIT_LEVEL_NUM):
            self._log(AUDIT_LEVEL_NUM, message, args, **kws) 
    logging.Logger.audit = audit

    def __init__(self, cfg):
        super(CustomLogger, self).__init__(cfg)

    def audit(self, msg, *args, **kwargs):
        lvl = self.LOG_LEVELS.get("audit", logging.INFO)
        self.error_log.log(lvl, msg, *args, **kwargs)
