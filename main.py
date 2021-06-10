import requests
import time
import routine
import os
import utils

routine.delete_logs()

WEBHOOK = os.getenv('WEBHOOK')
USERNAME = 'Notifier'

while True:
    utils.logger('NOTIFIER: check')
    timers = utils.get_all_timers()
    subs = utils.get_subs()
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
            requests.post(WEBHOOK, data={'username': USERNAME, 'content': msg})
            utils.logger(f'NOTIFIER: sent {msg}')
    utils.logger('NOTIFIER: finish check')

    time.sleep(300)
