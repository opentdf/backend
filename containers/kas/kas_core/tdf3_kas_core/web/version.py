"""REST Web handler for version."""

from tdf3_kas_core.kas import Kas
import logging
from .run_service_with_exceptions import run_service_with_exceptions

logger = logging.getLogger(__name__)


@run_service_with_exceptions
def version():
    """Handle the '/version' route.

    Display image tag and chart version
    """
    logger.debug("version()")
    return (Kas.get_instance().get_session_version())()
