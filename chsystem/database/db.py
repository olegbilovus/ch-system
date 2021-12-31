import time

import bcrypt
import pymongo
from dotenv import dotenv_values

config = dotenv_values('.env')

db = pymongo.MongoClient(config['URL_MONGODB'])[config['DB_NAME']]

ERROR_MESSAGES = {
    'boss_not_found': 'Boss not found',
    'user_not_found': 'User not found',
    'user_already_exists': 'User already exists',
    'user_no_discord_id': 'User has no discord id',
    'role_not_found': 'Role not found',
    'clan_not_found': 'Clan not found',
    'clan_already_exists': 'Clan already exists',
    'server_not_found': 'Server not found',
    'sub_already_exists': 'Sub already exists',
    'sub_not_found': 'Sub not found',
}

PROJECTS_MONGODB = {
    'check': {'_id': 1},
    'user.discord_id': {'discord_id': 1},
}


def build_id_account(main_account, server):
    return f'{server}_{main_account}'


def build_id_role_stats(clan, role):
    return f'{role}_{clan}'


def build_id_boss_timer(clan, boss):
    return f'{boss}_{clan}'


def get_bosses_default():
    return db.boss.find({})


def get_bosses_type():
    return db.boss_type.find({})


def get_user(main_account, server, project=None):
    return db.user.find_one({'_id': build_id_account(main_account, server)}, project)


def get_user_details(main_account, server, project=None):
    return db.user_details.find_one({'_id': build_id_account(main_account, server)}, project)


def get_user_sensitive(main_account, server, project=None):
    return db.user_sensitive.find_one({'_id': build_id_account(main_account, server)}, project)


def get_user_stats(main_account, server, project=None):
    return db.user_stats.find_one({'_id': build_id_account(main_account, server)}, project)


def get_role_stats(clan, role, project=None):
    return db.role_stats.find_one({'_id': build_id_role_stats(clan, role)}, project)


def get_clan(clan, project=None):
    return db.clan.find_one({'_id': clan}, project)


def create_clan(clan, server, name, count_users=0):
    if get_clan(clan, PROJECTS_MONGODB['check']):
        return {'success': False, 'msg': ERROR_MESSAGES['clan_already_exists']}
    if not get_server(server, PROJECTS_MONGODB['check']):
        return {'success': False, 'msg': ERROR_MESSAGES['server_not_found']}

    db.clan.insert_one({'_id': clan, 'server': server,
                        'name': name, 'count_users': count_users})
    return {'success': True, 'msg': 'Clan created'}


def delete_clan(clan):
    if not get_clan(clan, PROJECTS_MONGODB['check']):
        return {'success': False, 'msg': ERROR_MESSAGES['clan_not_found']}

    db.clan.delete_one({'_id': clan})
    db.role_stats.delete_many({'_id': {'$regex': f'_{clan}'}})
    db.boss_timer.delete_many({'_id': {'$regex': f'_{clan}'}})
    return {'success': True, 'msg': 'Clan deleted'}


def get_server(server, project=None):
    return db.server.find_one({'_id': server}, project)


def create_server(server, name, count_users=0, status='Online'):
    if get_server(server, PROJECTS_MONGODB['check']):
        return {'success': False, 'msg': ERROR_MESSAGES['server_already_exists']}

    db.server.insert_one({'_id': server, 'name': name,
                          'count_users': count_users, 'status': status})
    return {'success': True, 'msg': 'Server created'}


def delete_server(server):
    if not get_server(server, PROJECTS_MONGODB['check']):
        return {'success': False, 'msg': ERROR_MESSAGES['server_not_found']}

    db.server.delete_one({'_id': server})
    return {'success': True, 'msg': 'Server deleted'}


def check_user_references_exists(clan, server):
    if get_clan(clan, PROJECTS_MONGODB['check']) is None:
        return {'success': False, 'msg': ERROR_MESSAGES['clan_not_found']}
    if get_server(server, PROJECTS_MONGODB['check']) is None:
        return {'success': False, 'msg': ERROR_MESSAGES['server_not_found']}
    return {'success': True, 'msg': 'User references exists'}


def check_role_is_valid(role):
    return db.role.find_one({'_id': role}, PROJECTS_MONGODB['check'])


def check_boss_is_valid(boss):
    return db.boss.find_one({'_id': boss}, PROJECTS_MONGODB['check'])


def add_sub_to_boss_timer(server, clan, main_account, boss):
    id_boss_timer = build_id_boss_timer(clan, boss)
    user = get_user(main_account, server, PROJECTS_MONGODB['user.discord_id'])
    if not user:
        return {'success': False, 'msg': ERROR_MESSAGES['user_not_found']}
    if not user['discord_id']:
        return {'success': False, 'msg': ERROR_MESSAGES['user_no_discord_id']}
    if db.boss_timer.find_one({'_id': id_boss_timer, 'subs': {'$in': [user['discord_id']]}}, PROJECTS_MONGODB['check']):
        return {'success': False, 'msg': ERROR_MESSAGES['sub_already_exists']}

    db.user.update_one({'_id': build_id_account(main_account, server)}, {'$push': {'subs': boss}})
    db.boss_timer.update_one({'_id': id_boss_timer}, {'$push': {'subs': user['discord_id']}}, upsert=True)

    return {'success': True, 'msg': 'User added to boss timer subs'}


def remove_sub_from_boss_timer(server, clan, main_account, boss):
    id_boss_timer = build_id_boss_timer(clan, boss)
    user = get_user(main_account, server, PROJECTS_MONGODB['user.discord_id'])
    if not user:
        return {'success': False, 'msg': ERROR_MESSAGES['user_not_found']}
    if user['discord_id']:
        return {'success': False, 'msg': ERROR_MESSAGES['user_no_discord_id']}
    if not db.boss_timer.find_one({'_id': id_boss_timer, 'boss': {'$in': [boss]}}):
        return {'success': False, 'msg': ERROR_MESSAGES['sub_not_found']}

    db.boss_timer.update_one({'_id': id_boss_timer}, {
        '$pull': {'subs': user['discord_id']}})
    db.user.update_one({'_id': build_id_account(main_account, server)}, {
        '$pull': {'subs': boss}})

    return {'success': True, 'msg': 'User removed from boss timer subs'}


def create_user(main_account,
                pw,
                role,
                server,
                clan,
                bosses_subbed=None,
                discord_id=None,
                alts=None,
                bans=None,
                notes=None,
                change_pw=False):
    if get_user(main_account, server, PROJECTS_MONGODB['check']) is not None:
        return {'success': False, 'msg': ERROR_MESSAGES['user_already_exists']}
    user_references = check_user_references_exists(clan, server)
    if not user_references['success']:
        return user_references
    if not check_role_is_valid(role):
        return {'success': False, 'msg': ERROR_MESSAGES['role_not_found']}

    id_acc = build_id_account(main_account, server)

    db.user.insert_one({
        '_id': id_acc,
        'main_account': main_account,
        'role': role,
        'server': server,
        'clan': clan,
        'discord_id': discord_id
    })
    db.user_details.insert_one({
        '_id': id_acc,
        'alts': alts,
        'bans': bans,
        'notes': notes
    })
    db.user_sensitive.insert_one({
        '_id': id_acc,
        'hash_pw': bcrypt.hashpw(str.encode(pw), bcrypt.gensalt()).decode(),
        'change_pw': change_pw
    })
    db.user_stats.insert_one({
        '_id': id_acc,
        'last_login': 0,
        'count_login': 0,
        'count_bosses_reset': 0
    })
    db.role_stats.update_one({'_id': build_id_role_stats(clan, role), 'role': role},
                             {'$inc': {'count_users': 1},
                              '$push': {'users': {'_id': id_acc,
                                                  'date_assigned': int(
                                                      time.time())}}},
                             upsert=True)
    db.server.update_one({'_id': server}, {'$inc': {'count_users': 1}})
    db.clan.update_one({'_id': clan}, {'$inc': {'count_users': 1}})
    if bosses_subbed:
        for boss in bosses_subbed:
            if not check_boss_is_valid(boss):
                return {'success': False, 'msg': ERROR_MESSAGES['boss_not_found']}
            response = add_sub_to_boss_timer(server, clan, main_account, boss)
            if not response['success']:
                return response
            db.user.update_one({'_id': id_acc}, {
                '$push': {'bosses_subbed': boss}})

    return {'success': True, 'msg': 'User account created'}


def delete_user(main_account, server):
    user = get_user(main_account, server, {'clan': 1, 'role': 1})
    if not user:
        return {'success': False, 'msg': ERROR_MESSAGES['user_not_found']}

    id_acc = build_id_account(main_account, server)

    db.user.delete_one({'_id': id_acc})
    db.user_details.delete_one({'_id': id_acc})
    db.user_sensitive.delete_one({'_id': id_acc})
    db.user_stats.delete_one({'_id': id_acc})
    db.role_stats.update_one({'_id': build_id_role_stats(user['clan'], user['role'])},
                             {'$inc': {'count_users': -1}, '$pull': {'users': {'_id': id_acc}}})
    db.server.update_one({'_id': server}, {'$inc': {'count_users': -1}})
    db.clan.update_one({'_id': user['clan']}, {'$inc': {'count_users': -1}})
    if 'bosses_subbed' in user:
        for boss in user['bosses_subbed']:
            response = remove_sub_from_boss_timer(
                server, user['clan'], main_account, boss)
            if not response['success']:
                return response

    return {'success': True, 'msg': 'User account deleted'}
