"""The decision functions decide access."""

import logging

from tdf3_kas_core.errors import AuthorizationError

logger = logging.getLogger(__name__)


def all_of_decision(data_values, subject_claims):
    """Test all-of type attributes."""
    logger.debug("All-of decision function called")

    for dv in data_values:
        logger.debug("DV attrib: %s", dv.attribute)
        logger.debug(subject_claims.subject_attributes)
        for subject_id, subject_attributes in subject_claims.subject_attributes.items():
            subj_attr_cluster = subject_attributes.cluster(dv.namespace)
            if subj_attr_cluster is None:
                logger.debug(f"All-of criteria NOT satisfied for subject: {subject_id} - lacked attribute")
                raise AuthorizationError("AllOf not satisfied")
            if not data_values <= subj_attr_cluster.values:
                logger.debug(f"All-of criteria NOT satisfied for subject: {subject_id} - wrong attribute value")
                raise AuthorizationError("AllOf not satisfied")
    return True

def any_of_decision(data_values, subject_claims):
    """Test any_of type attributes."""
    logger.debug("Any-of decision function called")

    for dv in data_values:
        found_dv_match = False
        logger.debug("DV attrib: %s", dv.attribute)
        for subject_id, subject_attributes in subject_claims.subject_attributes.items():
            subj_attr_cluster = subject_attributes.cluster(dv.namespace)

            if subj_attr_cluster is None:
                logger.debug(f"Any-of criteria not satisfied for attr: {dv.attribute} on subject: {subject_id} - keep looking")
            else:
                intersect = data_values & subj_attr_cluster.values
                if len(data_values) == 0 or len(intersect) > 0:
                    logger.debug(f"Any-of criteria satisfied for attr: {dv.attribute} on subject: {subject_id}")
                    found_dv_match = True

        if not found_dv_match:
            logger.debug(f"Any-of criteria not satisfied - no subject in claims entitled with {dv.attribute}")
            raise AuthorizationError("AnyOf not satisfied")
        else:
            return True

def hierarchy_decision(data_values, subject_claims, order):
    """Test hierarchy decision function."""
    logger.debug("Hierarchical decision function called")

    # TODO this is a preexisting check - but why would we ever have more than one data value?
    # <attrnamespace>/<attrvalue> would be unique in all cases that matter to a PDP.
    if len(data_values) != 1:
        raise AuthorizationError("Hiearchy - must be one data value")
    data_value = next(iter(data_values))
    if data_value.value not in order:
        raise AuthorizationError("Hiearchy - data value not in attrib policy")
    data_rank = order.index(data_value.value)

    merged_subject_attr_values = set()

    #Mush all the subject attr values for this namespace into a single set,
    #then calc order on least-significant one
    for subject_id, subject_attributes in subject_claims.subject_attributes.items():
        # Get subject attrib key that == data attrib key
        subj_attr_cluster = subject_attributes.cluster(data_value.namespace)
        # Add a null value if no value is found - for purposes of Hierarchy comparison,
        # subject with "no value" always counts one lower than the lowest "valid" value in a
        # hierarchy comparison - that is, an automatic fail.

        if subj_attr_cluster is None:
            merged_subject_attr_values.add(None)
        else:
            merged_subject_attr_values.update(subj_attr_cluster.values)
        logger.debug("Attribute subject values for subject {} = {}".format(subject_id, merged_subject_attr_values))
        # return merged_subject_attr_values


    # Compute the rank of the subject attr value against the rank of the data value
    # While we only ever compare against a single value, we may have several
    # subject values to deal with - so we go with the value that has the least-significant index
    least_subj_rank = 0
    for val in merged_subject_attr_values:
        if val is None or val.value not in order:
            raise AuthorizationError("Hierarchy - subject missing hierarchy value, which is an automatic hierarchy failure")
        value_rank = order.index(val.value)
        print(f"VAL IS {value_rank} AND LEAST IS {least_subj_rank}")
        if value_rank >= least_subj_rank:
            least_subj_rank = value_rank

    # Compare the ranks to determine value satisfaction

    print(f"DATA VAL IS {data_rank} AND LEAST IS {least_subj_rank}")
    if least_subj_rank <= data_rank:
        logger.debug("Hierarchical criteria satisfied")
        return True

    # Y
    logger.debug("Hierarchical criteria not satisfied")
    raise AuthorizationError("Hierarchy - subject attribute value rank too low")
