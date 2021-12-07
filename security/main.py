import requests
import os
import time
import server
import numpy as np

from threading import Thread
from replit import db
from datetime import datetime
from utility import utils, routine
from matplotlib import pyplot as plt

routine.delete_logs()

WEBHOOKS = os.getenv('WEBHOOKS').split(',')
TAGS = os.getenv('TAGS').split(',')
URL3 = os.getenv('URL3')
IMG_PATH_LVLS = 'security/lvls.png'
IMG_PATH_CLASSES = 'security/classes.png'
IMG_PATH_LVL_WARRIOR = 'security/lvl_warrior.png'
IMG_PATH_LVL_DRUID = 'security/lvl_druid.png'
IMG_PATH_LVL_MAGE = 'security/lvl_mage.png'
IMG_PATH_LVL_RANGER = 'security/lvl_ranger.png'
IMG_PATH_LVL_ROGUE = 'security/lvl_rogue.png'
TICK = 10

db['status'] = f'Alive since {datetime.now()}'

server_s = Thread(target=server.run)
server_s.start()


def send_msg(msg):
    for WEBHOOK in WEBHOOKS:
        res = requests.post(WEBHOOK,
                            data={
                                'username': 'ebk-check',
                                'content': msg
                            })
        utils.logger(f'{res.status_code}\n{msg}')


def send_img(img_path):
    for WEBHOOK in WEBHOOKS:
        with open(img_path, 'rb') as file:
            res = requests.post(WEBHOOK,
                                files={
                                    'file': (file.name, file, 'application/octet-stream')
                                },
                                data={
                                    'username': 'ebk-check'
                                })
            utils.logger(f'{res.status_code}\n{img_path}')


def create_plot_pie_file(title, data, labels, img_path):
    fig1, ax1 = plt.subplots()
    ax1.pie(data, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90)
    ax1.axis('equal')
    plt.title(title)
    plt.savefig(img_path)
    plt.close('all')


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
            levels[level] = {
                'Warrior': 0,
                'Druid': 0,
                'Mage': 0,
                'Ranger': 0,
                'Rogue': 0
            }
            levels[level][class_] = 1
        else:
            levels[level][class_] += 1

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

    levels_stats = {}
    warrior = {}
    druid = {}
    mage = {}
    ranger = {}
    rogue = {}
    for lvl in range(0, max(levels.keys()) + 1, TICK):
        lvl_str = f'{lvl}-{lvl+TICK - 1}'
        levels_stats[lvl_str] = 0
        warrior[lvl_str] = 0
        druid[lvl_str] = 0
        mage[lvl_str] = 0
        ranger[lvl_str] = 0
        mage[lvl_str] = 0
        rogue[lvl_str] = 0
        for lvl_ in range(lvl, lvl + TICK):
            if lvl_ in levels:
                levels_stats[lvl_str] += sum(levels[lvl_].values())
                warrior[lvl_str] += levels[lvl_]['Warrior']
                druid[lvl_str] += levels[lvl_]['Druid']
                mage[lvl_str] += levels[lvl_]['Mage']
                ranger[lvl_str] += levels[lvl_]['Ranger']
                rogue[lvl_str] += levels[lvl_]['Rogue']

        if levels_stats[lvl_str] == 0:
            del levels_stats[lvl_str]
        if warrior[lvl_str] == 0:
            del warrior[lvl_str]
        if druid[lvl_str] == 0:
            del druid[lvl_str]
        if mage[lvl_str] == 0:
            del mage[lvl_str]
        if ranger[lvl_str] == 0:
            del ranger[lvl_str]
        if rogue[lvl_str] == 0:
            del rogue[lvl_str]

    create_plot_pie_file('Level of current members',
                         levels_stats.values(), levels_stats.keys(), IMG_PATH_LVLS)
    send_img(IMG_PATH_LVLS)
    create_plot_pie_file('Classes of current members',
                         classes.values(), classes.keys(), IMG_PATH_CLASSES)
    send_img(IMG_PATH_CLASSES)
    create_plot_pie_file('Warrior', warrior.values(),
                         warrior.keys(), IMG_PATH_LVL_WARRIOR)
    send_img(IMG_PATH_LVL_WARRIOR)
    create_plot_pie_file('Druid', druid.values(),
                         druid.keys(), IMG_PATH_LVL_DRUID)
    send_img(IMG_PATH_LVL_DRUID)
    create_plot_pie_file('Mage', mage.values(), mage.keys(), IMG_PATH_LVL_MAGE)
    send_img(IMG_PATH_LVL_MAGE)
    create_plot_pie_file('Ranger', ranger.values(),
                         ranger.keys(), IMG_PATH_LVL_RANGER)
    send_img(IMG_PATH_LVL_RANGER)
    create_plot_pie_file('Rogue', rogue.values(),
                         rogue.keys(), IMG_PATH_LVL_ROGUE)
    send_img(IMG_PATH_LVL_ROGUE)

    time.sleep(3600)
