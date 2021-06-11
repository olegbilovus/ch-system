import requests
import os

from replit import db
from datetime import datetime

API_URL = os.getenv('API_URL')
API_KEY = os.getenv('API_KEY')


def login(user_id, api_key):
    if user_id in db['users']:
        res = requests.post(f'{API_URL}/api/validate',
                            headers={'X-ApiKey': API_KEY},
                            json={
                                'user_id': user_id,
                                'api_key': api_key
                            })
        if res.status_code == 200:
            return True
    return False


def logger(msg):
    log = f'[{datetime.now()}] {msg}'
    print(log)
    with open('log.txt', 'a') as logs:
        logs.write(log + '\n')
    db['logs'] = db['logs'] + log + '\n'
