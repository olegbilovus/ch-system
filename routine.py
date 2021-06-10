from replit import db
from datetime import date
from utils import minutes_sub, BOSSES
import db_utils

import utils
import time


def delete_logs():
    last_delete = date.today()
    try:
        last_delete = date.fromtimestamp(int(db['last_delete']))
    except KeyError:
        db['last_delete'] = round(time.time())
    days = (date.today() - last_delete).days
    utils.logger(f'DL: check, days: {days}')
    if days >= 10:
        db_utils.delete_logs()


def delete_old_timers():
    utils.logger('DOT: check')
    for key in db.keys():
        if key.isdigit() and key in BOSSES:
            timer = db[key]
            if timer is not None and minutes_sub(timer) <= -180:
                utils.logger(f'DOT: deleted {key}')
                db[key] = None
