import requests
import os
import time

from threading import Thread
from replit import db
from datetime import datetime
from utility import utils, routine, keep_alive

routine.delete_logs()

WEBHOOK = os.getenv('WEBHOOK')
WEBHOOK2 = os.getenv('WEBHOOK2')
TAGS = os.getenv('TAGS').split(',')
URL3 = os.getenv('URL3')

db['status'] = f'Alive since {datetime.now()}'

server_s = Thread(target=keep_alive.run)
server_s.start()

def send_msg(msg):
    res1 = requests.post(WEBHOOK,
                         data={
                             'username': 'ebk-check',
                             'content': msg
                         })
    res2 = requests.post(WEBHOOK2,
                         data={
                             'username': 'ebk-check',
                             'content': msg
                         })

    utils.logger(f'{res1.status_code}, {res2.status_code}\n{msg}')

msg = f'\nFull list of people who joined EBK:\n{db["ebk_members"]}'
send_msg(msg)

while True:
    json = requests.get(URL3).json()
    members = json['RankingDataList']
    members_db = db['ebk_members']
    str_to_send = '\nCurrent EBK members:\n'
    new_members = False
    for member in members:

        name = member['Name']
        level = member['Level']
        class_name = member['ClassName']

        if name not in members_db:
            new_members = True
            members_db.append(name)
            str_to_send += '--'

        str_to_send += f'{name} {class_name} {level}\n'

    str_to_send += f'number members: {json["TotalResults"]}'

    if new_members:
        db['ebk_members'] = members_db
        str_to_send += '\n@everyone'

    send_msg(str_to_send)

    time.sleep(3600)
