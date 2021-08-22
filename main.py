import requests
import time
import routine
import os
import utils
import server

from datetime import datetime
from threading import Thread
from replit import db

routine.delete_logs()

WEBHOOK = os.getenv('WEBHOOK')
USERNAME = 'Notifier'

db['status'] = f'Alive since {datetime.now()}'

server_s = Thread(target=server.run)
server_s.start()

while True:
    utils.logger('NOTIFIER: check')
    timers = utils.get_all_timers()
    subs = utils.get_subs()
    res = None
    if timers is not None and subs is not None:
        msg = ''
        for boss, timer in timers.items():
            timer = int(timer) if timer is not None else None
            if timer is not None:
                minutes = utils.minutes_sub(int(timer))
                if 10 >= minutes >= 0:
                    utils.logger(f'NOTIFIER: {boss}:{minutes} preparing')
                    subs_id = subs[boss]
                    if subs_id:
                        msg += f'{boss} due in {utils.minutes_to_dhm(timer)} '
                        for sub_id in subs_id:
                            msg += f'<@{sub_id}>'
                        msg += '\n'
                    else:
                        msg += f'{boss} due in {utils.minutes_to_dhm(timer)}\n'
        if len(msg) > 0:
            res = requests.post(
                WEBHOOK, data={'username': USERNAME, 'content': msg})
            utils.logger(f'NOTIFIER: res: {res.status_code}, sent: {msg}')
    utils.logger('NOTIFIER: finish check')
    if res and res.status_code >= 400:
        utils.logger('NOTIFIER: 429')
        time.sleep(3600)
    else:
        time.sleep(300)
