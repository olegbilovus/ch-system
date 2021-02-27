import time
import utils
from datetime import datetime

from replit import db

from utils import minutes_sub


def delete_old_timers():
    utils.logger.info(f'DOT: ready at {datetime.now()}')
    while True:
        utils.logger.info(f'DOT: check at {datetime.now()}')
        for key in db.keys():
            if key.isdigit():
                timer = db[key]
                if timer is not None and minutes_sub(timer) <= -180:
                    utils.logger.info(
                        f'DOT: deleted {key} at {datetime.now()}')
                    db[key] = None

        # 6h
        time.sleep(10800)


def delete_logs():
    while True:
        with open('log.txt', 'w') as logs:
            logs.write('--DELETED--\n')
        utils.logger.info(f'DL: deleted logs at {datetime.now()}')

        # 30 days
        time.sleep(2592000)
