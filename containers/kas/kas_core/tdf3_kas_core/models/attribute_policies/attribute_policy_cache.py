"""AttributesCache, a reference for AttributePolicies."""
import logging

from tdf3_kas_core.errors import InvalidAttributeError
from tdf3_kas_core.server_timing import Timing

from .attribute_policy import AttributePolicy
from .attribute_policy import HIERARCHY
from .get_attribute_policy import get_attribute_policy

logger = logging.getLogger(__name__)


class AttributePolicyCache(object):
    """The AttributePolicyCache Class.

    This class caches AttributePolicies.
    """

    def __init__(self):
        """Construct an empty set."""
        self.__policies = {}  # URL keyed dict of AttributePolicies

    @property
    def size(self):
        """Return the number of policies in the cache."""
        return len(self.__policies)

    def load_config(self, attribute_policy_config):
        """
        Load policies defined in a config dict.

        Note that this translates un-modeled "attribute_objects"
        returned from rewrap plugins into modeled AttributePolicy
        objects.

        If you're wondering why specific plugin implementations
        don't perform/hide this translation to avoid abstraction leakage,
        join the club, and maybe redo this in a language with a static typing
        system that wouldn't allow this to happen in the first place.
        """
        if not attribute_policy_config:
            logger.warn("No attribute configs found")
            return
        Timing.start("attribute_load")
        logger.debug(
            "--- Fetch attribute_policy_config  [attribute = %s] ---",
            attribute_policy_config,
        )
        for attribute_object in attribute_policy_config:
            # use the policy constructor to validate the inputs
            authority_namespace = attribute_object["authorityNamespace"]
            attribute_name = attribute_object["name"]
            attribute_name_object = f"{authority_namespace}/attr/{attribute_name}"
            group_by_attr = ""
            if "group_by" in attribute_object:
                group_by_attr = "{}/attr/{}/value/{}".format(
                    attribute_object["group_by"]["authority"],
                    attribute_object["group_by"]["name"],
                    attribute_object["group_by"]["value"]
                )

            if "rule" in attribute_object:
                # specialize the arguments for the rule
                if attribute_object["rule"] == HIERARCHY:
                    if "order" not in attribute_object:
                        raise InvalidAttributeError(
                            """
                            Failed to create hierarchy policy
                             - no order array
                        """
                        )
                    policy = AttributePolicy(
                        attribute_name_object,
                        rule=attribute_object["rule"],
                        order=attribute_object["order"],
                        group_by=group_by_attr,
                    )
                else:  # No special options argument list
                    policy = AttributePolicy(
                        attribute_name_object,
                        rule=attribute_object["rule"],
                        group_by=group_by_attr,
                    )
            else:
                # Use the default rule
                policy = AttributePolicy(
                    attribute_name_object,
                    group_by=group_by_attr,
                )

            # Add to the cache
            logger.debug("--- cached  [policy = %s] ---", str(policy))
            if policy is not None:
                self.__policies[attribute_name_object] = policy
        Timing.stop("attribute_load")

    def get(self, attr_definition):
        # TODO rename AttributePolicy to AttributeDefinition -
        # makes more sense and distinguishes effectively between
        # AttributeDefinitions (attr with possible values)
        # and AttributeInstances (attr with concrete values)
        """Get an AttributePolicy."""
        try:
            count = 2
            while (attr_definition not in self.__policies) and (count > 0):
                ap = get_attribute_policy(attr_definition)
                if isinstance(ap, AttributePolicy):
                    self.__policies[attr_definition] = ap
                count = count - 1

            if attr_definition not in self.__policies:
                raise Exception()
            return self.__policies[attr_definition]
        except Exception as e:
            logger.exception(e)
            logger.setLevel(logging.DEBUG)  # dynamically escalate level
            return None
