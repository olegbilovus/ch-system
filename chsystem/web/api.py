import requests
import os

from replit import db
from utils import API_URL, API_KEY

ROLES = ['Recruit', 'Clansman', 'Guardian', 'General', 'Admin']
ROLES_COLORS = ['#f1c21b', '#e67f22', '#3398dc', '#9a59b5', '#1abc9b']
WEB_DISCORD = os.getenv('WEB_DISCORD')
WB_USERNAME = 'WebToDiscord'


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


def get_user(user_id):
    users = db['users']
    if user_id in users:
        return users[user_id]
    return None


def get_users():
    return db['users']


def create_user_local(user_id, role, main):
    users = db['users']
    if user_id not in users:
        users[user_id] = {'role': role, 'main': main}
        db['users'] = users
        return True
    return False
