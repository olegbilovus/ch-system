from replit import db
import utils
import time


def get_all_key_values():
    db_kv = {}
    for key in db.keys():
        db_kv[key] = db[key]
    return db_kv


def print_db(db_kv):
    for key, value in db_kv.items():
        print(f'{key}: {value}')


def write_logs_file(file_name='tmp.txt'):
    with open(file_name, 'w') as logs:
        logs.write(db['logs'])


def delete_logs():
    with open('log.txt', 'w') as logs:
        logs.write('--DELETED--\n')
        db['logs'] = ''
        utils.logger('DL: deleted logs')
        db['last_delete'] = str(round(time.time()))
