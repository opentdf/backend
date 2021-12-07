"""ClaimsAttributes."""

import logging

from tdf3_kas_core.errors import InvalidAttributeError

from .attribute_set import AttributeSet
from .attribute_value import AttributeValue

logger = logging.getLogger(__name__)


class ClaimsAttributes(AttributeSet):
    """ClaimsAttributes."""

    # TODO This object model is whack, I don't get why AttributeSet exists
    # We're just putting simple structures in lists, we don't need custom classes for that.
    @classmethod
    def create_from_raw(cls, raw_claims_attributes):
        """Construct a dict of ClaimsAttributes for each subject (keyed by subject ID) from raw data (dict)."""
        subjects = {}

        logger.debug("RAW CLAIMS IS IS: {}".format(raw_claims_attributes))
        for subject in raw_claims_attributes:
            subjectname = subject['subject_identifier']
            subjectattrs = subject['subject_attributes']
            logger.debug("SUBJECTATTRS IS: {}".format(subjectattrs))
            subject_attribute_set = cls()
            for attributeObj in subjectattrs:
                if "attribute" in attributeObj:
                    logger.debug("AttributeOBJ IS: {}".format(attributeObj))
                    logger.debug("AttributeOBJ ATTRIB IS: {}".format(attributeObj['attribute']))
                    subject_attribute_set.add(AttributeValue(attributeObj['attribute']))
                elif "url" in attributeObj:
                    logger.warning("DEPRECATED - attribute 'url' should be 'attribute'")
                    subject_attribute_set.add(AttributeValue(attributeObj['url']))
                else:
                    msg = f"'attribute' field missing = {attribute}"
                    logger.error(msg)
                    logger.setLevel(logging.DEBUG)  # dynamically escalate level
                    raise InvalidAttributeError(msg)
            subjects[subjectname] = subject_attribute_set

        return subjects

    @classmethod
    def create_from_list(cls, subject_id, attr_list):
        """Load subject attributes from a list of raw values and a subject identifier"""
        subjects = {}
        ea = cls()
        for attr_value in attr_list:
            ea.add(AttributeValue(attr_value["attribute"]))
        subjects[subject_id] = ea
        return subjects
