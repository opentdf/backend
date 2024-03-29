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


def get_query(table_to_query, filter_args: dict = {}, sort_args: list = []):
    logger.info("Filtering by [%s]", filter_args)
    logger.info("Sorting by [%s]", sort_args)

    filters = get_filter_by_args(table_to_query, filter_args)
    sorters = get_sorter_by_args(table_to_query, sort_args)
    return filters, sorters
