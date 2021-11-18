import os
import requests
import time

from threading import Thread
from datetime import datetime
from replit import db
from utility import utils, routine, keep_alive

routine.delete_logs()

WEBHOOK = os.getenv('WEBHOOK')
USERNAME = 'Notifier'

db['status'] = f'Alive since {datetime.now()}'

server_s = Thread(target=keep_alive.run)
server_s.start()

while True:
    utils.logger('NOTIFIER: check')
    timers = None
    subs = None
    try:
        timers = utils.get_all_timers()
        subs = utils.get_subs()
    except Exception as e:
        utils.logger(str(e))
    res = None
    if timers is not None and subs is not None:
        for boss, timer in timers.items():
            msg = ''
            timer = int(timer) if timer is not None else None
            if timer is not None:
                minutes = utils.minutes_sub(int(timer))
                if 10 >= minutes >= 0:
                    utils.logger(f'NOTIFIER: {boss}:{minutes} preparing')
                    subs_id = subs[boss]
                    if subs_id:
                        msg += f'{boss} due in {utils.minutes_to_dhm(timer)}\n'
                        for sub_id in subs_id:
                            msg += f'<@{sub_id}>'
                    else:
                        msg += f'{boss} due in {utils.minutes_to_dhm(timer)}'
                    if len(msg) > 0:
                        res = requests.post(WEBHOOK,
                                            data={
                                                'username': USERNAME,
                                                'content': msg
                                            })
                        utils.logger(
                            f'NOTIFIER: res: {res.status_code}, sent: {msg}')
    utils.logger('NOTIFIER: finish check')
    if res and (res.status_code == 429):
        utils.logger('NOTIFIER: 429')
        os.system('kill 1')
    else:
        time.sleep(300)
