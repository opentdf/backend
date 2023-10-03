import logging
import os
import sys
import json

class JsonFormatter(logging.Formatter):
    def __init__(self):
        super(JsonFormatter, self).__init__()

    def format(self, record):
        json_record = {}
        json_record["levelname"] = record.levelname
        json_record["name"] = record.name
        json_record["message"] = record.getMessage()
        return json.dumps(json_record)


def enable_json_logging():
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JsonFormatter())

    logging.basicConfig(
        stream=sys.stdout, level=os.getenv("SERVER_LOG_LEVEL", "CRITICAL").upper()
    )

    logger = logging.getLogger()
    logger.handlers = [handler] # replace current handler with json handler
