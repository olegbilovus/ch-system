from replit import db
from datetime import date
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
