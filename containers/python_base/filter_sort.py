import logging
import os
import sys

from sqlalchemy import ARRAY, func, Integer
from sqlalchemy.orm import Session
from .access_control import add_filter_by_access_control


from .access_control import add_filter_by_access_control
logging.basicConfig(
    stream=sys.stdout, level=os.getenv("SERVER_LOG_LEVEL", "CRITICAL").upper()
)
logger = logging.getLogger(__package__)


def get_filter_by_args(model, dict_args: dict):
    filters = []
    for key, value in dict_args.items():  # type: str, any
        if key.endswith("__lte"):
            key = key.replace("__lte", "")
            filters.append(getattr(model.c, key) <= value)
        elif key.endswith("__lt"):
            key = key.replace("__lt", "")
            filters.append(getattr(model.c, key) < value)
        elif key.endswith("__gte"):
            key = key.replace("__gte", "")
            filters.append(getattr(model.c, key) >= value)
        elif key.endswith("__gt"):
            key = key.replace("__gt", "")
            filters.append(getattr(model.c, key) > value)
        elif key.endswith("__ne"):
            key = key.replace("__ne", "")
            filters.append(getattr(model.c, key) != value)
        elif key.endswith("__eq"):
            key = key.replace("__eq", "")
            filters.append(getattr(model.c, key) == value)
        else:
            if isinstance(getattr(model.c, key).type, Integer):
                key = key.replace("__eq", "")
                filters.append(getattr(model.c, key) == value)
            elif isinstance(getattr(model.c, key).type, ARRAY):
                filters.append(
                    func.array_to_string(getattr(model.c, key), ",").ilike(
                        "%{}%".format(value)
                    )
                )
            else:
                filters.append(getattr(model.c, key).ilike("%{}%".format(value)))
    return filters


def get_sorter_by_args(model, args: list):
    sorters = []
    for key in args:
        if key[0] == "-":
            sorters.append(getattr(model.c, key[1:]).desc())
        else:
            sorters.append(getattr(model.c, key))
    return sorters


def get_query(request, metadata, db: Session, filter_args: dict = {}, sort_args: list = []):
    logger.info("Filtering by [%s]", filter_args)
    logger.info("Sorting by [%s]", sort_args)
    host = request.headers.get("host", "").split(":")[0].lower()

    if host == "attributes":
        org_name = add_filter_by_access_control(request)
        attribute_ns = metadata.tables['tdf_attribute.attribute_namespace']
        query = db.query(attribute_ns).filter(attribute_ns.c.name == org_name).all()
        table_to_query = metadata.tables['tdf_attribute.attribute']
    else:
        table_to_query = metadata.tables['tdf_entitlement.entity_attribute']

    if org_name is not None:
        for row in query:
            filter_args["namespace_id"] = row.id

    filters = get_filter_by_args(table_to_query, filter_args)
    sorters = get_sorter_by_args(table_to_query, sort_args)
    return db.query(table_to_query).filter(*filters).order_by(*sorters)
