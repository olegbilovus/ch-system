from replit import db
from utils import BOSSES


def delete_all_subs():
    for key in db.keys():
        if key.endswith('sub'):
            print(key)
            del db[key]


def get_all_key_values():
    db_kv = {}
    for key in db.keys():
        db_kv[key] = db[key]
    return db_kv


def print_db(db_kv):
    for key, value in db_kv.items():
        print(f'{key}: {value}')


def get_all_bosses():
    return {boss: timer for (boss, timer) in db.items() if boss in BOSSES}


if __name__ == '__main__':
    print(get_all_bosses())
