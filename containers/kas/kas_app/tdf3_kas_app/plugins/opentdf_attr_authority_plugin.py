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
    BadRequestError,
)

logger = logging.getLogger(__name__)


class OpenTDFAttrAuthorityPlugin(AbstractHealthzPlugin, AbstractRewrapPlugin):
    """Fetch attributes from OpenTDF Attribute authority instance.
    Note that this plugin is expected to return a list of attributes
    in the following format:


     class Attribute:
         authority: AnyUrl
         name: str
         order: list
         rule: RuleEnum
         state: str (optional)
         group_by: {"name":xxx, "authority":xxx, "value":xxx} (optional)

    Somehow this abstraction was missed, and in a statically-type language would be necessarily made
    explicit by the plugin interface itself so it wouldn't need specifying, but this is Python
    and DIY typing.
    """

    def __init__(self, attribute_host):
        """Initialize the plugin."""
        self._host = attribute_host
        self._headers = {"Content-Type": "application/json"}
        self._timeout = 10  # in seconds

    def _fetch_definition_from_authority_by_ns(self, namespace):
        ca_cert_path = os.environ.get("CA_CERT_PATH")
        client_cert_path = os.environ.get("CLIENT_CERT_PATH")
        client_key_path = os.environ.get("CLIENT_KEY_PATH")

        uri = "{0}/v1/attrName".format(self._host)
        params = {"authority": namespace}

        try:
            if client_cert_path and client_key_path:
                logger.debug("Using cert auth for url:%s", uri)
                resp = requests.get(
                    uri,
                    headers=self._headers,
                    params=params,
                    timeout=self._timeout,
                    cert=(client_cert_path, client_key_path),
                    verify=ca_cert_path,
                )
            else:
                resp = requests.get(
                    uri,
                    headers=self._headers,
                    params=params,
                    timeout=self._timeout,
                    verify=ca_cert_path,
                )
        except (
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ReadTimeout,
        ) as err:
            logger.warning("attr auth: timeout [%s]", uri, exc_info=err)
            raise RequestTimeoutError(
                "Fetch attributes request connect timed out"
            ) from err
        except requests.exceptions.RequestException as err:
            logger.warning("attr auth: request exception [%s]", uri, exc_info=err)
            raise InvalidAttributeError("Unable to be fetch attributes") from err

        if resp.status_code != 200:
            logger.debug(
                "--- Fetch attribute %s failed with status %s; reason [%s] ---",
                uri,
                resp.status_code,
                resp.reason,
            )
            return []
        logger.debug("--- Fetch attributes successful --- ")
        res = resp.json()
        logger.debug("Fetch attribute %s => %s", uri, res)
        return res

    def fetch_attributes(self, namespaces):
        """Fetch attribute definitions from authority for KAS to make rewrap decision."""
        logger.debug(
            "--- Fetch attributes from OpenTDF Attribute authority [namespaces to fetch = %s] ---",
            namespaces,
        )

        attrs = []
        namespaces = set(
            [x if "/attr/" not in x else x.split("/attr/")[0] for x in namespaces]
        )
        for namespace in namespaces:
            ns_attrdefs = self._fetch_definition_from_authority_by_ns(namespace)
            attrs = attrs + ns_attrdefs

        if len(attrs) == 0:
            return None

        print(attrs)
        return attrs

    def update(self, req, res):
        """We use the default rewrap behavior."""
        return (req, res)

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
