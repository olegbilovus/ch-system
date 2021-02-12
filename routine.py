from replit import db
from utils import minutes_sub
from datetime import datetime
import time


def delete_old_timers():
    print(f'DOT: ready at {datetime.now()}')
    while True:
        print(f'DOT: check at {datetime.now()}')
        for key in db.keys():
            if key.isdigit():
                timer = db[key]
                if timer != None and minutes_sub(timer) <= -180:
                    print(f'DOT: deleted {key} at {datetime.now()}')
                    db[key] = None

        # 6h
        time.sleep(10800)
