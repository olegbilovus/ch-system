from logtail import LogtailHandler
import logging
import sys


def get_logger(name, token=None, logtail=True, stdout=True, stderr=False):
    logger = logging.getLogger(name)
    logger.handlers = []

    if logtail:
        handler = LogtailHandler(source_token=token)
        logger.addHandler(handler)
    if stdout:
        handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(handler)
    if stderr:
        handler = logging.StreamHandler(sys.stderr)
        logger.addHandler(handler)

    logger.setLevel(logging.INFO)

    return logger
