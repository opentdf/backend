"""This example file exposes a wsgi-callable object as app."""

import os
import logging

from importlib import metadata
from importlib.metadata import PackageNotFoundError

from tdf3_kas_core import Kas

from .plugins import (
    opentdf_attr_authority_plugin,
    revocation_plugin,
    access_pdp_healthz_plugin,
    hooks
)

logger = logging.getLogger(__name__)


USE_OIDC = os.environ.get("USE_OIDC") == "1"
OIDC_SERVER_URL = os.environ.get("OIDC_SERVER_URL") is not None

AUDIT_ENABLED = os.getenv("AUDIT_ENABLED", "false").lower() in ("yes", "true", "t", "1")


def configure_filters(kas):
    def str_to_list(varname):
        s = os.environ.get(varname)
        if not s:
            return None
        return s.split(",")

    allows = str_to_list("EO_ALLOW_LIST")
    blocks = str_to_list("EO_BLOCK_LIST")
    if not (allows or blocks):
        return
    filter_plugin = revocation_plugin.RevocationPlugin(allows=allows, blocks=blocks)
    kas.use_rewrap_plugin(filter_plugin)
    kas.use_upsert_plugin(filter_plugin)
    if USE_OIDC:
        # filter_plugin = revocation_plugin.RevocationPluginV2(allows=allows, blocks=blocks)
        kas.use_rewrap_plugin_v2(filter_plugin)
        kas.use_upsert_plugin_v2(filter_plugin)


def version_info():
    try:
        return metadata.version("tdf3-kas-core")
    except PackageNotFoundError:
        curr_dir = os.path.dirname(__file__)
        project_dir = os.path.dirname(curr_dir)
        path = os.path.join(project_dir, "VERSION")
        with open(path, "r") as ver:
            return ver.read()


def app(name):
    """Return a wsgi-callable app containing the KAS instance.

    This is a very simple plain vanilla instance. Attribute config files and
    policy plugins can be added to enhance the basic functionality.

    The name parameter is the name of the execution root. Typically this will
    be __main__.
    """
    global USE_OIDC
    # Construct the KAS instance
    kas = Kas.get_instance()
    kas.set_root_name(name)

    # Set the version, if possible
    version = version_info()
    if not version:
        logger.warning("Version not found")
    else:
        try:
            logger.info("KAS version is %s", version)
            kas.set_version(version)
        except AttributeError as e:
            logger.exception(e)
            logger.warning("Version not set")

    if USE_OIDC and OIDC_SERVER_URL:
        logger.info("Keycloak integration enabled.")
    elif USE_OIDC or OIDC_SERVER_URL:
        e_msg = "Either USE_OIDC or OIDC_SERVER_URL are not correctly defined - both are required."
        logger.error(e_msg)
        raise Exception(e_msg)
    # Add Attribute fetch plugin
    attr_host = os.environ.get("ATTR_AUTHORITY_HOST")
    if not attr_host:
        logger.error("OTDF attribute host is not configured correctly.")

    logger.info("ATTR_AUTHORITY_HOST = [%s]", attr_host)
    otdf_attr_backend = opentdf_attr_authority_plugin.OpenTDFAttrAuthorityPlugin(
        attr_host
    )
    kas.use_healthz_plugin(otdf_attr_backend)
    kas.use_rewrap_plugin_v2(otdf_attr_backend)

    access_pdp_health = access_pdp_healthz_plugin.AccessPDPHealthzPlugin()
    kas.use_healthz_plugin(access_pdp_health)

    if AUDIT_ENABLED:
        kas.use_post_rewrap_hook(hooks.audit_hook)
        kas.use_err_rewrap_hook(hooks.err_audit_hook)

    configure_filters(kas)

    # Get configuration from environment
    def load_key_bytes(env_var, start_app_errors):
        key = os.getenv(env_var, None)
        if not key:
            start_app_errors.append(env_var)
            return None
        return key.encode()

    missing_variables = []
    (
        kas_private_key,
        kas_certificate,
        kas_ec_secp256r1_certificate,
        kas_ec_secp256r1_private_key,
    ) = [
        load_key_bytes(e, missing_variables)
        for e in [
            "KAS_PRIVATE_KEY",
            "KAS_CERTIFICATE",
            "KAS_EC_SECP256R1_CERTIFICATE",
            "KAS_EC_SECP256R1_PRIVATE_KEY",
        ]
    ]
    # Exit if errors exist
    if missing_variables:
        raise Exception(f"KAS must have variables: {missing_variables}.")

    # Configure kas
    kas.set_key_pem("KAS-PRIVATE", "PRIVATE", kas_private_key)
    kas.set_key_pem("KAS-PUBLIC", "PUBLIC", kas_certificate)
    kas.set_key_pem("KAS-EC-SECP256R1-PRIVATE", "PRIVATE", kas_ec_secp256r1_private_key)
    kas.set_key_pem("KAS-EC-SECP256R1-PUBLIC", "PUBLIC", kas_ec_secp256r1_certificate)

    # Configure compatibility with EO mode
    aa_certificate = load_key_bytes("ATTR_AUTHORITY_CERTIFICATE", missing_variables)
    if not aa_certificate:
        logger.warn(
            "KAS does not have an ATTR_AUTHORITY_CERTIFICATE; running in OIDC-only mode"
        )
    else:
        kas.set_key_pem("AA-PUBLIC", "PUBLIC", aa_certificate)

    # Get a Flask app from the KAS instance
    return kas.app()
