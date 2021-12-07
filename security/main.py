import requests
import os
import time
import server

from threading import Thread
from replit import db
from datetime import datetime
from utility import utils, routine
from matplotlib import pyplot as plt

routine.delete_logs()

WEBHOOK = os.getenv('WEBHOOK')
TAGS = os.getenv('TAGS').split(',')
URL3 = os.getenv('URL3')
IMG_PATH_LVLS = 'security/lvls.png'
IMG_PATH_CLASSES = 'security/classes.png'

db['status'] = f'Alive since {datetime.now()}'

server_s = Thread(target=server.run)
server_s.start()


def send_msg(msg):
    res = requests.post(WEBHOOK,
                        data={
                            'username': 'ebk-check',
                            'content': msg
                        })
    utils.logger(f'{res.status_code}\n{msg}')


def send_img(img_path):
    with open(img_path, 'rb') as file:
        res = requests.post(WEBHOOK,
                            files={
                                'file': (file.name, file, 'application/octet-stream')
                            },
                            data={
                                'username': 'ebk-check'
                            })
        utils.logger(f'{res.status_code}\n{img_path}')


def create_plot_file(title, data, labels, img_path):
    fig1, ax1 = plt.subplots()
    ax1.pie(data, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90)
    ax1.axis('equal')
    plt.title(title)
    plt.savefig(img_path)
    plt.close(fig1)


db['ebk_members'] = sorted(db['ebk_members'])
msg = f'------__***Full list of people who joined EBK***__------\n'
for member in db['ebk_members']:
    msg += f'{member}, '
send_msg(msg)

while True:
    json = requests.get(URL3).json()
    db['ebk_json_current'] = json
    members = sorted(json['RankingDataList'], key=lambda v: v['Name'])
    members_db = db['ebk_members']
    str_to_send = '------__***Current EBK members***__------\n'
    new_members = False
    levels = {}
    classes = {
        'Warrior': 0,
        'Druid': 0,
        'Mage': 0,
        'Ranger': 0,
        'Rogue': 0
    }
    for member in members:

        name = member['Name']
        level = member['Level']
        class_ = member['ClassName']

        if level not in levels:
            levels[level] = 1
        else:
            levels[level] += 1

        classes[class_] += 1

        if name not in members_db:
            new_members = True
            members_db.append(name)
            str_to_send += f'--__***{name}***__\n'
        else:
            str_to_send += f'{name}\n'

    str_to_send += f'number members: {json["TotalResults"]}'

    if new_members:
        db['ebk_members'] = members_db
        str_to_send += '\n@everyone'

    send_msg(str_to_send)

    create_plot_file('Level of current members',
                     levels.values(), levels.keys(), IMG_PATH_LVLS)
    send_img(IMG_PATH_LVLS)
    create_plot_file('Classes of current members',
                     classes.values(), classes.keys(), IMG_PATH_CLASSES)
    send_img(IMG_PATH_CLASSES)

    time.sleep(3600)
