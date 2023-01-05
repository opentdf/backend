import logging
import os
from gunicorn import glogging

AUDIT_LEVEL_NUM = os.getenv("AUDIT_LEVEL_NUM", 45)
AUDIT_ENABLED = os.getenv("AUDIT_ENABLED", "false").lower() in ("yes", "true", "t", "1")


class KasLogger(glogging.Logger):
    """Custom logger for Gunicorn log messages."""

    LOG_LEVELS = {
        "critical": logging.CRITICAL,
        "audit": AUDIT_LEVEL_NUM,
        "error": logging.ERROR,
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG,
    }

    logging.addLevelName(AUDIT_LEVEL_NUM, "AUDIT")

    def audit(self, message, *args, **kws):
        if self.isEnabledFor(AUDIT_LEVEL_NUM) and AUDIT_ENABLED:
            self._log(AUDIT_LEVEL_NUM, message, args, **kws)

    logging.Logger.audit = audit

    def __init__(self, cfg):
        super(KasLogger, self).__init__(cfg)

    def audit(self, msg, *args, **kwargs):
        lvl = self.LOG_LEVELS.get("audit", logging.INFO)
        self.error_log.log(lvl, msg, *args, **kwargs)
