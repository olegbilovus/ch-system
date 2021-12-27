import time
import requests
import os
from db import get_bosses_default

from datetime import datetime



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


def days_hours_mins_to_mins(array_values):
    days = 0
    hours = 0
    minutes = 0
    for value in array_values:
        if len(value) > 1:
            if value[-1] == 'd':
                days = int(value[:-1])
            elif value[-1] == 'h':
                hours = int(value[:-1])
            elif value[-1] == 'm':
                minutes = int(value[:-1])

    return (days * 24 * 60) + (hours * 60) + minutes


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
