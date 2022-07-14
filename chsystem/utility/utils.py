import time
import requests
import os

from replit import db
from datetime import datetime

_429 = 1200

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

SUB_SUFFIX = 's'


def minutes_sub(timer):
    return timer - (round(time.time()) // 60)


def minutes_add(timer):
    return round(time.time()) // 60 + timer


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





def get_timer(boss):
    if boss in BOSSES:
        res = requests.post(f'{API_URL}/api/get',
                            headers={'X-ApiKey': API_KEY},
                            json={'bosses': [boss]})
        try:
            return res.json()[boss]
        except Exception as e:
            logger(e)
            return None
    else:
        return None


def get_all_timers():
    res = requests.post(f'{API_URL}/api/get',
                        headers={'X-ApiKey': API_KEY},
                        json={'bosses': LIST_BOSSES})
    try:
        return res.json()
    except Exception as e:
        logger(e)
        return None


def set_timer(boss, timer):
    if boss in BOSSES:
        res = requests.post(f'{API_URL}/api/set',
                            headers={'X-ApiKey': API_KEY},
                            json={
                                'boss': boss,
                                'timer': int(timer)
                            })
        if res.status_code == 200:
            return True
    return False


def get_subs():
    res = requests.post(f'{API_URL}/api/getsubs',
                        headers={'X-ApiKey': API_KEY})
    return res.json()


def separator_label(category, separator='---------------------------------'):
    return separator + '\n' + category + '\n'


class Message:
    def __init__(self, content, author):
        self.content = content
        self.length = len(content)
        self.author_mention = author.mention
        self.author_id = author.id
        self.author_name = str(author)

    def __str__(self):
        return f'content:{self.content}, length:{self.length}, mention:{self.author_mention}, id:{self.author_id}'


def logger(msg):
    log = f'[{datetime.now()}] {msg}'
    print(log)
    db['logs'] = db['logs'] + log + '\n'


def status(down):
    status_message = ''
    if down:
        logger('429')
        db['429'] = True
        status_message = f'Down for 20mins since {datetime.now()}'
    else:
        db['429'] = False
        status_message = f'Alive since {datetime.now()}'
    db['status'] = status_message


def get_logs():
    return db['logs']
