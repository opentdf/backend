"""The AccessPDP makes a decision, which the surrounding KAS PEP uses to determine access to the wrapped key."""
import logging


import grpc
from google.protobuf.json_format import MessageToJson
import tdf3_kas_core.pdp_grpc as pdp_grpc

from tdf3_kas_core.errors import AuthorizationError

from accesspdp.v1 import accesspdp_pb2_grpc, accesspdp_pb2

logger = logging.getLogger(__name__)

local_pdp = "localhost:50052"


class AccessPDP(object):
    """Access PDP (policy decision point) is the ABAC component that makes a boolean Yes/No decision about access

    It is a shared, open-source component that lives here: https://github.com/virtru/access-pdp

    We are invoking it as a local gRPC service here, but it could be remote.

    The Access PDP requires 3 things to make decisions
    # 1. Entity attribute instances
    # 2. Data attribute instances
    # 3. Attribute definitions for every data attribute instance in #2

    KAS is an Access PEP (policy enforcement point), and it "wraps" this PDP.

    The PDP makes the decision, KAS decides what to *do* with the decision.
    """

    def can_access(self, policy, claims, attribute_definitions):
        # TODO deprecated, remove, this skips all ABAC checks
        # Check to see if this claimset fails the dissem tests.
        self._check_dissem(policy.dissem, claims.user_id)
        # Then check the attributes
        self._check_attributes(
            policy.data_attributes, claims.entity_attributes, attribute_definitions
        )
        # Passed all the tests, The entity who was issued this claimset is Worthy!
        return True

    def _check_dissem(self, dissem, entity_id):
        """Test to see if entity is in dissem list.

        If the dissem list is empty then the dissem list is a wildcard
        and the entity passes by default. If the dissem list has elements
        the entity must be on the list.

        This check is something of a hack we need to excise -
        it short-circuits actual ABAC comparison logic, and it
        assumes that only one entity is involved in a key release operation -
        which is not a valid assumption.

        Additionally, it assumes an empty list is equivalent to valid auth - also a
        somewhat suspect assumption.

        Also, we should probably represent the dissem check as Just Another Attribute

        However, for backwards compat we're leaving this here, and assuming for now that the
        OIDC JWT's `preferred_username` field is "the entity" we should be using
        in the query.
        """
        if (dissem.size == 0) | dissem.contains(entity_id):
            return True
        else:
            logger.debug(f"Entity {entity_id} is not on dissem list {dissem.list}")
            raise AuthorizationError("Entity is not on dissem list.")

    def _check_attributes(
        self, data_attributes, entity_attributes, data_attribute_definitions
    ):
        access = True
        """Invoke the PDP over gRPC and obtain decisions.

        We should obtain 1 Decision per entity in the `entity_attributes` dict

        If all entity-level Decisions are True, then return True, else return false.
        """
        # BEGIN grpc
        logger.debug(f"Invoking local PDP: {local_pdp}")
        channel = grpc.insecure_channel(local_pdp)
        stub = accesspdp_pb2_grpc.AccessPDPEndpointStub(channel)

        logger.debug("Serializing KAS structures")
        attr_defs = pdp_grpc.convert_attribute_defs(data_attribute_definitions)
        entity_attrs = pdp_grpc.convert_entity_attrs(entity_attributes)
        data_attrs = pdp_grpc.convert_data_attrs(data_attributes)

        req = accesspdp_pb2.DetermineAccessRequest(
            data_attributes=data_attrs,
            entity_attribute_sets=entity_attrs,
            attribute_definitions=attr_defs,
        )

        logger.debug(f"Requesting decision - request is {MessageToJson(req)}")
        responses = stub.DetermineAccess(req)
        entity_responses = []

        if not responses:
            # when accesspdp returns empty response list, do not allow access
            access = False

        for response in responses:
            logger.debug(
                "Received response for entity %s with access decision %s"
                % (response.entity, response.access)
            )
            # Boolean AND the results - e.g. flip `access` to false if any response.Result is false
            access = access and response.access
            # Capture the per-data-attribute result details for each entity decision, for logging/etc
            logger.debug(
                f"Detailed data attribute results for entity {response.entity}: \n"
            )
            string_res = MessageToJson(response)
            logger.debug(f"{string_res}\n")
            entity_responses.append(string_res)
        # END grpc

        # Final check - KAS wants an error thrown if access == false
        if not access:
            raise AuthorizationError(f"Access Denied")
