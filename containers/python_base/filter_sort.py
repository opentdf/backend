import logging
import os
import sys

from sqlalchemy import ARRAY, func, Integer
from sqlalchemy.orm import Session


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
            filters.append(getattr(model, key) <= value)
        elif key.endswith("__lt"):
            key = key.replace("__lt", "")
            filters.append(getattr(model, key) < value)
        elif key.endswith("__gte"):
            key = key.replace("__gte", "")
            filters.append(getattr(model, key) >= value)
        elif key.endswith("__gt"):
            key = key.replace("__gt", "")
            filters.append(getattr(model, key) > value)
        elif key.endswith("__ne"):
            key = key.replace("__ne", "")
            filters.append(getattr(model, key) != value)
        elif key.endswith("__eq"):
            key = key.replace("__eq", "")
            filters.append(getattr(model, key) == value)
        else:
            if isinstance(getattr(model, key).type, Integer):
                key = key.replace("__eq", "")
                filters.append(getattr(model, key) == value)
            elif isinstance(getattr(model, key).type, ARRAY):
                filters.append(
                    func.array_to_string(getattr(model, key), ",").ilike(
                        "%{}%".format(value)
                    )
                )
            else:
                filters.append(getattr(model, key).ilike("%{}%".format(value)))
    return filters


def get_sorter_by_args(model, args: list):
    sorters = []
    for key in args:
        if key[0] == "-":
            sorters.append(getattr(model, key[1:]).desc())
        else:
            sorters.append(getattr(model, key))
    return sorters


def get_query(request, model, authority: None, db: Session, filter_args: dict = {}, sort_args: list = []):
    logger.info("Filtering by [%s]", filter_args)
    logger.info("Sorting by [%s]", sort_args)
    logger.info(model)
    if authority is not None:
        org_name = add_filter_by_access_control(request)
    else:
        pass
    filter_args["namespace_id"] = db.query(authority).filter(authority.name == org_name).first()
    filters = get_filter_by_args(model, filter_args)
    sorters = get_sorter_by_args(model, sort_args)
    return db.query(model).filter(*filters).order_by(*sorters)
