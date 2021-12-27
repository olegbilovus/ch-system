import os
import utils
import pymongo
import bcrypt

db = pymongo.MongoClient(os.getenv('URL_MONGODB'))[os.getenv('DB_NAME')]


def get_bosses_default():
    return db.boss.find({})


def get_bosses_type():
    return db.boss_type.find({})


def get_user(main_account, server):
    return db.user.find({'_id': f'{main_account}_{server}'})

def create(main_account,
           pw,
           role,
           server,
           clan,
           discordID=None,
           alts=[],
           bans=[],
           notes=[],
          change_pw=False):
              
    if get_user(main_account, server) is not None:
        return {'success': False, 'msg': 'User already exists'}

    id_acc = f'{main_account}_{server}'
        
    db.user.insert_one({
        '_id': id_acc,
        'main_account': main_account,
        'role': role,
        'server': server,
        'bosses_subbed': [],
        'clan': clan,
        'discordID': discordID
    })
        
    db.user_details.insert_one({
        '_id': id_acc,
        'alts': alts,
        'bans': bans,
        'notes': notes
    })
    
    db.user_sensitive.insert_one({
        '_id': id_acc,
        'hash_pw': bcrypt(str.encode(pw), bcrypt.gensalt()).decode(),
        'change_pw': change_pw
    })

    db.user_stats.insert_one({
        '_id': id_acc,
        'last_login': 0,
        'count_login': 0,
        'count_bosses_reset': 0
    })

    return {'success': True, 'msg': 'User account created'}


def delete(main_account, server):
    if get_user(main_account, server) is None:
        return {'success': False, 'msg': 'User does not exists'}

    id_acc = f'{main_account}_{server}'
    
    db.user.delete_one({'_id': id_acc})
    db.user_details.delete_one({'_id': id_acc})
    db.user_sensitive.delete_one({'_id': id_acc})
    db.user_stats.delete_one({'_id': id_acc})


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


BOSSES = get_bosses_default()
BOSSES_TYPE = get_bosses_type()
