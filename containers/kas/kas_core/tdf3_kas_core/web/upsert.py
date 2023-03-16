"""REST Web handler for upsert."""
import connexion
import logging

from ..kas import Kas
from ..schema import get_schema

from .create_context import create_context
from .run_service_with_exceptions import run_service_with_exceptions

TDF3_UPSERT_SCHEMA = get_schema("tdf3_upsert_schema")
logger = logging.getLogger(__name__)


def upsert_helper(body, mode="upsert"):
    """Handle the '/upsert' route.

    This endpoint performs a secondary service of the KAS; to proxy the
    back-end services that support the KAS functions.
    """
    logger.debug("+=+=+=+=+=+ Upsert service runner starting")

    # Data validation performed by Connexion library against openapi.yaml

    # create the context object. Connexion provides Flask request headers:
    context = create_context(connexion.request.headers)

    logger.debug("+=+=+=+=+=+ Upsert Request is Valid")

    # process the request. Throws a variety of errors.
    if mode == "upsert":
        logger.info("+=+=+=+=+=+ UpsertV1")
        session_upsert = Kas.get_instance().get_session_upsert()
    else:
        logger.info("+=+=+=+=+=+ UpsertV2")
        session_upsert = Kas.get_instance().get_session_upsert_v2()
    res = session_upsert(body, context)
    # package up the response and send it.

    logger.debug("+=+=+=+=+=+ Upsert request complete")
    return res


@run_service_with_exceptions
def upsert(body, *, dpop=None):
    Kas.get_instance().get_middleware()(dpop, Kas.get_instance()._key_master)
    return upsert_helper(body, "upsert")


@run_service_with_exceptions
def upsert_v2(body, *, dpop=None):
    Kas.get_instance().get_middleware()(dpop, Kas.get_instance()._key_master)
    return upsert_helper(body, "upsert_v2")
