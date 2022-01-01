import bcrypt
import pymongo
from dotenv import dotenv_values

config = dotenv_values('.env')

ERROR_MESSAGES = {
    'boss_not_found': 'Boss not found',
    'boss_already_exists': 'Boss already exists',
    'boss_type_already_exists': 'Boss type already exists',
    'boss_type_not_found': 'Boss type not found',
    'user_not_found': 'User not found',
    'user_already_exists': 'User already exists',
    'user_no_discord_id': 'User has no discord id',
    'role_not_found': 'Role not found',
    'role_already_exists': 'Role already exists',
    'clan_not_found': 'Clan not found',
    'clan_already_exists': 'Clan already exists',
    'server_not_found': 'Server not found',
    'server_already_exists': 'Server already exists',
    'sub_already_exists': 'Sub already exists',
    'sub_not_found': 'Sub not found',
}

PROJECTS_MONGODB = {
    'check': {'_id': 1},
    'user.discord_id': {'discord_id': 1},
}


def get_db(url_db, server_name=None, *vargs, **kwargs):
    return pymongo.MongoClient(url_db, *vargs, **kwargs)[server_name] if server_name else pymongo.MongoClient(url_db,
                                                                                                              *vargs,
                                                                                                              **kwargs)


db = None


def get_bosses():
    return db.boss.find({})


def check_boss_is_valid(boss):
    return db.boss.find_one({'boss': boss}, PROJECTS_MONGODB['check'])


def create_boss(boss, _type, reset, alias=None):
    if check_boss_is_valid(boss):
        return {'success': False, 'msg': ERROR_MESSAGES['boss_already_exists']}
    if not check_boss_type_is_valid(_type):
        return {'success': False, 'msg': ERROR_MESSAGES['boss_type_not_found']}
    db.boss.insert_one({'boss': boss, 'type': _type, 'reset': reset, 'alias': alias})
    return {'success': True, 'msg': 'Boss created'}


def get_bosses_type():
    return db.boss_type.find({})


def check_boss_type_is_valid(_type):
    return db.boss_type.find_one({'type': _type}, PROJECTS_MONGODB['check'])


def create_boss_type(_type):
    if check_boss_type_is_valid(_type):
        return {'success': False, 'msg': ERROR_MESSAGES['boss_type_already_exists']}
    db.boss_type.insert_one({'type': _type})
    return {'success': True, 'msg': 'Boss type created'}


def get_bosses_timer(boss, clan, server, project=None):
    return db.boss_timer.find_one({'boss': boss, 'server': server, 'clan': clan}, project)


def get_user(server, main_account, project=None):
    return db.user.find_one({'server': server, 'main_account': main_account}, project)


def create_user(main_account,
                pw,
                role,
                clazz,
                level,
                server,
                clan,
                subs=None,
                discord_id=None,
                alts=None,
                bans=None,
                notes=None,
                change_pw=False):
    if get_user(server, main_account, PROJECTS_MONGODB['check']) is not None:
        return {'success': False, 'msg': ERROR_MESSAGES['user_already_exists']}
    user_references = check_user_references_exists(clan, server)
    if not user_references['success']:
        return user_references
    if not check_role_is_valid(role):
        return {'success': False, 'msg': ERROR_MESSAGES['role_not_found']}

    db.user.insert_one({
        'main_account': main_account,
        'role': role,
        'server': server,
        'clan': clan,
        'class': clazz,
        'level': level,
        'discord_id': discord_id,
        'alts': alts,
        'bans': bans,
        'notes': notes,
        'hash_pw': bcrypt.hashpw(str.encode(pw), bcrypt.gensalt()).decode(),
        'change_pw': change_pw,
        'last_login': 0,
        'count_login': 0,
        'count_bosses_reset': 0
    })

    db.role_stats.update_one({'role': role, 'server': server, 'clan': clan}, {'$inc': {'count_users': 1}}, upsert=True)
    db.server.update_one({'server': server}, {'$inc': {'count_users': 1}})
    db.clan.update_one({'server': server, 'clan': clan}, {'$inc': {'count_users': 1}})
    if subs:
        for boss in subs:
            if not check_boss_is_valid(boss):
                return {'success': False, 'msg': ERROR_MESSAGES['boss_not_found']}
            response = add_sub_to_boss_timer(server, clan, main_account, boss)
            if not response['success']:
                return response

    return {'success': True, 'msg': 'User account created'}


def delete_user(main_account, server):
    user = get_user(server, main_account)
    if not user:
        return {'success': False, 'msg': ERROR_MESSAGES['user_not_found']}
    db.role_stats.update_one({'role': user['role'], 'server': server, 'clan': user['clan']},
                             {'$inc': {'count_users': -1}})
    db.server.update_one({'server': server}, {'$inc': {'count_users': -1}})
    db.clan.update_one({'server': server, 'clan': user['clan']}, {'$inc': {'count_users': -1}})
    if 'subs' in user:
        for boss in user['subs']:
            response = remove_sub_from_boss_timer(
                server, user['clan'], main_account, boss)
            if not response['success']:
                return response
    db.user.delete_one({'server': server, 'main_account': main_account})

    return {'success': True, 'msg': 'User account deleted'}


def get_user_details(server, main_account):
    return db.user.find_one({'server': server, 'main_account': main_account},
                            {'_id': 0, 'alts': 1, 'bans': 1, 'notes': 1})


def get_user_sensitive(server, main_account):
    return db.user_sensitive.find_one({'server': server, 'main_account': main_account},
                                      {'_id': 0, 'hash_pw': 1, 'change_pw': 1})


def get_user_stats(server, main_account, project=None):
    return db.user_stats.find_one({'server': server, 'main_account': main_account},
                                  {'_id': 0, 'last_login': 1, 'count_login': 1, 'count_bosses_reset': 1})


def get_role_stats(role, clan, server, project=None):
    return db.role_stats.find_one({'role': role, 'server': server, 'clan': clan}, project)


def get_roles():
    return db.role.find({})


def check_role_is_valid(role):
    return db.role.find_one({'role': role}, PROJECTS_MONGODB['check'])


def create_role(role):
    if check_role_is_valid(role):
        return {'success': False, 'msg': ERROR_MESSAGES['role_already_exists']}
    db.role.insert_one({'role': role})
    return {'success': True, 'msg': 'Role created'}


def get_clan(clan, server, project=None):
    return db.clan.find_one({'server': server, 'clan': clan}, project)


def create_clan(clan, server, count_users=0):
    if get_clan(clan, server, PROJECTS_MONGODB['check']):
        return {'success': False, 'msg': ERROR_MESSAGES['clan_already_exists']}
    if not get_server(server, PROJECTS_MONGODB['check']):
        return {'success': False, 'msg': ERROR_MESSAGES['server_not_found']}

    db.clan.insert_one({'clan': clan, 'server': server, 'count_users': count_users})
    return {'success': True, 'msg': 'Clan created'}


def delete_clan(clan, server):
    if not get_clan(clan, server, PROJECTS_MONGODB['check']):
        return {'success': False, 'msg': ERROR_MESSAGES['clan_not_found']}

    db.clan.delete_one({'server': server, 'clan': clan})
    db.role_stats.delete_many({'server': server, 'clan': clan})
    db.boss_timer.delete_many({'server': server, 'clan': clan})
    return {'success': True, 'msg': 'Clan deleted'}


def get_server(server, project=None):
    return db.server.find_one({'server': server}, project)


def create_server(server, count_users=0, status='Online'):
    if get_server(server, PROJECTS_MONGODB['check']):
        return {'success': False, 'msg': ERROR_MESSAGES['server_already_exists']}

    db.server.insert_one({'server': server, 'count_users': count_users, 'status': status})
    return {'success': True, 'msg': 'Server created'}


def delete_server(server):
    if not get_server(server, PROJECTS_MONGODB['check']):
        return {'success': False, 'msg': ERROR_MESSAGES['server_not_found']}

    db.server.delete_one({'server': server})
    return {'success': True, 'msg': 'Server deleted'}


def check_user_references_exists(clan, server):
    if get_clan(clan, server, PROJECTS_MONGODB['check']) is None:
        return {'success': False, 'msg': ERROR_MESSAGES['clan_not_found']}
    if get_server(server, PROJECTS_MONGODB['check']) is None:
        return {'success': False, 'msg': ERROR_MESSAGES['server_not_found']}
    return {'success': True, 'msg': 'User references exists'}


def add_sub_to_boss_timer(server, clan, main_account, boss):
    user = get_user(server, main_account, PROJECTS_MONGODB['user.discord_id'])
    if not user:
        return {'success': False, 'msg': ERROR_MESSAGES['user_not_found']}
    if not user['discord_id']:
        return {'success': False, 'msg': ERROR_MESSAGES['user_no_discord_id']}
    if db.boss_timer.find_one({'server': server, 'boss': boss, 'clan': clan, 'subs': {'$in': [user['discord_id']]}},
                              PROJECTS_MONGODB['check']):
        return {'success': False, 'msg': ERROR_MESSAGES['sub_already_exists']}

    db.user.update_one({'server': server, 'main_account': main_account}, {'$push': {'subs': boss}})
    db.boss_timer.update_one({'server': server, 'boss': boss, 'clan': clan}, {'$push': {'subs': user['discord_id']}},
                             upsert=True)

    return {'success': True, 'msg': 'User added to boss timer subs'}


def remove_sub_from_boss_timer(server, clan, main_account, boss):
    user = get_user(server, main_account, PROJECTS_MONGODB['user.discord_id'])
    if not user:
        return {'success': False, 'msg': ERROR_MESSAGES['user_not_found']}
    if not user['discord_id']:
        return {'success': False, 'msg': ERROR_MESSAGES['user_no_discord_id']}
    if not db.boss_timer.find_one(
            {'server': server, 'boss': boss, 'clan': clan, 'subs': {'$in': [user['discord_id']]}}):
        return {'success': False, 'msg': ERROR_MESSAGES['sub_not_found']}

    db.user.update_one({'server': server, 'main_account': main_account}, {
        '$pull': {'subs': boss}})
    db.boss_timer.update_one({'server': server, 'boss': boss, 'clan': clan}, {
        '$pull': {'subs': user['discord_id']}})

    return {'success': True, 'msg': 'User removed from boss timer subs'}


if __name__ == '__main__':
    db = get_db(config['URL_MONGODB'], config['DB_NAME'], wTimeoutMS=5000, w=1)
