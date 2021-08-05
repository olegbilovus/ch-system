from replit import db
from datetime import datetime

import time

BOSSES = {
    '110': 30,
    '115': 35,
    '120': 40,
    '125': 45,
    '130': 50,
    '140': 55,
    '155': 60,
    '160': 65,
    '165': 70,
    '170': 80,
    '180': 90,
    '185': 75,
    '190': 85,
    '195': 95,
    '200': 105,
    '205': 115,
    '210': 125,
    '215': 135,
    'aggy': 1894,
    'mord': 2160,
    'hrung': 2160,
    'necro': 2160,
    'prot': 1190,
    'gele': 2880,
    'bt': 4320,
    'dino': 4320
}

SUB_SUFFIX = 's'


def minutes_add(timer):
    return round(time.time()) // 60 + timer


def minutes_sub(timer):
    return timer - (round(time.time()) // 60)


def get_timer(boss):
    if boss in BOSSES:
        try:
            return db[boss]
        except KeyError:
            return None
    else:
        return None


def set_timer(boss, timer):
    if boss in BOSSES:
        timer = int(timer)
        if timer == 0:
            db[boss] = None
        else:
            db[boss] = minutes_add(timer)
        return True
    return False


def get_subs(boss):
    if boss in BOSSES:
        subs = []
        boss_suffix = boss + SUB_SUFFIX
        try:
            subs = db[boss_suffix]
        except KeyError:
            db[boss_suffix] = subs
        return subs
    return None


def add_sub(boss, user_id):
    subs = get_subs(boss)
    if subs is not None and user_id not in subs:
        subs.append(user_id)
        db[boss + SUB_SUFFIX] = subs
        return True
    return False


def remove_sub(boss, user_id):
    subs = get_subs(boss)
    if subs and user_id in subs:
        subs.remove(user_id)
        db[boss + SUB_SUFFIX] = subs
        return True
    return False


def logger(msg):
    log = f'[{datetime.now()}] {msg}'
    print(log)
    #with open('log.txt', 'a') as logs:
        #logs.write(log + '\n')
    db['logs'] = db['logs'] + log + '\n'
