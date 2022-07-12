import os
from logtail import LogtailHandler
import logging
import sys
from dotenv import load_dotenv

load_dotenv()
if os.getenv('DB_URL') is not None:
    print('Loaded successfully env variables')
else:
    sys.exit('Failed to load env variables')


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
