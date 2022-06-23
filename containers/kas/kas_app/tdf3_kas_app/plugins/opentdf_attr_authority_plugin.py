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


def _translate_otdf_attrdefs(attrdefs):
    '''
    KAS has an (undocumented) format for attribute definitions
    that differs from the one OpenTDF uses by two (2) property names
    so just append those duplicate properties to the dict and
    call it a day - the schema emitted by the AA shouldn't be
    tightly coupled to KAS processing and it's not worth maintaining
    separate serverside handlers for this.

    You might ask why this plugin/kas data model isn't just changed to use the
    new route/handler.

    Well, that's because the new handler does non-optional pagination and JWT auth,
    and KAS isn't set up to do the former, and doesn't need to do the latter (E-W traffic)
    '''

    for attr in attrdefs:
        attr["authorityNamespace"] = attr["authority"]
        attr["values"] = attr["order"]


class OpenTDFAttrAuthorityPlugin(AbstractHealthzPlugin, AbstractRewrapPlugin):
    """Fetch attributes from OpenTDF Attribute authority instance.
       Note that this plugin is expected to return a list of attributes
       in the following format:


        class Attribute:
            authorityNamespace: AnyUrl
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
        params = {'authority': namespace}

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

    def fetch_attributes(self, namespaces):
        """Fetch attribute definitions from authority for KAS to make rewrap decision."""
        logger.debug("--- Fetch attributes from OpenTDF Attribute authority [namespaces to fetch = %s] ---", namespaces)

        attrs = []
        for namespace in namespaces:
            ns_attrdefs = self._fetch_definition_from_authority_by_ns(namespace)
            _translate_otdf_attrdefs(ns_attrdefs)
            attrs.append(ns_attrdefs)

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
