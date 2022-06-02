"""OpenTDF rewrap plugin."""

import logging
import requests
import json
import os

from tdf3_kas_core.abstractions import AbstractHealthzPlugin, AbstractRewrapPlugin

from tdf3_kas_core.errors import (
    Error,
    InvalidAttributeError,
    RequestTimeoutError,
    BadRequestError
)
logger = logging.getLogger(__name__)


class OpenTDFAttrAuthorityPlugin(AbstractHealthzPlugin, AbstractRewrapPlugin):
    """Fetch attributes from OpenTDF Attribute authority instance."""

    def __init__(self, attribute_host):
        """Initialize the plugin."""
        self._host = attribute_host
        self._headers = {"Content-Type": "application/json", },
        self._timeout = 10  # in seconds

    def fetch_attributes(self, namespaces):
        """Fetch attribute definitions from authority for KAS to make rewrap decision."""
        logger.debug("--- Fetch attributes from OpenTDF Attribute authority [attribute = %s] ---", namespaces)

        uri = "{0}/v1/attrName".format(self._host)
        ca_cert_path = os.environ.get("CA_CERT_PATH")
        client_cert_path = os.environ.get("CLIENT_CERT_PATH")
        client_key_path = os.environ.get("CLIENT_KEY_PATH")

        try:
            if client_cert_path and client_key_path:
                logger.debug("Using cert auth for url:%s", uri)
                resp = requests.post(
                    uri,
                    headers=self._headers,
                    data=json.dumps(namespaces),
                    timeout=self._timeout,
                    cert=(client_cert_path, client_key_path),
                    verify=ca_cert_path,
                )
            else:
                resp = requests.post(
                    uri,
                    headers=self._headers,
                    data=json.dumps(namespaces),
                    timeout=self._timeout,
                    verify=ca_cert_path,
                )
        except (
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ReadTimeout,
        ) as err:
            logger.exception(err)
            logger.setLevel(logging.DEBUG)
            raise RequestTimeoutError(
                "Fetch attributes request connect timed out"
            ) from err
        except requests.exceptions.RequestException as err:
            logger.exception(err)
            logger.setLevel(logging.DEBUG)
            raise InvalidAttributeError("Unable to be fetch attributes") from err

        if resp.status_code != 200:
            logger.debug(
                "--- Fetch attribute %s failed with status %s; reason [%s] ---",
                uri,
                resp.status_code,
                resp.reason,
            )
            return None
        logger.debug("--- Fetch attributes successful --- ")
        res = resp.json()
        logger.debug("Fetch attribute %s => %s", uri, res)
        return res

    def healthz(self, *, probe):
        """Ping OpenTDF Attribute service."""
        if "readiness" == probe:
            logger.debug("--- Ping OpenTDF Attribute authority ---")

            uri = "{0}/healthz".format(self._host)
            ca_cert_path = os.environ.get("CA_CERT_PATH")
            client_cert_path = os.environ.get("CLIENT_CERT_PATH")
            client_key_path = os.environ.get("CLIENT_KEY_PATH")

            if client_cert_path and client_key_path:
                logger.debug("Using cert auth for url:%s", uri)
                resp = requests.get(
                    uri,
                    headers=self._headers,
                    timeout=self._timeout,
                    cert=(client_cert_path, client_key_path),
                    verify=ca_cert_path,
                )
            else:
                resp = requests.get(
                    uri,
                    headers=self._headers,
                    timeout=self._timeout,
                    verify=ca_cert_path,
                )

            if 200 <= resp.status_code < 300:
                logger.debug("--- Ping OpenTDF Attribute authority successful --- ")
            else:
                logger.debug(
                    "--- Ping OpenTDF Attribute authority %s failed with status %s; reason [%s] ---",
                    uri,
                    resp.status_code,
                    resp.reason,
                )
                raise Error("Unable to be ping OpenTDF Attribute authority")

        elif not probe or probe == "liveness":
            pass
        else:
            raise BadRequestError(f"Unrecognized healthz probe name {probe}")
