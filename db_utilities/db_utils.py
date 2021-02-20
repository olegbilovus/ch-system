from replit import db


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


if __name__ == '__main__':
    delete_all_subs()