"""The Adjudicator adjudicates access to the wrapped key."""
import logging

import json

import grpc
import tdf3_kas_core.pdp_grpc as pdp_grpc

from tdf3_kas_core.errors import AdjudicatorError
from tdf3_kas_core.errors import AuthorizationError

from accesspdp.v1 import accesspdp_pb2_grpc, accesspdp_pb2
from attributes.v1 import attributes_pb2

logger = logging.getLogger(__name__)

local_pdp = 'localhost:50052'

class AccessPDP(object):
    """Adjudicator adjudicates.

    All checks to see whether the provided entity claims are sufficient to access the wrapped key split
    are in this model.

    The basic pattern is that failed checks raise errors. These are caught
    at the Web layer and converted to messages of the appropriate form.  If
    the entity claims pass all the tests without raising an error,
    then the authenticated entity who was issued the claims is assumed to be worthy.
    """

    def can_access(self, policy, claims, attribute_definitions):
        """Determine if the presented entity claims are worthy."""
        # Check to see if this claimset fails the dissem tests.
        self._check_dissem(policy.dissem, claims.user_id)
        # Then check the attributes
        self._check_attributes(policy.data_attributes, claims.entity_attributes, attribute_definitions)
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

    def _check_attributes(self, data_attributes, entity_attributes, data_attribute_definitions):
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

        req = accesspdp_pb2.DetermineAccessRequest(data_attributes=data_attrs, entity_attribute_sets=entity_attrs, attribute_definitions=attr_defs)

        logger.debug(f"Requesting decision - request is {dir(req)}")
        responses = stub.DetermineAccess(req)
        rule_results = []
        for response in responses:
            logger.debug("Received response for entity %s with access decision %s" %
                (response.entity, response.access))

            # Boolean AND the results - e.g. flip `access` to false if any response.Result is false
            access = access and response.access
            rule_results.append(response.results)
        # END grpc

        # Final check - KAS wants an error thrown if access == false
        if not access:
            raise AuthorizationError(f"Access Denied - Decision details: {json.dumps(rule_results)}")
