"""gRPC helper functions for PDP invocation - mostly type conversions
between internal KAS objects and gRPC types"""
import logging
from attributes.v1 import attributes_pb2
from tdf3_kas_core.errors import InvalidAttributeError

logger = logging.getLogger(__name__)

ALL_OF = "allOf"
ANY_OF = "anyOf"
HIERARCHY = "hierarchy"

def convert_attribute_defs(attribute_defs):
    """Load attribute definitions from a dict."""
    if not attribute_defs:
        logger.warn("No attribute definitions found!")
        return
    logger.debug(
        "--- attribute definitions  [attribute def = %s] ---",
        attribute_defs,
    )

    pb_attr_defs = []
    for attribute_def in attribute_defs:
        # use the policy constructor to validate the inputs
        authority = attribute_def["authorityNamespace"]
        name = attribute_def["name"]

        # TODO This is an existing KAS default - if no definition (or incomplete definition)
        # found then "create" a new attribute definition with a "default" ALL_OF rule.
        # This is useful for development but in terms of access logic almost always entirely wrong.
        #
        # We should, arguably, fail with an error if we cannot fetch an attribute definition with a rule
        # from an attribute authority for EVERY data attribute canonical name.
        pb_attr_def = attributes_pb2.AttributeDefinition(authority=authority, name=name, rule=ALL_OF)

        if "rule" in attribute_def:
            pb_attr_def.rule = attribute_def["rule"]
        else:
            pb_attr_def.rule = ANY_OF
        if "order" in attribute_def:
            pb_attr_def.rule = attribute_def["order"]
        if "state" in attribute_def:
            pb_attr_def.state = attribute_def["state"]
        if "group_by" in attribute_def:
            pb_attr_def.group_by = attributes_pb2.AttributeInstance(
                authority=attribute_def["group_by"].authority,
                name=attribute_def["group_by"].name,
                value=attribute_def["group_by"].value
            )

        pb_attr_defs.append(pb_attr_def)

    return pb_attr_defs


def convert_entity_attrs(entity_attributes):
    """Load attribute instances from a dict."""
    if not entity_attributes:
        logger.warn("No entity attributes found!")
        return
    logger.debug(
        "--- entity attribute instances  [attribute instances = %s] ---",
        entity_attributes,
    )

    pb_entity_attr_dict = {}
    for entity_id, entity_attributes in entity_attributes.items():
        pb_entity_attrs = []
        for entity_attribute in entity_attributes:
            pb_entity_attrs.append(attributes_pb2.AttributeInstance(
                authority=entity_attribute.authority,
                name=entity_attribute.name,
                value=entity_attribute.value
            ))

        pb_entity_attr_dict[entity_id] = pb_entity_attrs

    return pb_entity_attr_dict

def convert_data_attrs(data_attributes):
    """Load attribute instances from a dict."""
    if not data_attributes:
        logger.warn("No data attributes found!")
        return
    logger.debug(
        "--- data attribute instances  [attribute instances = %s] ---",
        data_attributes,
    )

    pb_data_attrs = []
    for data_attribute in data_attributes:
            pb_data_attrs.append(attributes_pb2.AttributeInstance(
                authority=data_attribute.authority,
                name=data_attribute.name,
                value=data_attribute.value
            ))

    return pb_data_attrs
