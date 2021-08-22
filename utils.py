from replit import db
from datetime import datetime

import requests
import os
import time

API_URL = os.getenv('API_URL')
API_KEY = os.getenv('API_KEY')

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

LIST_BOSSES = list(BOSSES)

MINUTES_IN_A_DAY = 1440


def minutes_sub(timer):
    return timer - (round(time.time()) // 60)


def minutes_to_dhm(minutes):
    minutes = minutes_sub(minutes)
    negative = False
    if int(minutes) < 0:
        minutes *= -1
        negative = True
    days = minutes // MINUTES_IN_A_DAY
    minutes = minutes % MINUTES_IN_A_DAY
    hours = minutes // 60
    minutes = minutes % 60
    msg = f'{str(days) + "d " if days > 0 else ""}{str(hours) + "h " if hours > 0 else ""}{minutes}m'
    if not negative:
        return msg
    return '-' + msg


def get_all_timers():
    res = requests.post(f'{API_URL}/api/get',
                        headers={'X-ApiKey': API_KEY},
                        json={'bosses': LIST_BOSSES})
    try:
        return res.json()
    except Exception as e:
        logger(e)
        return None


def get_subs():
    res = requests.post(f'{API_URL}/api/getsubs',
                        headers={'X-ApiKey': API_KEY})
    return res.json()


def logger(msg):
    log = f'[{datetime.now()}] {msg}'
    print(log)
    db['logs'] = db['logs'] + log + '\n'
