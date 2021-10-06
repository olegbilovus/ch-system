from replit import db
from datetime import datetime
from collections import Counter

import os

ROLES = os.getenv('ROLES').split(',')


def logger(msg):
    log = f'[{datetime.now()}] {msg}'
    print(log)
    db['logs'] = db['logs'] + log + '\n'


def count_roles(users):
    roles_count = {}
    for role in ROLES:
        roles_count[role] = 0
    for user in users:
        roles_count[ROLES[int(user['role'])]] += 1

    return roles_count
