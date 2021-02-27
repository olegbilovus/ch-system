import time
import utils

from replit import db

from utils import minutes_sub


def delete_old_timers():
    utils.logger('DOT: ready')
    while True:
        utils.logger('DOT: check')
        for key in db.keys():
            if key.isdigit():
                timer = db[key]
                if timer is not None and minutes_sub(timer) <= -180:
                    utils.logger(f'DOT: deleted {key}')
                    db[key] = None

        # 6h
        time.sleep(10800)


def delete_logs():
    while True:
        with open('log.txt', 'w') as logs:
            logs.write('--DELETED--\n')
        utils.logger('DL: deleted logs')

        # 30 days
        time.sleep(2592000)
