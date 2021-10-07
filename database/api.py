import secrets
import os

from replit import db
from utility import utils

key = os.getenv('KEY')


def create(user_id):
    api_keys = get_all()
    if user_id not in api_keys:
        api_key = secrets.token_hex(4)
        api_keys[user_id] = api_key
        db[key] = api_keys
        return api_key
    return None


def delete(user_id):
    api_keys = get_all()
    if user_id in api_keys:
        for boss in utils.BOSSES:
            remove_sub(boss, user_id)
        del api_keys[user_id]
        db[key] = api_keys
        return True
    return False


def edit_userid(user_id, new_user_id):
    api_keys = get_all()
    if user_id in api_keys:
        api_keys[new_user_id] = api_keys.pop(user_id)
        return True
    return False


def validate_apikey(user_id, apikey):
    api_keys = get_all()
    if user_id in api_keys and api_keys[user_id] == apikey:
        return True
    return False


def get(user_id):
    return db[key][user_id]


def get_all():
    return db[key]


def get_users():
    return list(dict(db[key]).keys())


def delete_all():
    del db[key]


def get_timer(boss):
    if boss in utils.BOSSES:
        try:
            return db[boss]
        except KeyError:
            return None
    else:
        return None


def set_timer(boss, timer):
    if boss in utils.BOSSES:
        timer = int(timer)
        if timer == 0:
            db[boss] = None
        else:
            db[boss] = utils.minutes_add(timer)
        return True
    return False


def get_subs(boss):
    if boss in utils.BOSSES:
        subs = []
        boss_suffix = boss + utils.SUB_SUFFIX
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
        db[boss + utils.SUB_SUFFIX] = subs
        return True
    return False


def remove_sub(boss, user_id):
    subs = get_subs(boss)
    if subs and user_id in subs:
        subs.remove(user_id)
        db[boss + utils.SUB_SUFFIX] = subs
        return True
    return False
