from replit import db
import utils
import time


def get_user(user_id):
    users = db['users']
    if user_id in users:
        return users[user_id]
    return None


def get_users():
    return db['users']


def change_role(user_id, role):
    users = db['users']
    if user_id in users:
        users[user_id]['role'] = role
        db['users'] = users
        return True
    return False


def write_logs_file(file_name='tmp.txt'):
    with open(file_name, 'w') as logs:
        logs.write(db['logs'])


def delete_logs():
    with open('log.txt', 'w') as logs:
        logs.write('--DELETED--\n')
        db['logs'] = ''
        utils.logger('DL: deleted logs')
        db['last_delete'] = str(round(time.time()))
