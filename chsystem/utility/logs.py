import os
from logtail import LogtailHandler
import logging
import sys


def get_logger(logtail=True, stdout=True, name=__name__):
    logger = logging.getLogger(name)
    logger.handlers = []

    if logtail:
        handler = LogtailHandler(source_token=os.getenv('LOGTAIL_TOKEN'))
        logger.addHandler(handler)
    if stdout:
        handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(handler)

    logger.setLevel(logging.INFO)

    return logger
