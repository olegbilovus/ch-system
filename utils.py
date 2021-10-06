import requests
import os
import time

from replit import db
from datetime import datetime

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
ROLES = ['Recruit', 'Clansman', 'Guardian', 'General', 'Admin']
ROLES_COLORS = ['#f1c21b', '#e67f22', '#3398dc', '#9a59b5', '#1abc9b']
WEB_DISCORD = os.getenv('WEB_DISCORD')
WB_USERNAME = 'WebToDiscord'


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


def login(user_id, api_key):
    users = db['users']
    if user_id in users:
        res = requests.post(f'{API_URL}/api/validate',
                            headers={'X-ApiKey': API_KEY},
                            json={
                                'user_id': user_id,
                                'api_key': api_key
                            })
        if res.status_code == 200:
            return users[user_id]
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


def create_user(user_id, role, main):
    users = db['users']
    if user_id not in users:
        res = requests.post(f'{API_URL}/api/create',
                            headers={'X-ApiKey': API_KEY},
                            json={'user_id': user_id})
        if res.status_code == 200:
            users[user_id] = {'role': role, 'main': main}
            db['users'] = users
            return res.content
    return None


def delete_user(user_id):
    users = db['users']
    if user_id in users:
        res = requests.post(f'{API_URL}/api/delete',
                            headers={'X-ApiKey': API_KEY},
                            json={'user_id': user_id})
        if res.status_code == 200:
            del users[user_id]
            db['users'] = users
            return True
    return False


def change_role(user_id, role):
    users = db['users']
    if user_id in users:
        users[user_id]['role'] = role
        db['users'] = users
        return True
    return False


def boss_sub(api_key, boss):
    res = requests.post(f'{API_URL}/api/sub',
                        headers={'X-ApiKey': api_key},
                        json={'boss': boss})
    if res.status_code == 200:
        return True
    return False


def boss_unsub(api_key, boss):
    res = requests.post(f'{API_URL}/api/unsub',
                        headers={'X-ApiKey': api_key},
                        json={'boss': boss})
    if res.status_code == 200:
        return True
    return False


def boss_reset(api_key, boss, timer):
    res = requests.post(f'{API_URL}/api/set',
                        headers={'X-ApiKey': api_key},
                        json={
                            'boss': boss,
                            'timer': timer
                        })
    if res.status_code == 200:
        return True
    return False


def web_to_discord(boss, timer):
    res = requests.post(WEB_DISCORD,
                        data={
                            'username': WB_USERNAME,
                            'content': f'Set {boss} {timer}m'
                        })
    if res.status_code == 200:
        return True
    return False


def logger(msg):
    log = f'[{datetime.now()}] {msg}'
    print(log)
    db['logs'] = db['logs'] + log + '\n'


def get_logs():
    return db['logs']
