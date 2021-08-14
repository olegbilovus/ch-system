from threading import Thread
from replit import db
from datetime import datetime
from flos import Session

import server
import utils
import requests
import os
import time
import routine

routine.delete_logs()

WEBHOOK = os.getenv('WEBHOOK')
USERNAME = os.getenv('USERNAME')
ADMINS = os.getenv('ADMINS').split(',')
TAG_ADMINS = os.getenv('TAG_ADMINS')

db['status'] = f'Alive since {datetime.now()}'

server_s = Thread(target=server.run)
server_s.start()

session = Session(os.getenv('USER'), os.getenv('PASS'), os.getenv('CLAN'))
session.login()

while True:
    utils.logger(f'{USERNAME}: check')
    res = None
    try:
        users = session.get_users()
        users_unauthorized = session.check_admins(users, ADMINS)
        msg = f'All good, {len(users)} users in Flos'
        if users_unauthorized:
            msg = f'<@&{TAG_ADMINS}> The following users got Admin, an attemp to remove it was made, please verify\n'
            for user in users_unauthorized:
                msg += f'{user}\n'
        res = requests.post(WEBHOOK,
                            data={
                                'username': USERNAME,
                                'content': msg
                            })
    except Exception as e:
        utils.logger(str(e))
        try:
            session.login()
        except Exception as e:
            utils.logger(str(e))

    utils.logger(f'{USERNAME}: res: {res.status_code}, sent: {msg}')
    utils.logger(f'{USERNAME}: finish check')

    if res and res.status_code >= 400:
        utils.logger(f'{USERNAME}: 429')
        time.sleep(3600)
    else:
        time.sleep(300)
