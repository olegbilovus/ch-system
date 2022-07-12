import os
from logtail import LogtailHandler
import logging
import sys
from dotenv import load_dotenv

load_dotenv()
if os.getenv('LOGTAIL_TOKEN') is not None:
    print('Loaded successfully env variables')
else:
    print('Failed to load env variables')
    sys.exit(1)

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
