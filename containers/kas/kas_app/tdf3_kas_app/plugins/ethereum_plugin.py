import logging
import os

import requests
import jwt as jwt

from tdf3_kas_core.abstractions import AbstractRewrapPlugin
from tdf3_kas_core import Policy
from tdf3_kas_core.errors import BadRequestError

logger = logging.getLogger(__name__)


def get_entity_pubkey(access_jwt):
    # grab information out of the token without verifying it.
    decoded_jwt = jwt.decode(
        access_jwt,
        options={"verify_signature": False, "verify_aud": False},
        algorithms=["RS256", "ES256", "ES384", "ES512"],
    )
    logger.debug(decoded_jwt)
    return decoded_jwt["entity-pubkey"]


class EthereumPlugin(AbstractRewrapPlugin):
    def update(self, req, res):
        # entity_pubkey from bearer token
        global tdf_pubkey, tdf_content_tier
        auth_token = req["context"].data["Authorization"]
        bearer, _, idp_jwt = auth_token.partition(" ")
        entity_pubkey = get_entity_pubkey(idp_jwt)
        logger.debug("~~~~~~~~~")
        logger.debug(entity_pubkey)
        logger.debug("~~~~~~~~~")
        # tdf_pubkey and tdf_amount from TDF data attributes
        canonical_policy: Policy = req["policy"]
        found = False
        for _, data_attribute in enumerate(canonical_policy.data_attributes.clusters):
            if data_attribute.namespace.startswith("https://kovan.network/attr/Wallet"):
                found = True
                for _, values in enumerate(data_attribute.values):
                    tdf_pubkey = values.value
                    logger.debug("*********")
                    logger.debug(tdf_pubkey)
                    logger.debug("*********")
            if data_attribute.namespace.startswith("https://virtru.com/attr/ContentExclusivity"):
                for _, values in enumerate(data_attribute.values):
                    tdf_content_tier = values.value
                    logger.debug(".........")
                    logger.debug(tdf_content_tier)
                    logger.debug(".........")
        # make call to eth-pdp
        if found:
            eth_pdp_url = os.getenv("PLUGIN_ETH_URL")
            url = f"{eth_pdp_url}?tier={tdf_content_tier}&senderAddress={entity_pubkey}&recipientAddress={tdf_pubkey}&value=0.01"
            logger.debug(url)
            response = requests.request("GET", url, headers={}, data={})
            if response.status_code is not 200:
                raise BadRequestError("payment not found")

        return req, res
